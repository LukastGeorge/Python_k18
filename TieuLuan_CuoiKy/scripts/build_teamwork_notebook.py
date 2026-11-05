"""Build the group 8 notebook. Run execute_teamwork_notebook.py to verify it."""
from pathlib import Path
from textwrap import dedent

import nbformat as nbf


PROJECT = Path(__file__).resolve().parents[1] / "real_estate_ai"
OUTPUT = PROJECT.parent / "notebooks" / "TeamWork_PP_Nhom8.ipynb"
cells = []


def md(source):
    cells.append(nbf.v4.new_markdown_cell(dedent(source).strip()))


def code(source):
    cells.append(nbf.v4.new_code_cell(dedent(source).strip()))


md(r"""
# TEAMWORK PP — NHÓM 8
## Dự đoán giá nhà từ diện tích, số phòng ngủ và vị trí

**Dự án:** `TieuLuan_CuoiKy/real_estate_ai`  
**Sinh viên:** Nguyễn Duy Trường — **MSSV:** 24150180 — **STT:** 6  
**Nhóm:** 8 (thực hiện cá nhân)  
**Ngành:** Công nghệ thông tin — **Chuyên ngành:** Kỹ thuật phần mềm

Notebook thực hiện ba phần: **lựa chọn dataset → tiền xử lý và trực quan hóa → lựa chọn, huấn luyện và đánh giá mô hình**.

Ứng dụng demo nhận bốn đầu vào `dien_tich`, `so_phong_ngu`, `latitude`, `longitude`.
Hai tin giả lập của ứng dụng không đủ để huấn luyện hay đánh giá ML. Vì vậy, bài này dùng
giao dịch công khai King County, ánh xạ về đúng bốn đầu vào trên, với **nhãn giá bán thực bằng USD**.
Notebook chạy độc lập với PostgreSQL và không ghi đè mô hình VND của ứng dụng.
""")

md(r"""
### Cách chạy

1. Mở file này trong VS Code với tiện ích Jupyter hoặc trong JupyterLab.
2. Khi chạy trong dự án, chọn kernel Python của `real_estate_ai/.venv`.
3. Nếu thiếu thư viện, mở terminal tại `TieuLuan_CuoiKy/real_estate_ai` và chạy:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements/notebook.txt
   ```

4. Chọn **Restart Kernel and Run All** để tái tạo toàn bộ kết quả.

CSV đi kèm nằm tại `real_estate_ai/data/raw/kc_house_data.csv`, nên máy hiện tại chạy được offline.
Nếu chỉ mang notebook sang máy khác, cell tải dữ liệu sẽ lấy CSV từ Kaggle; khi đó cần Internet.
Các thư viện cần thiết: `numpy pandas matplotlib seaborn scikit-learn xgboost ipykernel`.
Các bảng và hình đã lưu trong notebook có thể xem mà không cần chạy lại.
""")

code(r"""
from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, is_zipfile
from urllib.request import Request, urlopen
from hashlib import sha256
from importlib.metadata import version

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LogNorm
from matplotlib.ticker import FuncFormatter
from IPython.display import display, Markdown
from sklearn.base import clone
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

SEED = 42
np.random.seed(SEED)
pd.set_option("display.max_columns", 25)
pd.set_option("display.float_format", lambda number: f"{number:,.3f}")
sns.set_theme(style="whitegrid", font="DejaVu Sans", context="notebook")
plt.rcParams.update({"figure.dpi": 110, "axes.titlesize": 13, "axes.labelsize": 11})

packages = ["numpy", "pandas", "matplotlib", "seaborn", "scikit-learn", "xgboost"]
display(pd.DataFrame({"Thư viện": packages, "Phiên bản": [version(p) for p in packages]}))
""")

md(r"""
## 1. Lựa chọn và tìm hiểu dataset

### 1.1. Nguồn và phạm vi

**House Sales in King County, USA**, được tài khoản **harlfoxem** công bố trên
[Kaggle](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction).
[GeoDa Center](https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/)
cung cấp mô tả các biến. Bản CSV dùng trong bài được tải ngày **31/10/2026**.
Thời điểm tải không phải thời điểm giao dịch; khoảng ngày bán được kiểm tra trực tiếp bên dưới.

Một dòng là **một lần bán nhà**, không nhất thiết là một căn nhà riêng biệt.
Đây là dataset giá giao dịch để học có giám sát, khác với giá do công thức demo tạo ra.
File nguồn được kiểm tra SHA-256 để kết quả có thể tái lập trên cùng bản dữ liệu.
""")

code(r"""
DATASET_URL = "https://www.kaggle.com/datasets/harlfoxem/housesalesprediction"
DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/harlfoxem/housesalesprediction"
EXPECTED_SHA256 = "d0875baa0251b21d4bdc9d2ae940a4fe0bb6009824f23dd0e2a5b2bf04557b7e"

# Hỗ trợ mở notebook từ thư mục gốc workspace, TieuLuan_CuoiKy hoặc real_estate_ai.
cwd = Path.cwd().resolve()
candidates = [cwd, cwd / "TieuLuan_CuoiKy", cwd.parent]
demo_root = next((p for p in candidates if (p / "real_estate_ai").is_dir()), cwd)
data_dir = demo_root / "real_estate_ai" / "data" / "raw"
data_path = data_dir / "kc_house_data.csv"

if data_path.exists():
    csv_bytes = data_path.read_bytes()
else:
    request = Request(DOWNLOAD_URL, headers={"User-Agent": "TeamWork-PP-Nhom8/1.0"})
    try:
        with urlopen(request, timeout=90) as response:
            payload = response.read()
    except Exception as exc:
        raise RuntimeError(
            "Không tải được dữ liệu. Tải kc_house_data.csv từ trang Kaggle ở trên "
            f"và đặt tại {data_path}, rồi chạy lại."
        ) from exc
    if not is_zipfile(BytesIO(payload)):
        raise ValueError("Kaggle không trả về ZIP; hãy tải CSV thủ công từ trang dataset.")
    with ZipFile(BytesIO(payload)) as archive:
        csv_bytes = archive.read("kc_house_data.csv")  # Chỉ đọc đúng file, không extractall.
    if sha256(csv_bytes).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Bản tải đã thay đổi. Cần kiểm tra nguồn trước khi cập nhật checksum.")
    data_dir.mkdir(parents=True, exist_ok=True)
    data_path.write_bytes(csv_bytes)

actual_sha256 = sha256(csv_bytes).hexdigest()
if actual_sha256 != EXPECTED_SHA256:
    raise ValueError("CSV hiện tại khác bản đã kiểm tra; không tiếp tục dùng nhầm dữ liệu.")

raw = pd.read_csv(BytesIO(csv_bytes), dtype={"id": "string", "zipcode": "string"})
expected_columns = [
    "id", "date", "price", "bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors",
    "waterfront", "view", "condition", "grade", "sqft_above", "sqft_basement",
    "yr_built", "yr_renovated", "zipcode", "lat", "long", "sqft_living15", "sqft_lot15",
]
assert raw.columns.tolist() == expected_columns
sale_dates = pd.to_datetime(raw["date"], format="%Y%m%dT%H%M%S", errors="coerce")
display(pd.DataFrame({
    "Nội dung": ["Số giao dịch", "Số thuộc tính", "Số mã nhà riêng biệt", "Ngày bán đầu", "Ngày bán cuối"],
    "Kết quả": [len(raw), raw.shape[1], raw["id"].nunique(),
                sale_dates.min().date(), sale_dates.max().date()],
}))
print("SHA-256:", actual_sha256)
display(raw.head())
""")

md(r"""
### 1.2. Mô tả toàn bộ 21 thuộc tính

| Thuộc tính | Ý nghĩa / đơn vị |
|---|---|
| `id` | Mã nhà |
| `date` | Ngày bán |
| `price` | Giá bán (USD), nhãn |
| `bedrooms` | Số phòng ngủ |
| `bathrooms` | Số phòng tắm quy đổi |
| `sqft_living` | Diện tích ở (ft²) |
| `sqft_lot` | Diện tích đất (ft²) |
| `floors` | Số tầng |
| `waterfront` | Ven nước: 1=có, 0=không |
| `view` | Điểm cảnh quan (0–4) |
| `condition` | Điểm tình trạng (1–5) |
| `grade` | Hạng chất lượng xây dựng |
| `sqft_above` | Diện tích trên mặt đất (ft²) |
| `sqft_basement` | Diện tích tầng hầm (ft²) |
| `yr_built` | Năm xây |
| `yr_renovated` | Năm sửa; 0=chưa sửa |
| `zipcode` | Mã bưu chính |
| `lat`, `long` | Vĩ độ, kinh độ (độ) |
| `sqft_living15` | Diện tích ở trung bình 15 nhà gần nhất (ft²) |
| `sqft_lot15` | Diện tích đất trung bình 15 nhà gần nhất (ft²) |

Diễn giải biến theo [GeoDa](https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/).
`lat` và `long` là hai cột riêng. Tên chứa `15` không được hiểu là nhãn giá năm 2015.
""")

md(r"""
### 1.3. Vì sao dataset phù hợp với `TieuLuan_CuoiKy`?

- Có nhãn giá bán dạng số liên tục và hơn 21 nghìn giao dịch, đủ để chia dữ liệu và so sánh mô hình.
- Có đủ bốn đầu vào của ứng dụng. `sqft_living` được đổi sang m² bằng hệ số **0,09290304**;
  trong notebook, “diện tích” được định nghĩa rõ là **diện tích ở**, không phải diện tích đất.
- Có mã nhà để kiểm soát các lần bán lặp, ngày bán để kiểm tra phạm vi thời gian,
  và các thuộc tính bổ sung để thảo luận về giới hạn của mô hình bốn đầu vào.

### 1.4. Hạn chế

- Chỉ bao phủ King County, bang Washington; không đại diện toàn nước Mỹ hay nhà ở Việt Nam.
- Giao dịch cũ năm 2014–2015, không thể dùng kết quả này như định giá thị trường năm 2026.
- Giá tính bằng **USD**. Đổi đơn vị tiền không giải quyết khác biệt thị trường; không đưa mô hình này vào luồng VND của demo.
- Bốn đầu vào bỏ qua tình trạng, chất lượng, tuổi nhà và nhiều yếu tố khác. Các căn cùng diện tích,
  số phòng và vị trí vẫn có thể có giá khác nhau.
- Không có hồ sơ đối soát từng giao dịch trong CSV; các giá trị bất thường cần xác minh từ nguồn.
  Bài này không tự sửa 33 phòng thành 3 phòng hoặc tự gán giá thiếu.
- Kết quả phụ thuộc cách chia dữ liệu. Chia theo mã nhà ngăn một căn xuất hiện ở nhiều tập,
  nhưng chưa kiểm tra khả năng dự báo thời gian tương lai hoặc tổng quát sang khu vực mới.
""")

md(r"""
## 2. Tiền xử lý bằng NumPy, Pandas và trực quan hóa

### 2.1. Kích thước, kiểu dữ liệu và giá trị thiếu

Kiểm tra tất cả các cột trước khi chọn đặc trưng. Mã nhà và mã bưu chính được giữ dưới dạng chuỗi
vì đây là mã định danh, không phải đại lượng có ý nghĩa cộng/trừ.
Không quy ước mọi giá trị 0 là thiếu: 0 phòng ngủ có thể là một cách ghi nhận hợp lệ;
0 ở trường năm cải tạo có nghĩa riêng.
""")

code(r"""
print(f"Kích thước dữ liệu gốc: {raw.shape[0]:,} dòng × {raw.shape[1]} cột")
quality = pd.DataFrame({
    "Kiểu dữ liệu": raw.dtypes.astype(str),
    "Số ô thiếu": raw.isna().sum(),
    "Tỷ lệ thiếu (%)": raw.isna().mean().mul(100),
    "Số giá trị riêng biệt": raw.nunique(),
})
display(quality)
missing_columns = quality.index[quality["Số ô thiếu"] > 0].tolist()
print("Thuộc tính bị thiếu:", missing_columns if missing_columns else "Không có trong bản CSV này")
numeric_raw = raw.select_dtypes(include="number")
print("Số giá trị số vô hạn:", int(np.isinf(numeric_raw.to_numpy(dtype=float)).sum()))
print("Ngày bán không phân tích được:", int(sale_dates.isna().sum()))
display(raw[["price", "sqft_living", "bedrooms", "lat", "long"]].describe())
""")

md(r"""
### 2.2. Kiểm tra trùng lặp

Phân biệt ba trường hợp: trùng toàn bộ bản ghi, trùng cặp mã nhà/ngày bán, và chỉ trùng mã nhà.
Một căn bán vào nhiều ngày là nhiều quan sát; vì vậy không xóa hàng loạt theo `id`.
Chỉ bản ghi giống hoàn toàn mới bị loại tự động. Nếu xuất hiện cùng mã/ngày nhưng nội dung khác,
notebook dừng để kiểm tra thay vì chọn tùy ý một giá bán.
""")

code(r"""
duplicate_audit = pd.Series({
    "Dòng trùng hoàn toàn (ngoài lần đầu)": int(raw.duplicated().sum()),
    "Dòng lặp mã nhà (ngoài lần đầu)": int(raw.duplicated("id").sum()),
    "Dòng lặp mã + ngày bán (ngoài lần đầu)": int(raw.duplicated(["id", "date"]).sum()),
    "Số mã nhà xuất hiện nhiều lần": int(raw.loc[raw.duplicated("id", keep=False), "id"].nunique()),
})
display(duplicate_audit.to_frame("Số lượng"))
deduplicated = raw.drop_duplicates().copy()
if deduplicated.duplicated(["id", "date"]).any():
    raise ValueError("Có nhiều bản ghi khác nhau cho cùng mã nhà và ngày bán; cần kiểm tra nguồn.")
repeat_examples = raw.loc[raw.duplicated("id", keep=False), ["id", "date", "price"]]
display(repeat_examples.sort_values(["id", "date"]).head(8))
""")

md(r"""
### 2.3. Chuẩn hóa đầu vào và kiểm tra miền giá trị

| Cột nguồn | Cột đầu vào của demo | Cách xử lý |
|---|---|---|
| `sqft_living` | `dien_tich` | Nhân 0,09290304 để đổi ft² sang m² |
| `bedrooms` | `so_phong_ngu` | Giữ số phòng ngủ |
| `lat` | `latitude` | Giữ vĩ độ |
| `long` | `longitude` | Giữ kinh độ |
| `price` | Nhãn `price` | Giữ USD, không đưa vào X |

Giới hạn **10–1.000 m²**, **0–30 phòng ngủ nguyên**, tọa độ hợp lệ được lấy theo
`real_estate_ai/backend/validation.py` để phù hợp miền đầu vào hiện tại của demo.
Loại các dòng ngoài miền này là thu hẹp phạm vi nghiên cứu, **không khẳng định chúng là tin giả**.
Không loại nhà đắt chỉ vì giá cao và không cắt ngoại lệ dựa trên phân vị của tập Test.
Giá thiếu/không dương không thể làm nhãn huấn luyện; không nội suy nhãn từ dự đoán.
""")

code(r"""
FEATURES = ["dien_tich", "so_phong_ngu", "latitude", "longitude"]
SQFT_TO_M2 = 0.09290304
working = pd.DataFrame(index=deduplicated.index)
working["id"] = deduplicated["id"]
working["date"] = pd.to_datetime(deduplicated["date"], format="%Y%m%dT%H%M%S", errors="coerce")
working["price"] = pd.to_numeric(deduplicated["price"], errors="coerce")
working["dien_tich"] = pd.to_numeric(deduplicated["sqft_living"], errors="coerce") * SQFT_TO_M2
working["so_phong_ngu"] = pd.to_numeric(deduplicated["bedrooms"], errors="coerce")
working["latitude"] = pd.to_numeric(deduplicated["lat"], errors="coerce")
working["longitude"] = pd.to_numeric(deduplicated["long"], errors="coerce")
working[FEATURES + ["price"]] = working[FEATURES + ["price"]].replace([np.inf, -np.inf], np.nan)

invalid = pd.DataFrame({
    "Thiếu mã hoặc ngày": working["id"].isna() | working["date"].isna(),
    "Giá thiếu/không dương": working["price"].isna() | working["price"].le(0),
    "Diện tích thiếu/ngoài 10–1000 m²": ~working["dien_tich"].between(10, 1000),
    "Phòng ngủ thiếu/ngoài miền nguyên 0–30": (
        ~working["so_phong_ngu"].between(0, 30) | working["so_phong_ngu"].mod(1).ne(0)
    ),
    "Tọa độ thiếu/không hợp lệ": (
        ~working["latitude"].between(-90, 90) | ~working["longitude"].between(-180, 180)
    ),
})
display(invalid.sum().rename("Số dòng vi phạm (có thể giao nhau)").to_frame())
removed_mask = invalid.any(axis=1)
display(working.loc[removed_mask, ["id", "dien_tich", "so_phong_ngu", "price"]])
clean = working.loc[~removed_mask].reset_index(drop=True)

assert clean[FEATURES + ["price"]].notna().all().all()
assert np.isfinite(clean[FEATURES + ["price"]].to_numpy(dtype=float)).all()
assert len(clean) + int(removed_mask.sum()) == len(deduplicated)
print(f"Gốc: {len(raw):,}; sau bỏ trùng hoàn toàn: {len(deduplicated):,}; "
      f"ngoài miền: {removed_mask.sum():,}; còn dùng: {len(clean):,} giao dịch.")
display(clean.head())
""")

md(r"""
### 2.4. Những thuộc tính không đưa vào mô hình và lý do

Không xóa khỏi file gốc; chỉ lựa chọn cột khi tạo ma trận `X`.

| Thuộc tính | Quyết định và lý do |
|---|---|
| `price` | Là nhãn `y`; đưa vào `X` sẽ rò rỉ đáp án. |
| `id` | Chỉ dùng chia nhóm; trị số của mã không diễn tả giá trị căn nhà. |
| `date` | Dùng kiểm tra thời gian; demo chưa nhận ngày giao dịch. Không dùng để khẳng định dự báo tương lai. |
| `sqft_living`, `bedrooms`, `lat`, `long` | Đã đổi đơn vị/đổi tên thành bốn đặc trưng; không giữ thêm bản sao trong `X`. |
| `sqft_above`, `sqft_basement` | Là các thành phần diện tích; không có đầu vào tương ứng trong demo. |
| `bathrooms`, `floors`, `sqft_lot` | Có thể hữu ích, nhưng nằm ngoài bốn trường hiện tại. |
| `waterfront`, `view`, `condition`, `grade` | Có thể giải thích chênh lệch giá; chưa được demo thu thập. |
| `yr_built`, `yr_renovated` | Có thể thể hiện tuổi/tình trạng nhà; chưa có trên đầu vào. |
| `zipcode` | Chưa dùng thêm mã vùng khi đang nghiên cứu mô hình bốn đầu vào có tọa độ. |
| `sqft_living15`, `sqft_lot15` | Cần dữ liệu nhà lân cận, demo chưa cung cấp. |

Các thuộc tính bổ sung không bị kết luận là vô ích. Việc bỏ chúng giữ bài toán phù hợp ứng dụng
nhưng có thể làm giảm chất lượng dự đoán; mở rộng đầu vào là một hướng phát triển.
""")

md(r"""
### 2.5. Tách dữ liệu trước khi khám phá sâu

Giữ riêng **20% số mã nhà cho Test**, dùng 80% còn lại làm tập phát triển.
Trong tập phát triển, tiếp tục chia **80% Fit / 20% Validation** theo mã nhà.
Tỷ lệ cuối cùng xấp xỉ **64% / 16% / 20%**, có thể chênh nhẹ theo số dòng vì một mã có nhiều giao dịch.
Seed cố định giúp tái lập. [GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html)
áp dụng tỷ lệ theo **nhóm**, không cam kết chính xác tỷ lệ hàng.

Mọi lần bán của cùng `id` chỉ thuộc một tập. Các biểu đồ khám phá dưới đây chỉ dùng **Fit**.
Validation dùng chọn mô hình; Test được giữ đến bước đánh giá cuối.
""")

code(r"""
outer_split = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
development_idx, test_idx = next(outer_split.split(clean[FEATURES], clean["price"], groups=clean["id"]))
development = clean.iloc[development_idx].copy()
test = clean.iloc[test_idx].copy()

inner_split = GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=7)
fit_idx, validation_idx = next(inner_split.split(
    development[FEATURES], development["price"], groups=development["id"]
))
fit = development.iloc[fit_idx].copy()
validation = development.iloc[validation_idx].copy()

split_frames = {"Fit": fit, "Validation": validation, "Test": test}
for left, right in [(fit, validation), (fit, test), (validation, test)]:
    assert set(left["id"]).isdisjoint(set(right["id"]))
    assert set(left.index).isdisjoint(set(right.index))
assert sum(map(len, split_frames.values())) == len(clean)
split_summary = pd.DataFrame([
    {"Tập": name, "Số giao dịch": len(frame), "Số mã nhà": frame["id"].nunique(),
     "Tỷ lệ dòng (%)": len(frame) / len(clean) * 100}
    for name, frame in split_frames.items()
]).set_index("Tập")
display(split_summary)
print("Kiểm tra đạt: không có mã nhà hoặc dòng dữ liệu chung giữa các tập.")
""")

md(r"""
### 2.6. Biểu đồ 1 — Phân bố giá bán

**Câu hỏi:** Giá có phân bố cân đối hay bị kéo dài bởi một số căn rất đắt?
Hai trục dưới thể hiện cùng dữ liệu: giá gốc và `log1p(giá)`.
Biểu đồ giúp cân nhắc biến đổi nhãn trước khi hồi quy, đồng thời giải thích vì sao cần xem cả MAE và RMSE.
""")

code(r"""
fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
sns.histplot(fit["price"] / 1_000_000, bins=60, ax=axes[0], color="#2563eb")
axes[0].axvline(fit["price"].median() / 1_000_000, color="#ef4444", linestyle="--", label="Trung vị")
axes[0].set(title="Giá bán trên tập Fit", xlabel="Giá (triệu USD)", ylabel="Số giao dịch")
axes[0].legend()
sns.histplot(np.log1p(fit["price"]), bins=50, ax=axes[1], color="#0f766e")
axes[1].set(title="Giá sau biến đổi log1p", xlabel="ln(1 + giá USD)", ylabel="Số giao dịch")
plt.show()
display(Markdown(
    f"**Nhận xét từ Fit:** Giá trung bình **{fit['price'].mean():,.0f} USD**, "
    f"trung vị **{fit['price'].median():,.0f} USD**, độ lệch skew **{fit['price'].skew():.2f}**. "
    "Giá có đuôi phải dài; biến đổi log làm giảm chênh lệch thang đo giữa nhà phổ thông và nhà đắt. "
    "Khi đánh giá, dự đoán phải được đổi trở lại USD."
))
""")

md(r"""
### 2.7. Biểu đồ 2 — Diện tích và giá bán

**Câu hỏi:** Diện tích lớn hơn có đi cùng giá cao hơn không, và bốn đầu vào có thể giải thích hết giá không?
Lấy mẫu ngẫu nhiên tối đa 3.000 dòng Fit để tránh các điểm che nhau; thống kê tương quan vẫn tính trên toàn Fit.
""")

code(r"""
plot_sample = fit.sample(n=min(3000, len(fit)), random_state=SEED)
fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
points = ax.scatter(plot_sample["dien_tich"], plot_sample["price"] / 1_000_000,
                    c=plot_sample["so_phong_ngu"], cmap="viridis", s=20, alpha=0.55)
fig.colorbar(points, ax=ax, label="Số phòng ngủ")
ax.set(title="Diện tích ở và giá bán — mẫu từ Fit", xlabel="Diện tích ở (m²)", ylabel="Giá bán (triệu USD)")
plt.show()
correlation = fit[["dien_tich", "price"]].corr().iloc[0, 1]
display(Markdown(
    f"**Nhận xét:** Tương quan Pearson giữa diện tích và giá trên Fit là **{correlation:.3f}**. "
    "Các điểm có cùng khoảng diện tích vẫn phân tán theo giá; diện tích không đủ để xác định giá một mình. "
    "Đây là quan hệ quan sát, không phải bằng chứng nhân quả."
))
""")

md(r"""
### 2.8. Biểu đồ 3 — Giá và vị trí

**Câu hỏi:** Các vị trí trong cùng một quận có cùng mặt bằng giá không?
Biểu đồ tọa độ dùng màu theo thang log của giá, không phải bản đồ hành chính.
Mẫu điểm lấy từ Fit giống biểu đồ 2. Màu chỉ biểu diễn giá bán thực, không phải độ chính xác mô hình.
""")

code(r"""
fig, ax = plt.subplots(figsize=(9, 6), layout="constrained")
points = ax.scatter(plot_sample["longitude"], plot_sample["latitude"], c=plot_sample["price"],
                    cmap="viridis", norm=LogNorm(vmin=fit["price"].min(), vmax=fit["price"].max()),
                    s=16, alpha=0.7)
colorbar = fig.colorbar(points, ax=ax, label="Giá bán (USD, thang log)")
colorbar.ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.set(title="Phân bố giá theo tọa độ — mẫu từ Fit", xlabel="Kinh độ (độ)", ylabel="Vĩ độ (độ)")
plt.show()
display(Markdown(
    "**Nhận xét:** Giá khác nhau giữa các vùng tọa độ; vị trí là tín hiệu cần giữ trong đầu vào. "
    "Quan hệ giá–tọa độ có thể thay đổi theo khu vực, là lý do thử mô hình cây bên cạnh hồi quy tuyến tính. "
    "Hình này chưa chứng minh khả năng dự đoán ở một thành phố chưa từng xuất hiện trong dữ liệu."
))
""")

md(r"""
## 3. Lựa chọn mô hình AI/ML và đánh giá

### 3.1. Loại bài toán

Đây là **học có giám sát — hồi quy**. Ma trận `X` có bốn cột số; `y` là giá bán bằng USD.
Mỗi mẫu có nhãn giá thực. Mục tiêu là ước lượng giá một căn nhà chưa xuất hiện trong dữ liệu huấn luyện,
trong phạm vi địa lý và thời kỳ tương tự dataset.

### 3.2. Hai thuật toán và mô hình đối chứng

| Mô hình | Lý do lựa chọn và ưu điểm | Hạn chế |
|---|---|---|
| **Ridge** (hồi quy tuyến tính có phạt L2) | Nhanh, ít tham số, hệ số dễ khảo sát; làm mốc tuyến tính có điều chuẩn. Chuẩn hóa đầu vào vì diện tích và tọa độ khác thang đo. | Quan hệ tuyến tính trên thang nhãn đã biến đổi; khó mô tả ranh giới khu vực và tương tác phức tạp. |
| **XGBoost Regressor** | Học các cây nối tiếp để sửa sai; biểu diễn quan hệ phi tuyến và tương tác diện tích–phòng–vị trí. Cùng họ thuật toán với `retrain_model.py` của demo. | Phức tạp hơn, có nguy cơ học quá khớp và khó giải thích từng dự đoán; không đáng tin khi ngoại suy sang thị trường khác. |
| **Median baseline** | Luôn trả trung vị giá của tập học; giúp biết việc học đặc trưng có cải thiện so với dự đoán một hằng số không. | Không phân biệt các căn nhà; chỉ là đối chứng, không phải thuật toán chính được đề xuất. |

[Tài liệu Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html) ·
[Tài liệu XGBoost](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

**Cách huấn luyện:** Ridge và XGBoost học `log1p(price)` để giảm ảnh hưởng thang giá lệch phải;
`TransformedTargetRegressor` tự đổi kết quả về USD bằng `expm1`.
Log là biến đổi cố định, không ước lượng từ Test. Tối ưu lỗi trên log không đồng nghĩa tối ưu RMSE USD,
nên lựa chọn mô hình vẫn dùng metric trên giá gốc.

Các tham số được đặt trước: Ridge `alpha=1`; XGBoost 300 cây, độ sâu 5, learning rate 0,05,
subsample 0,9. Đây là cấu hình thực nghiệm vừa phải, không khẳng định tối ưu.
Không dùng Test để chọn số cây, độ sâu hay chọn mô hình.
""")

md(r"""
### 3.3. Train / Validation / Test và chống rò rỉ

Phép chia theo mã nhà đã thực hiện ở mục 2.5:

1. Huấn luyện từng ứng viên trên **Fit**, đánh giá trên **Validation**.
2. Chọn ứng viên có **RMSE Validation thấp nhất**, khóa lựa chọn.
3. Huấn luyện lại ứng viên đó trên toàn bộ **Train = Fit + Validation** (khoảng 80% dữ liệu).
4. Đánh giá một lần trên **Test** giữ riêng (khoảng 20%), cùng baseline học trên Train.

Imputer và scaler nằm trong Pipeline: ở mỗi lần `.fit()`, chúng chỉ học từ tập được phép huấn luyện.
CSV hiện tại không có ô thiếu; sau kiểm tra miền cũng không còn giá trị thiếu. Imputer trung vị là bước dự phòng,
không thay thế nhãn và không có nghĩa bài này đã phát hiện ô thiếu. Scaler chỉ cần cho Ridge;
XGBoost không cần chuẩn hóa thang đo.

Chia ngẫu nhiên theo nhà chưa bảo đảm độc lập theo khu phố/thời gian. Nếu mục tiêu chuyển thành dự đoán
giá tương lai hoặc vùng mới, cần tách theo thời gian/vùng và đánh giá lại.
""")

md(r"""
### 3.4. Metric đánh giá

Gọi $y_i$ là giá thật, $\hat y_i$ là giá dự đoán, $n$ là số mẫu đánh giá:

- **MAE** $=\frac{1}{n}\sum |y_i-\hat y_i|$: sai lệch tuyệt đối trung bình, đơn vị USD, dễ diễn giải.
- **RMSE** $=\sqrt{\frac{1}{n}\sum(y_i-\hat y_i)^2}$: phạt mạnh sai số lớn; dùng làm tiêu chí chọn mô hình
  vì sai giá rất lớn ở một số căn cũng quan trọng.
- **R²** $=1-\frac{\sum(y_i-\hat y_i)^2}{\sum(y_i-\bar y)^2}$: so với dự đoán bằng trung bình của tập đánh giá.
  Càng gần 1 càng tốt; có thể âm và **không phải tỷ lệ phần trăm dự đoán đúng**.

MAE và RMSE càng thấp càng tốt. Tất cả được tính sau khi đưa dự đoán về **USD**, không báo lỗi log như lỗi tiền.
Baseline dùng trung vị để có đối chứng đơn giản, còn công thức R² vẫn dùng trung bình theo định nghĩa.
""")

code(r"""
X_fit, y_fit = fit[FEATURES], fit["price"]
X_validation, y_validation = validation[FEATURES], validation["price"]
X_train, y_train = development[FEATURES], development["price"]
X_test, y_test = test[FEATURES], test["price"]

ridge_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
    ("regressor", Ridge(alpha=1.0)),
])
xgb_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("regressor", XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.9, colsample_bytree=1.0, reg_lambda=1.0,
        objective="reg:squarederror", tree_method="hist", random_state=SEED, n_jobs=2,
    )),
])
templates = {
    "Median baseline": DummyRegressor(strategy="median"),
    "Ridge (log target)": TransformedTargetRegressor(
        regressor=ridge_pipeline, func=np.log1p, inverse_func=np.expm1
    ),
    "XGBoost (log target)": TransformedTargetRegressor(
        regressor=xgb_pipeline, func=np.log1p, inverse_func=np.expm1
    ),
}

def evaluate(y_true, predicted):
    predicted = np.asarray(predicted, dtype=float)
    assert predicted.shape == np.asarray(y_true).shape
    assert np.isfinite(predicted).all()
    return {
        "MAE (USD)": mean_absolute_error(y_true, predicted),
        "RMSE (USD)": np.sqrt(mean_squared_error(y_true, predicted)),
        "R²": r2_score(y_true, predicted),
    }

validation_rows = []
validation_models = {}
for name, template in templates.items():
    model = clone(template)
    model.fit(X_fit, y_fit)
    validation_models[name] = model
    validation_rows.append({"Mô hình": name, **evaluate(y_validation, model.predict(X_validation))})
validation_results = pd.DataFrame(validation_rows).set_index("Mô hình").sort_values("RMSE (USD)")
selected_name = validation_results.index[0]
display(validation_results)
print("Lựa chọn đã khóa bằng Validation:", selected_name)
""")

code(r"""
fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
values = validation_results["RMSE (USD)"] / 1000
bars = ax.barh(values.index, values.to_numpy(), color=["#0f766e", "#2563eb", "#94a3b8"])
ax.invert_yaxis()
ax.bar_label(bars, fmt="%.1f", padding=5)
ax.set_xlim(0, values.max() * 1.18)
ax.set(title="So sánh mô hình trên Validation — thấp hơn tốt hơn", xlabel="RMSE (nghìn USD)", ylabel="")
plt.show()
display(Markdown(
    f"**Lựa chọn:** {selected_name}, RMSE Validation **{validation_results.loc[selected_name, 'RMSE (USD)']:,.0f} USD**. "
    "Lựa chọn này được quyết định trước khi xem điểm Test; không thay mô hình dựa trên bảng Test tiếp theo."
))
""")

md(r"""
### 3.5. Đánh giá cuối trên Test

Huấn luyện lại lựa chọn đã khóa trên cả Fit và Validation. Test chỉ cung cấp điểm đánh giá cuối;
không quay lại điều chỉnh mô hình theo những sai số nhìn thấy ở bước này.
""")

code(r"""
final_model = clone(templates[selected_name]).fit(X_train, y_train)
test_predictions = final_model.predict(X_test)
baseline_model = DummyRegressor(strategy="median").fit(X_train, y_train)
baseline_predictions = baseline_model.predict(X_test)
test_results = pd.DataFrame([
    {"Mô hình": selected_name, **evaluate(y_test, test_predictions)},
    {"Mô hình": "Median baseline", **evaluate(y_test, baseline_predictions)},
]).set_index("Mô hình")
display(test_results)
print(f"Train cuối: {len(X_train):,} giao dịch; Test: {len(X_test):,} giao dịch.")
""")

code(r"""
errors = np.asarray(y_test) - test_predictions
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
axes[0].scatter(np.asarray(y_test) / 1_000_000, test_predictions / 1_000_000, s=13, alpha=0.35, color="#2563eb")
upper = max(float(np.max(y_test)), float(np.max(test_predictions))) / 1_000_000
axes[0].plot([0, upper], [0, upper], "--", color="#ef4444", label="Dự đoán = giá thật")
axes[0].set(title="Giá thật và giá dự đoán — Test", xlabel="Giá thật (triệu USD)", ylabel="Dự đoán (triệu USD)")
axes[0].legend()
axes[1].scatter(test_predictions / 1_000_000, errors / 1000, s=13, alpha=0.35, color="#0f766e")
axes[1].axhline(0, linestyle="--", color="#ef4444")
axes[1].set(title="Phần dư — Test", xlabel="Dự đoán (triệu USD)", ylabel="Giá thật − dự đoán (nghìn USD)")
plt.show()
display(Markdown(
    "**Đọc biểu đồ:** Điểm gần đường chéo có dự đoán sát thực tế. Phần dư dương nghĩa là dự đoán thấp hơn giá thật; "
    "phần dư âm nghĩa là dự đoán cao hơn. Các sai số lớn còn lại nhắc rằng bốn đầu vào chưa mô tả hết một căn nhà. "
    "Biểu đồ Test này phục vụ báo cáo, không được dùng để chọn lại mô hình trong cùng thực nghiệm."
))
""")

md(r"""
### 3.6. Minh họa dự đoán theo bốn trường của demo

Chọn cố định năm dòng đầu của Test để đối chiếu, không chọn riêng các trường hợp đoán tốt.
Các giá trị dưới đây đều bằng USD và thuộc phạm vi King County trong dataset.
Đây là mô hình thực nghiệm trong bộ nhớ của notebook; không xuất thành `house_model.pkl` của luồng VND.
""")

code(r"""
example = X_test.head(5).copy()
example["Giá thật (USD)"] = y_test.head(5).to_numpy()
example["Dự đoán (USD)"] = final_model.predict(example[FEATURES])
example["Sai lệch tuyệt đối (USD)"] = (
    example["Giá thật (USD)"] - example["Dự đoán (USD)"]
).abs()
display(example)
""")

md(r"""
## 4. Kết luận và hướng phát triển

Bảng dưới và đoạn kết luận được tạo từ kết quả thực thi, không điền sẵn điểm đánh giá.
""")

code(r"""
score = test_results.loc[selected_name]
baseline_score = test_results.loc["Median baseline"]
rmse_change = (1 - score["RMSE (USD)"] / baseline_score["RMSE (USD)"]) * 100
change_text = (f"giảm {rmse_change:.1f}%" if rmse_change >= 0 else f"tăng {-rmse_change:.1f}%")
display(Markdown(
    f"- **Dữ liệu:** {len(raw):,} giao dịch, {raw.shape[1]} thuộc tính gốc; "
    f"còn **{len(clean):,} giao dịch** trong miền đầu vào đã chọn.\n"
    f"- **Chất lượng dữ liệu:** {int(raw.isna().sum().sum())} ô thiếu, "
    f"{int(raw.duplicated().sum())} dòng trùng hoàn toàn; "
    f"{int(raw.duplicated('id').sum())} dòng lặp mã nhà được xử lý bằng chia nhóm.\n"
    f"- **Mô hình được chọn bằng Validation:** {selected_name}.\n"
    f"- **Test:** MAE **{score['MAE (USD)']:,.0f} USD**, RMSE **{score['RMSE (USD)']:,.0f} USD**, "
    f"R² **{score['R²']:.3f}**. RMSE {change_text} so với baseline trung vị.\n"
    "- **Giới hạn:** Đây là điểm trên một lần chia theo mã nhà, chưa có khoảng tin cậy hay kiểm thử thị trường khác. "
    "Không diễn giải R² thành tỷ lệ dự đoán đúng và không coi đây là giá nhà hiện tại ở Việt Nam."
))
""")

md(r"""
**Hướng phát triển:** Bổ sung chất lượng, tuổi nhà, phòng tắm và diện tích đất nếu mở rộng đầu vào demo;
thử GroupKFold chỉ trong tập Train để đánh giá độ ổn định; kiểm thử theo thời gian hoặc tách khu vực
khi đổi mục tiêu sử dụng; thu thập dữ liệu cùng thị trường và cùng đơn vị trước khi triển khai thực tế.
Nếu tiếp tục tối ưu từ những lỗi Test đã nhìn thấy, cần một tập kiểm thử mới cho lần kết luận tiếp theo.

### Đối chiếu yêu cầu bàn giao

| Yêu cầu | Vị trí trong notebook |
|---|---|
| Nguồn, số mẫu, đặc trưng, độ phù hợp, hạn chế | Mục 1 |
| Kích thước, giá trị thiếu, trùng lặp | Mục 2.1–2.2 |
| Làm sạch bằng NumPy/Pandas; bỏ thuộc tính có lý do | Mục 2.3–2.4 |
| Ít nhất 2 biểu đồ có ý nghĩa | 3 biểu đồ khám phá ở mục 2.6–2.8 |
| Loại bài toán; ít nhất 2 thuật toán, ưu/nhược điểm | Mục 3.1–3.2 |
| Cách chia Train/Test và kiểm soát rò rỉ | Mục 2.5 và 3.3 |
| Metric và lý do chọn | Mục 3.4 |
| Kết quả chạy và nhận xét | Mục 3.5–4 |

### Tài liệu tham khảo

1. [Kaggle — House Sales in King County, USA](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction).
2. [GeoDa Center — King County Home Sales](https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/).
3. [scikit-learn — GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html).
4. [scikit-learn — Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html).
5. [XGBoost — XGBRegressor](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

**Tên file bàn giao:** `TeamWork_PP_Nhom8.ipynb`.
""")

notebook = nbf.v4.new_notebook(
    cells=cells,
    metadata={
        "kernelspec": {"display_name": "Python 3 (TieuLuan_CuoiKy)", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.10"},
    },
)
nbf.validate(notebook)
nbf.write(notebook, OUTPUT)
print(f"Created {OUTPUT}: {len(cells)} cells")
