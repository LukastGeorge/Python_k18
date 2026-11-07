"""Add the Vietnam study while preserving the King County reference cells."""
import json
import os
from pathlib import Path
import sys
import copy
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / '.tools/kaggle-vietnam-20261107/notebook'
WORK.mkdir(parents=True,exist_ok=True)
for key,subdir in [('JUPYTER_RUNTIME_DIR','runtime'),('IPYTHONDIR','ipython'),('MPLCONFIGDIR','mpl')]:
    target=WORK/subdir;target.mkdir(exist_ok=True);os.environ[key]=str(target)
md,code=nbformat.v4.new_markdown_cell,nbformat.v4.new_code_cell
cells=[
md('''# Phân tích và dự đoán giá rao bán tại TP.HCM và Hà Nội

Nguyễn Duy Trường · MSSV 24150180 · Nhóm 8

Nguồn chính là House Price Prediction Dataset Vietnam 2024 của Nguyen Tien Nhan trên Kaggle, phiên bản 8. Price theo tỷ VND được nhân 1e9. Đây là giá rao bán, chưa phải giá giao dịch đã xác minh hoặc giá hiện tại. Nguồn không có ngày đăng từng tin hoặc cột loại nhà. Chia theo nhóm địa chỉ–diện tích; chưa kiểm thử theo thời gian. King County là thí nghiệm tham khảo riêng.'''),
code('''from pathlib import Path
import sys, json, hashlib, runpy
import numpy as np
import pandas as pd
from IPython.display import display, Image
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
project = next(p / "real_estate_ai" for p in [Path.cwd(), *Path.cwd().parents] if (p / "real_estate_ai/backend/vietnam.py").exists())
sys.path.insert(0,str(project))
from backend.vietnam import ARTIFACTS as VN_ART, FEATURES, normalize_features, load_bundle, estimate_property
provenance = json.loads((VN_ART / "clean_manifest.json").read_text(encoding="utf-8"))
assert hashlib.sha256((VN_ART / "listings_clean.csv.gz").read_bytes()).hexdigest() == provenance["sha256"]
vn_data = pd.read_csv(VN_ART / "listings_clean.csv.gz", dtype={"district_name":str,"ward_name":str})
vn_meta = load_bundle()["metadata"]
print(vn_meta["scope"])
display(pd.Series(vn_meta["audit"]).drop("optional_values_set_missing"))
print("Nguồn:",provenance["source"]["source_url"],"Revision:",provenance["source"]["revision"])'''),
md('''## 1 Sàng lọc đặc trưng và ngăn rò rỉ

Dataset có **12 cột**, gồm 11 cột dự báo ứng viên và nhãn Price. Loại Balcony direction vì thiếu trên 80% ở train; Address được tách thành ba nhóm địa bàn. Kết quả có **12 nhóm đầu vào**: 6 biến số và 6 nhóm danh mục, từ 10 cột nguồn được giữ. Không đưa giá hoặc giá/m² quan sát vào X. Các giá trị thiếu chỉ được điền bằng thống kê train. Khóa nhóm địa chỉ–diện tích không dùng giá; các dòng cùng khóa chỉ thuộc một tập.'''),
code('''vn_split = json.loads((VN_ART / "split.json").read_text(encoding="utf-8"))
for i, left in enumerate(vn_split):
    for right in list(vn_split)[i+1:]:
        assert not set(vn_split[left]) & set(vn_split[right])
display(pd.DataFrame(vn_meta["splits"]).T)
print("Đầu vào ứng viên:",FEATURES)
display(Image(filename=str(VN_ART / "charts/missingness.png")))'''),
md('''## 2 Hồi quy tuyến tính và feature importance

OLS học log(VND), lấy log diện tích và chuẩn hóa sáu biến số. Các nhóm danh mục được one-hot. Độ quan trọng của một nhóm được đo bằng **mức tăng RMSE log trên validation khi bỏ nhóm đó và fit lại OLS**. Cách này so được cả số và danh mục, không xếp hạng hệ số thô có đơn vị khác nhau. Chỉ dùng train/validation để chọn biến; không dùng test.

Chạy lại phân tích dưới đây tái lập kết quả từ dữ liệu đã kiểm tra checksum. Hệ số có điều kiện, chưa chứng minh nhân quả.'''),
code('''runpy.run_path(str(project.parent / "scripts/analyze_vietnam_linear.py"), run_name="__main__")
linear = json.loads((VN_ART / "linear_analysis.json").read_text(encoding="utf-8"))
print("12 cột gốc gồm nhãn Price →",linear["candidate_input_count"],"nhóm đầu vào sau xử lý →",linear["encoded_column_count"],"cột thiết kế OLS")
display(pd.DataFrame(linear["importance"])[["label","delta_rmse_log","delta_rmse_vnd"]])
display(Image(filename=str(VN_ART / "charts/linear_importance.png")))
display(Image(filename=str(VN_ART / "charts/linear_coefficients.png")))'''),
md('''## 3 Chọn số biến và lý do sử dụng

Chọn bộ nhỏ nhất trong các tiền tố thứ hạng có RMSE log không quá 1% so với bộ tốt nhất. Bộ lõi OLS có **6 biến**: diện tích, quận/huyện, số tầng, phường/xã, pháp lý và đường trước nhà. Diện tích mô tả quy mô; quận/phường mô tả vị trí; số tầng bổ sung kết cấu; pháp lý và chiều rộng đường bổ sung thông tin trong validation. Đây là liên hệ dự báo, chưa chứng minh nhân quả.

Số phòng tương quan với diện tích; thành phố có thông tin trùng quận/huyện. Ít thêm thông tin tuyến tính không có nghĩa là không liên quan đến giá. Ứng dụng phục vụ **XGBoost 12 đầu vào**, là mô hình phi tuyến riêng; chưa so XGBoost sáu biến với XGBoost 12 biến.'''),
code('''display(pd.DataFrame([{**row["validation"],"k":row["k"]} for row in linear["subsets"]]).set_index("k"))
print("Bộ chọn:",linear["selected"]["features"])
display(Image(filename=str(VN_ART / "charts/linear_selection.png")))'''),
md('''## 4 Biểu đồ về diện tích phòng và vị trí

Khám phá chỉ dùng train. Nguồn không có cột loại nhà nên các biểu đồ gộp bất động sản theo dataset. Trung vị giữa nhóm thể hiện quan hệ quan sát, không phải khoản tiền cộng cố định khi tăng một phòng. Đơn giá dùng diện tích khai báo, có thể là đất hoặc sàn tùy tin.'''),
code('''for chart in ["area_price","rooms","districts"]:
    display(Image(filename=str(VN_ART / "charts" / (chart+".png"))))'''),
md('''## 5 So sánh mô hình và kiểm thử cuối

XGBoost được chọn bằng validation, rồi fit train + validation. Calibration chỉ dùng hiệu chỉnh khoảng; test không chung nhóm địa chỉ–diện tích với phần fit. Không có ngày đăng để khẳng định test ở thời kỳ mới hơn. Các con số dưới đây được tính lại từ dự đoán của mô hình đã khóa.'''),
code('''display(pd.DataFrame(vn_meta["validation_comparison"]))
vn_test = pd.read_csv(VN_ART / "test_predictions.csv", dtype={"district_name":str,"ward_name":str})
vn_pred = np.exp(load_bundle()["pipeline"].predict(normalize_features(vn_test)).astype(float))
assert np.allclose(vn_pred,vn_test.predicted_vnd,rtol=1e-6)
ape = np.abs(vn_pred - vn_test.price)/vn_test.price
display(pd.Series({"MAE VND":mean_absolute_error(vn_test.price,vn_pred),
                   "RMSE VND":np.sqrt(mean_squared_error(vn_test.price,vn_pred)),
                   "R2 VND":r2_score(vn_test.price,vn_pred),"MdAPE":np.median(ape),
                   "Trong ±20%":np.mean(ape<=.2)}))
display(pd.DataFrame(vn_meta["test_breakdown"]))
display(Image(filename=str(VN_ART / "charts/test_errors.png")))'''),
md('''## 6 Giải thích một căn nhà tại TP.HCM và Hà Nội

Chọn tin test có giá nguồn ở trung vị nhóm khai báo đủ phòng, trước khi xem sai số. TreeSHAP cộng trên log(VND), sau đó lấy hàm mũ để tái tạo dự đoán. Không diễn giải các thanh thành khoản VND cộng trực tiếp. Các tin đối chiếu từ train + validation, chưa phải giao dịch đã bán.'''),
code('''vn_examples = json.loads((VN_ART / "examples.json").read_text(encoding="utf-8"))
for case in vn_examples:
    result = estimate_property(case["input"])
    reconstructed = np.exp(result["base_log_vnd"] + sum(x["log_contribution"] for x in result["explanations"]))
    assert np.isclose(result["predicted_vnd"], reconstructed, rtol=5e-5)
    print(case["label"],case["input"])
    display(pd.Series({"Giá rao nguồn VND":case["asking_vnd"],"Giá dự đoán VND":result["predicted_vnd"],
                       "VND/m² khai báo":result["price_per_m2_vnd"],"Khoảng 90%":result["interval_90_vnd"]}))
    display(pd.DataFrame(result["explanations"]))
    display(pd.DataFrame(result["comparables"]))
display(Image(filename=str(VN_ART / "charts/example_explanation.png")))'''),
md('''## 7 Giới hạn và cách chạy

Nguồn chưa có tọa độ hoặc khoảng cách trường học/cửa hàng được xác minh, nên mô hình không dùng những biến này. Chưa có mã nhà thật, ngày đăng hoặc loại nhà; giá là giá rao; diện tích khai báo có thể chưa đồng nhất. Giá nguồn giữ lại từ 1 đến 11,5 tỷ VND; không suy rộng chất lượng sang phân khúc cao hơn. Khoảng 90% gộp không bảo đảm độ phủ từng thành phố.

Chạy `TieuLuan_CuoiKy/chay_ui.cmd`, mở http://127.0.0.1:8000. King County tham khảo tại `/kingcounty`. Huấn luyện lại Việt Nam: `scripts/huan_luyen.cmd`. Dữ liệu và model nằm trong `real_estate_ai/artifacts/vietnam/`. Không dùng dự đoán của người dùng làm nhãn huấn luyện.

Nguồn: [Nguyen Tien Nhan trên Kaggle](https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024), phiên bản 8, CC0 Public Domain; [LinearRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html); [XGBoost prediction](https://xgboost.readthedocs.io/en/stable/prediction.html).''')]
nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python (Real Estate AI)','language':'python','name':'python3'}})
km=KernelManager(kernel_name='python3')
km.kernel_spec.argv=[sys.executable,'-X','utf8','-m','ipykernel_launcher','-f','{connection_file}']
NotebookClient(nb,km=km,timeout=300,allow_errors=False,resources={'metadata':{'path':str(ROOT/'notebooks')}}).execute()
assert not any(out.output_type=='error' for cell in nb.cells if cell.cell_type=='code' for out in cell.outputs)
nbformat.validate(nb)
nbformat.write(nb,ROOT / 'notebooks/PhanTich_GiaNha_VietNam.ipynb')
main_path=ROOT / 'notebooks/TeamWork_PP_Nhom8.ipynb'
main=nbformat.read(main_path,as_version=4)
if main.metadata.get('vietnam_extended_v1'):
    main.cells=main.cells[:main.metadata['vietnam_section_start']]
main.metadata['vietnam_section_start']=len(main.cells)
main.metadata['vietnam_extended_v1']=True
for cell in main.cells:
    if cell.cell_type=='markdown':
        cell.source=cell.source.replace('ứng dụng chính','ứng dụng tham khảo King County').replace('Đây là thí nghiệm dùng cho báo cáo, PowerPoint và ứng dụng chính.','Đây là thí nghiệm tham khảo King County.')
if 'Ứng dụng chính hiện dùng dữ liệu Việt Nam.' not in main.cells[0].source:
    main.cells[0].source += '\n\n**Ứng dụng chính hiện dùng dữ liệu Việt Nam. Xem mục 6 và notebook PhanTich_GiaNha_VietNam.ipynb; các mục King County phía trước là thí nghiệm tham khảo.**'
section=copy.deepcopy(nb)
section.cells[0].source='## 6 Phân tích và dự đoán giá rao bán tại Việt Nam\n\nPhần này đã chạy trong kernel mới; giữ nguyên kết quả các thí nghiệm tham khảo phía trước.\n\n'+section.cells[0].source.split('\n',1)[1]
main.cells+=section.cells
nbformat.validate(main);nbformat.write(main,main_path)
print('Executed Vietnam notebook and appended',len(section.cells),'cells to main notebook.')
