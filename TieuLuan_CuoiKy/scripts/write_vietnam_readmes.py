"""Generate documentation for the active Kaggle 2024 model and requested report."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
M=json.loads((ROOT/'real_estate_ai/artifacts/vietnam/metadata.json').read_text(encoding='utf-8'))
L=json.loads((ROOT/'real_estate_ai/artifacts/vietnam/linear_analysis.json').read_text(encoding='utf-8'))
source=M['source']['source_url']
main=f'''# Dự đoán giá nhà tại TP.HCM và Hà Nội từ Kaggle 2024

Nguồn chính: [House Price Prediction Dataset Vietnam 2024]({source}) của Nguyen Tien Nhan, **phiên bản 8**, CC0 Public Domain. CSV có **30.229 dòng và 12 cột**; giữ **22.183 tin** ở hai thành phố sau lọc. Price theo **tỷ VND**, được nhân 1e9 để huấn luyện và phục vụ bằng VND. Nguồn không có ngày đăng từng tin hoặc cột loại nhà.

## Chạy chương trình

Máy hiện tại đã có môi trường và model. Từ thư mục Python_k18:

```powershell
.\u005cTieuLuan_CuoiKy\u005cchay_ui.cmd
```

Mở **http://127.0.0.1:8000**, chọn tin mẫu hoặc nhập thông tin rồi dự đoán. Giữ terminal mở; Ctrl+C để dừng. Dùng SQLite, không cần bật PostgreSQL. Cài mới bằng `TieuLuan_CuoiKy/scripts/cai_dat.cmd` với Python 3.12.

## Báo cáo và notebook đang dùng

- **Word mới theo yêu cầu**: [44_NguyenDuyTruong_24150180.docx](docs/44_NguyenDuyTruong_24150180.docx), nguồn Kaggle 2024.
- [Notebook Việt Nam đã chạy](notebooks/PhanTich_GiaNha_VietNam.ipynb).
- [Notebook nhóm](notebooks/TeamWork_PP_Nhom8.ipynb): phần Việt Nam ở mục 6, các mục King County trước đó là tham khảo.
- [Nguồn và tái lập](docs/VIET_NAM.md).
- [PowerPoint 24 slide](docs/Thuyet_trinh_TieuLuan_CuoiKy.pptx): cùng dataset, số liệu, sáu feature OLS và ví dụ dự đoán với Word.
- Word giữ mẫu gốc Đại học Gia Định: bìa, phiếu chấm, mục lục, danh mục hình/bảng và bố cục sáu chương. Mẫu nguồn được giữ riêng trong docs/templates.

## Phương pháp và kết quả

12 cột gốc gồm Price và 11 cột dự báo ban đầu. Loại hướng ban công vì thiếu {M['audit']['training_missing_fraction']['balcony_direction']:.1%} trên train; tách Address thành 3 nhóm địa bàn. Kết quả có **12 nhóm đầu vào** gồm 6 biến số và 6 nhóm danh mục, mã hóa thành **{L['encoded_column_count']} cột OLS**.

OLS chọn **6 nhóm**: diện tích, quận/huyện, số tầng, phường/xã, pháp lý và đường trước nhà. Độ quan trọng đo bằng mức tăng RMSE log validation khi bỏ một nhóm rồi fit lại. Diện tích đứng đầu. Bộ gọn nhất nằm trong 1% sai số tốt nhất được chọn; đây là thí nghiệm tuyến tính riêng.

Ứng dụng dùng **XGBoost với 12 đầu vào**. Test **3.318 tin**: R² **0,644**, MAE **0,923 tỷ**, RMSE **1,225 tỷ**, MdAPE **12,1%**; **72,9%** tin trong sai lệch ±20%. Khoảng 90% danh nghĩa có độ phủ thực **89,6%**. Chưa so XGBoost sáu biến với XGBoost 12 biến.

Chia theo nhóm địa chỉ chuẩn hóa + diện tích làm tròn 0,1 m²: train 13.398, validation 3.271, calibration 2.196, test 3.318. Các tập không chung nhóm. Đây không phải kiểm thử theo thời gian. Giá dữ liệu giữ lại chỉ từ 1 đến 11,5 tỷ VND; không suy rộng chất lượng sang phân khúc cao hơn hoặc giá hiện tại.

## Huấn luyện và kiểm tra

Trong real_estate_ai:

```powershell
.\u005c.venv\u005cScripts\u005cpython.exe -m backend.train_vietnam --clean artifacts/vietnam/listings_clean.csv.gz --import-db
.\u005c.venv\u005cScripts\u005cpython.exe -m pytest -q
```

`scripts/huan_luyen.cmd` chạy huấn luyện từ CSV sạch có checksum. Chạy tiếp `scripts/analyze_vietnam_linear.py` và `scripts/build_vietnam_evidence.py` bằng Python trong .venv nếu cần tạo lại phân tích. Catalog Kaggle lưu trong `vietnam_2024_listings`; dữ liệu nhập trước đây và lịch sử người dùng được giữ. `vietnam_predictions` lưu dự đoán kèm phiên bản; API lịch sử chỉ trả model hiện hành. Không dùng dự đoán làm nhãn.

Kiểm thử bản Kaggle: **100 bài đạt, 1 bài PostgreSQL bỏ qua**. Kiểm tra đơn vị giá, schema, chuẩn hóa địa chỉ, nhóm không trùng, loại holdout khỏi fit, TreeSHAP, metric, API, nhập catalog và launcher khi cổng bận hoặc có phiên mã nguồn cũ.

Launcher dùng lại phiên đang chạy khi khớp mã nguồn và model. Nếu cổng 8000 có phiên khác, tự chọn cổng trống và in URL. Khi cần kiểm tra khởi động mà không mở trình duyệt: `chay_ui.cmd --no-browser --check-only`.

## Docker

Model/artifact mới nằm trong nguồn Docker hiện tại; chưa build hoặc phát hành image mới. Image GHCR đã xuất bản trước đây chưa được cập nhật bằng thao tác này. King County vẫn có tại `/kingcounty`, công cụ cũ tại `/legacy`.
'''
(ROOT/'README.md').write_text(main,encoding='utf-8')
(ROOT/'real_estate_ai/README.md').write_text('''# Ứng dụng Kaggle Vietnam Housing 2024

Backend Flask, frontend HTML/JS, mô hình XGBoost và SQLite. Hướng dẫn chạy, số liệu và file Word mới ở [README dự án](../README.md).

| Vị trí | Nội dung |
|---|---|
| backend/kaggle_vietnam.py | Xác minh nguồn, parse địa chỉ và chia nhóm |
| backend/vietnam.py | Pipeline, kiểm tra đầu vào, dự đoán và TreeSHAP |
| backend/train_vietnam.py | Huấn luyện, calibration và test |
| backend/vietnam_api.py | API info, predict, history và biểu đồ |
| backend/import_vietnam_data.py | Nhập catalog vào vietnam_2024_listings |
| frontend/templates/vietnam.html | Giao diện chính |
| artifacts/vietnam | Model, CSV sạch, split, metric, biểu đồ và ví dụ |
| data/raw/kaggle_vietnam_2024 | CSV gốc, metadata, manifest và SHA256 |

12 nhóm đầu vào: area, bedroom_count, bathroom_count, floor_count, frontage_width, road_width, province_name, district_name, ward_name, house_direction, legal_status, furniture_state. Không nhận Price hoặc giá/m² làm đầu vào. Hướng ban công được loại; nguồn không có loại nhà hoặc ngày đăng.

`GET /api/vietnam/info` trả nguồn và ví dụ. `POST /api/vietnam/predict` nhận JSON thông tin căn nhà, trả VND, khoảng 90%, giải thích và tin đối chiếu. `GET /api/vietnam/history` trả mười dự đoán của model hiện hành. Lịch sử cũ vẫn còn trong database theo model_version. Biểu đồ mô tả chỉ dùng train, biểu đồ TreeSHAP toàn cục dùng 600 tin calibration chưa fit.
''',encoding='utf-8')
(ROOT/'docs/VIET_NAM.md').write_text(f'''# Nguồn Kaggle Vietnam Housing 2024 và cách tái lập

[Dataset]({source}) · Nguyen Tien Nhan · phiên bản 8 · cập nhật 22/09/2024 · CC0 Public Domain theo Kaggle metadata. Theo tác giả, thu thập từ batdongsan.vn. CSV `vietnam_housing_dataset.csv`, 30.229 dòng, 12 cột. SHA256: `{M['source']['files'][0]['sha256']}`.

Price theo tỷ VND, nhân 1e9; Area m², Frontage/Access Road m. Không có ngày đăng, loại nhà hoặc ID thật. Chỉ lấy TP.HCM/Hà Nội; sửa Unicode, dấu chấm cuối và các alias thành phố. Giữ giá 0,5–200 tỷ, diện tích 15–1.000m², đơn giá 5–800 triệu/m². Thực tế còn 22.183 tin, giá 1–11,5 tỷ. Có 17.035 nhóm địa chỉ–diện tích; không coi mọi dòng cùng nhóm là căn trùng đã xác minh.

Nhóm theo địa chỉ chuẩn hóa và diện tích làm tròn 0,1 m², không dùng Price. GroupShuffleSplit tạo train/validation/calibration/test với xấp xỉ 60/15/10/15% nhóm, seeds 42/43/44. Nghiêm cấm gọi đây là split theo thời gian. Thống kê điền thiếu, chuẩn hóa và one-hot chỉ fit trên train. Sau chọn XGBoost, fit train+validation; calibration chỉ hiệu chỉnh khoảng; test giữ riêng.

12 cột nguồn gồm Price và 11 ứng viên; bỏ Balcony direction vì >80% thiếu ở train; Address thành ba nhóm địa bàn. 12 nhóm model (6 số + 6 danh mục). OLS log(VND), log(area), StandardScaler; drop-column refit trên validation, chọn prefix nhỏ nhất trong 1% sai số tốt nhất. Bộ chọn 6 biến: area, district_name, floor_count, ward_name, legal_status, road_width. OLS gọn là phân tích riêng; app dùng XGBoost 12 nhóm.

Trong `real_estate_ai`, `.venv/Scripts/python.exe -m backend.train_vietnam` huấn luyện từ raw CSV được xác minh. Có thể dùng `--clean artifacts/vietnam/listings_clean.csv.gz --import-db` với manifest sạch kèm SHA256. Sau đó chạy lần lượt `../scripts/analyze_vietnam_linear.py`, `../scripts/build_vietnam_evidence.py`, `../scripts/extend_vietnam_notebook.py` bằng Python trong .venv. Builder Word là `scripts/build_vietnam_report.py`, dùng runtime Documents của Codex.

Catalog mới dùng bảng vietnam_2024_listings, giữ nguyên dữ liệu cũ. Không dùng giá do app dự đoán làm nhãn. Model_version hiện tại: `{M['model_version']}`. Bản báo cáo được cập nhật là `44_NguyenDuyTruong_24150180.docx`; PPT 24 slide cùng dùng nguồn Kaggle và artifact này. Word được dựng từ docs/templates/mau_bao_cao_goc.docx, giữ cấu trúc sáu chương; không dùng lại bộ định dạng báo cáo chung.
''',encoding='utf-8')
(ROOT/'docs/README.md').write_text('''# Tài liệu dự án

- [44_NguyenDuyTruong_24150180.docx](44_NguyenDuyTruong_24150180.docx): báo cáo mới từ dataset Kaggle Vietnam Housing 2024.
- [Phan_tich_Gia_nha_Viet_Nam.md](Phan_tich_Gia_nha_Viet_Nam.md): nội dung báo cáo dạng Markdown.
- [VIET_NAM.md](VIET_NAM.md): nguồn, checksum và cách tái lập.
- [KING_COUNTY.md](KING_COUNTY.md): thí nghiệm tham khảo riêng.
- [Thuyet_trinh_TieuLuan_CuoiKy.pptx](Thuyet_trinh_TieuLuan_CuoiKy.pptx): 24 slide cùng nguồn Kaggle và số liệu với Word.
- templates/mau_bao_cao_goc.docx chỉ dùng làm mẫu định dạng gốc; không phải bản báo cáo hiện hành.
''',encoding='utf-8')
(ROOT/'notebooks/README.md').write_text('''# Notebook phân tích

PhanTich_GiaNha_VietNam.ipynb đã chạy với Kaggle Vietnam Housing Dataset 2024 phiên bản 8, 12 cột nguồn. Kiểm tra checksum, chia nhóm, chọn biến OLS, tạo biểu đồ và tính lại metric từ mô hình khóa. TeamWork_PP_Nhom8.ipynb giữ các phần King County tham khảo và thay phần Việt Nam tại mục 6 bằng kết quả Kaggle mới.
''',encoding='utf-8')
(ROOT/'real_estate_ai/data/raw/kaggle_vietnam_2024/README.md').write_text(f'''# House Price Prediction Dataset Vietnam 2024

Nguồn: {source}

Tác giả Nguyen Tien Nhan, phiên bản 8, cập nhật 2024-09-22, CC0 Public Domain theo metadata Kaggle. Theo tác giả, dữ liệu crawl từ batdongsan.vn. `dataset-metadata.json` giữ mô tả và thông tin phiên bản; `manifest.json` lưu schema, đơn vị và checksum. CSV gốc 30.229 dòng × 12 cột, {M['source']['files'][0]['bytes']} byte; SHA256 `{M['source']['files'][0]['sha256']}`.

Price theo **tỷ VND**, không phải VND. Không có ngày đăng từng tin hoặc cột loại nhà; không tự bổ sung các thông tin này. Bản ZIP chỉ phục vụ kiểm tra tải; pipeline đọc CSV có SHA256. Nguồn TiniX đã tải trước được giữ ở thư mục khác làm tham khảo và không dùng cho model hiện hành.
''',encoding='utf-8')
(ROOT.parent/'README.md').write_text('''# Python K18

Dự án cuối kỳ hiện dùng **Kaggle Vietnam Housing Dataset 2024** để dự đoán giá rao bán tại TP.HCM và Hà Nội. Xem [hướng dẫn dự án](TieuLuan_CuoiKy/README.md).

Chạy `TieuLuan_CuoiKy/chay_ui.cmd`, mở URL in trong terminal, mặc định http://127.0.0.1:8000. Launcher xử lý phiên cũ và cổng bận. Báo cáo: [44_NguyenDuyTruong_24150180.docx](TieuLuan_CuoiKy/docs/44_NguyenDuyTruong_24150180.docx), giữ mẫu gốc Đại học Gia Định. Word, PowerPoint và notebook dùng cùng dataset Kaggle và số liệu.

Các thư mục bài lab và thí nghiệm khác được giữ trong workspace. King County là thí nghiệm tham khảo tại `/kingcounty`.
''',encoding='utf-8')
print('Wrote documentation for Kaggle 2024')
