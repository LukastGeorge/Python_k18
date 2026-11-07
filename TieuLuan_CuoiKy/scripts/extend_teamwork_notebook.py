"""Preserve the original four-feature experiment and add the integrated study."""
from pathlib import Path
import shutil
import nbformat

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / 'notebooks/TeamWork_PP_Nhom8.ipynb'


def extend():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    if nb.metadata.get('kingcounty_extended_v1'):
        return
    backup = ROOT.parent / '.tools/kingcounty-20261107/backup/TeamWork_PP_Nhom8.ipynb'
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(NOTEBOOK, backup)
    nb.cells[0].source += ('\n\n**Bản tích hợp 07/11/2026:** Các mục 1–4 giữ thí nghiệm tham chiếu bốn biến. '
        'Mục 5 mở rộng thuộc tính, chia theo thời gian, hiệu chỉnh khoảng dự đoán, giải thích TreeSHAP '
        'và kết nối ứng dụng King County hiển thị VND. Điểm hai thí nghiệm dùng tập test khác nhau nên không so sánh trực tiếp.')
    for cell in nb.cells:
        if cell.cell_type == 'markdown':
            cell.source = cell.source.replace('Notebook chạy độc lập với PostgreSQL và không ghi đè mô hình VND của ứng dụng.',
                'Thí nghiệm tham chiếu này giữ nhãn USD. Mục 5 dùng cùng dataset để huấn luyện mô hình tích hợp và quy đổi giá hiển thị sang VND.')
            cell.source = cell.source.replace('Không đưa mô hình này vào luồng VND của demo.',
                'Ứng dụng tích hợp ở mục 5 ghi rõ thị trường King County và tỷ giá quy đổi, không coi đây là mô hình nhà Việt Nam.')
    md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
    nb.cells += [
        md('''## 5 Phân tích mở rộng và ứng dụng tích hợp

Đây là thí nghiệm dùng cho báo cáo, PowerPoint và ứng dụng chính. Dữ liệu vẫn là snapshot King County đã kiểm tra SHA-256 ở mục 1. Nhãn học máy là giá USD, kết quả hiển thị VND theo snapshot tỷ giá Vietcombank có lưu nguồn và ngày.

Các đặc trưng bổ sung gồm diện tích đất, phòng tắm, số tầng, chất lượng, tình trạng, cảnh quan, ven nước, tuổi nhà, cải tạo, mã bưu chính và tháng giao dịch. Giá/m² được tính **sau dự đoán**, không đưa vào X vì dẫn xuất từ nhãn. Không dùng `sqft_living15` và `sqft_lot15` khi chưa xác nhận vintage lịch sử của hai biến này.

Train 05–10/2014, validation 11–12/2014, hiệu chỉnh khoảng 01–02/2015 và test 03–05/2015. Loại giao dịch cũ của mã nhà thuộc tập phía sau để các tập không chung căn. Chọn mô hình chỉ bằng RMSE validation. Mô hình phục vụ là chính bản train + validation đã được đánh giá, không fit lại trên calibration hoặc test.'''),
        code('''import sys, json
sys.path.insert(0, str(demo_root / "real_estate_ai"))
from backend.train_kingcounty import train as train_integrated
from backend.kingcounty import ARTIFACTS, load_bundle, estimate_property
integrated_metadata = train_integrated(import_db=False)
display(pd.DataFrame(integrated_metadata["splits"]).T)
display(pd.read_csv(ARTIFACTS / "validation_metrics.csv"))
print("Mô hình đã khóa:", integrated_metadata["selected_model"])
print("Các dòng bị loại:", integrated_metadata["audit"]["invalid_rows"])
print("Giao dịch cũ bị purge:", integrated_metadata["purged_rows"])'''),
        md('''### 5 1 Bằng chứng về diện tích phòng và môi trường

Biểu đồ khám phá dưới đây chỉ dùng tập train. Trung vị giữa các nhóm thể hiện quan hệ quan sát, không chứng minh tăng thêm một phòng sẽ làm giá tăng đúng bằng chênh lệch giữa hai cột. Chất lượng, diện tích và vị trí có thể cùng thay đổi.'''),
        code('''import importlib.util
from IPython.display import Image
_spec = importlib.util.spec_from_file_location("kc_evidence", demo_root / "scripts/build_kingcounty_evidence.py")
_evidence_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_evidence_module)
_evidence_module.main()
for _chart in ["area_price", "bedrooms_bathrooms", "quality_environment", "location", "price_per_m2"]:
    display(Image(filename=str(ARTIFACTS / "charts" / (_chart + ".png"))))'''),
        md('''### 5 2 Trường học và cửa hàng

Dataset gốc không có trường học, cửa hàng hay khoảng cách tiện ích. Mã nguồn hỗ trợ snapshot OpenStreetMap trước ngày 02/05/2014, lưu thời điểm, checksum và giấy phép. Chỉ khi snapshot xác minh được mới tạo các biến khoảng cách và đưa mô hình thêm tiện ích vào so sánh validation.

Nếu nguồn ngoài không truy cập được, kết quả ghi rõ chưa có dữ liệu. Không suy ra khoảng cách từ mã bưu chính, không lấy dữ liệu vị trí hiện tại làm bằng chứng năm 2014 và không tự điền con số. Khoảng cách đường chim bay cũng không xác định quyền tuyển sinh hay quãng đường đi bộ.'''),
        code('''print("Có snapshot tiện ích:", integrated_metadata["poi_available"])
print("Số địa điểm theo loại:", integrated_metadata["poi_counts"])
display(Image(filename=str(ARTIFACTS / "charts/amenities.png")))'''),
        md('''### 5 3 Kiểm thử theo thời gian và độ bất định

Khoảng dự đoán sử dụng phân vị hiệu chỉnh của sai số tuyệt đối trên log(1 + USD) ở tập calibration. Mức 90% là danh nghĩa; dữ liệu theo thời gian có thể thay đổi phân phối nên phải báo cáo độ phủ thực tế trên test. R² không phải tỷ lệ dự đoán đúng. Tỷ lệ nằm trong sai lệch ±10% và ±20% được tính trực tiếp từ từng giao dịch.'''),
        code('''display(pd.DataFrame([integrated_metadata["test_metrics"], integrated_metadata["baseline_test_metrics"]], index=["Mô hình được chọn", "Median baseline"]))
for _chart in ["test_errors", "calibration", "importance"]:
    display(Image(filename=str(ARTIFACTS / "charts" / (_chart + ".png"))))'''),
        md('''### 5 4 Giải thích một căn nhà trong tập test

Chọn căn có giá thật gần trung vị của test trước khi xem sai số, không lựa trường hợp dự đoán tốt. TreeSHAP phân rã chính xác dự đoán trên thang log(1 + USD). Các đóng góp cộng với mức nền để tái tạo đầu ra, không cộng trực tiếp thành các khoản VND và không được diễn giải là tác động nhân quả.

Các giao dịch đối chiếu phải đã bán trước ngày định giá và không cùng mã căn nhà đang xét. Giá/m² = giá dự đoán VND / diện tích ở m². Đây không phải một đơn giá cố định cho mọi căn.'''),
        code('''integrated_examples = json.loads((ARTIFACTS / "examples.json").read_text(encoding="utf-8"))
case = integrated_examples[0]
display(pd.Series(case["input"], name="Đầu vào"))
case_result = estimate_property(case["input"])
display(pd.Series({"Giá thật USD": case["actual_usd"], "Giá thật VND": case["actual_vnd"],
    "Dự đoán VND": case_result["predicted_vnd"], "VND mỗi m² diện tích ở": case_result["price_per_m2_vnd"],
    "Cận dưới VND": case_result["interval_vnd"][0], "Cận trên VND": case_result["interval_vnd"][1]}))
display(pd.DataFrame(case_result["comparables"]))
display(Image(filename=str(ARTIFACTS / "charts/example_explanation.png")))
print("Tỷ giá và nguồn:", integrated_metadata["exchange_rate"])
print(integrated_metadata["limitation"])'''),
        md('''### 5 5 Chạy lại và nguồn tham chiếu

Từ `real_estate_ai`: `python -m backend.train_kingcounty --import-db` với `DB_BACKEND=sqlite`. Chạy `../scripts/build_kingcounty_evidence.py` để dựng lại biểu đồ. `../chay_ui.cmd` mở giao diện chính. Dữ liệu cũ được giữ trong bảng riêng, dataset theo giao dịch ở `kingcounty_sales` và lịch sử dự đoán ở `kingcounty_predictions`.

Nguồn: [Kaggle King County](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction), [GeoDa mô tả biến](https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/), [Vietcombank](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-tien-ich/Ty-gia), [OpenStreetMap và ODbL](https://www.openstreetmap.org/copyright), [scikit-learn về cross validation](https://scikit-learn.org/stable/modules/cross_validation.html), [XGBoost về dự đoán đóng góp](https://xgboost.readthedocs.io/en/stable/prediction.html).''')]
    nb.metadata['kingcounty_extended_v1'] = True
    nbformat.write(nb, NOTEBOOK)
    print('Extended notebook:', NOTEBOOK)


if __name__ == '__main__':
    extend()
