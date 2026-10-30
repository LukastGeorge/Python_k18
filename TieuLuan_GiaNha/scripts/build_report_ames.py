"""Tạo báo cáo từ mẫu giảng viên và các kết quả đã chạy; dùng python-docx."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/template_reference.docx"
OUTPUT = ROOT / "docs/6_Nguyễn Duy Trường_24150180.docx"
meta = json.loads((ROOT / "artifacts/metadata.json").read_text(encoding="utf-8"))
scores = list(csv.DictReader((ROOT / "artifacts/metrics.csv").open(encoding="utf-8")))
best = next(row for row in scores if row["model"] == meta["selected_model"])
importance = list(csv.DictReader((ROOT / "artifacts/feature_importance.csv").open(encoding="utf-8")))
test_tree = ET.parse(ROOT / "artifacts/test_results.xml").getroot()
test_count = sum(int(s.attrib.get("tests", 0)) for s in test_tree.findall("testsuite"))
test_failures = sum(int(s.attrib.get("failures", 0)) + int(s.attrib.get("errors", 0)) for s in test_tree.findall("testsuite"))
assert test_failures == 0, "Không tạo báo cáo kết quả đạt khi còn kiểm thử lỗi"
audit = meta["audit"]

doc = Document(REFERENCE)
body = doc.element.body
original_parts = {n: b for n, b in []}
with ZipFile(REFERENCE) as z:
    original_parts = {n: z.read(n) for n in z.namelist()}


def font(run, size=13, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold, run.italic = bold, italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")


def replace(paragraph, text, size, bold=False):
    # Preserve pPr, including the cover section break and drawing-free layout.
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    font(paragraph.add_run(text), size, bold)


for p in list(doc.paragraphs):
    text = p.text
    if text == "<TÊN ĐỀ TÀI >":
        replace(p, "PHÂN TÍCH DỮ LIỆU BẤT ĐỘNG SẢN\nVÀ XÂY DỰNG ỨNG DỤNG\nDỰ ĐOÁN GIÁ NHÀ", 18, True)
    elif text.startswith("Ngành:"):
        replace(p, "Ngành: CÔNG NGHỆ THÔNG TIN", 16, True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif text.startswith("Chuyên ngành"):
        replace(p, "Chuyên ngành: KỸ THUẬT PHẦN MỀM", 16, True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif text.startswith("Sinh viên thực hiện:"):
        replace(p, "Sinh viên thực hiện: NGUYỄN DUY TRƯỜNG", 14, True)
    elif text.startswith("MSSV:"):
        replace(p, "MSSV: 24150180  |  STT: 6  |  Nhóm: 8", 14, True)
    elif text.startswith("Họ và tên sinh viên:"):
        replace(p, "Họ và tên: Nguyễn Duy Trường          MSSV: 24150180", 13)
    elif text == "(Chữ đậm, in hoa, cỡ chữ 30)":
        body.remove(p._p)

# Remove only the source's empty content slots after the grading signature.
signature = next(p for p in doc.paragraphs if p.text == "(Ký và ghi rõ họ tên)")
after = list(body).index(signature._p) + 1
for child in list(body)[after:]:
    if child.tag != qn("w:sectPr"):
        body.remove(child)

# Topic is longer than its placeholder; reclaim three empty paragraphs before it.
topic = next(p for p in doc.paragraphs if p.text.startswith("PHÂN TÍCH DỮ LIỆU"))
for _ in range(3):
    prev = topic._p.getprevious()
    if prev is not None and not prev.xpath('.//w:t|.//w:drawing|.//w:pict'):
        body.remove(prev)

for name, size, bold in [("Report Body", 13, False), ("Heading 1", 14, True), ("Heading 2", 13, True),
                         ("Figure Caption", 11, False), ("Table Caption", 11, False)]:
    style = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.3 if name == "Report Body" else 1.1
    if name == "Report Body":
        style.paragraph_format.first_line_indent = Cm(.8)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if name.startswith("Heading"):
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.keep_with_next = True
    if name.endswith("Caption"):
        style.font.italic = True
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style.paragraph_format.first_line_indent = Cm(0)

for style_name in ["TOC 1", "TOC 2", "TOC Heading"]:
    if style_name in doc.styles:
        doc.styles[style_name].font.name = "Times New Roman"
        doc.styles[style_name].font.size = Pt(12)
        doc.styles[style_name].font.color.rgb = RGBColor(0, 0, 0)

story = []
figure_counter = 0
table_counter = 0


def paragraph(text):
    p = doc.add_paragraph(text, "Report Body")
    p.paragraph_format.widow_control = True
    story.append(text)
    return p


def heading(text, level=1, new_page=False):
    p = doc.add_paragraph(text, f"Heading {level}")
    p.paragraph_format.page_break_before = new_page
    story.append("#" * (level + 1) + " " + text)
    return p


def front_heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.page_break_before = True
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(18)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run(text), 13, True)
    return p


def field(instruction):
    p = doc.add_paragraph()
    f = OxmlElement("w:fldSimple")
    f.set(qn("w:instr"), instruction)
    p._p.append(f)


def table(title, headers, rows, widths=None):
    global table_counter
    table_counter += 1
    caption = f"Bảng {table_counter}. {title}"
    p = doc.add_paragraph(caption, "Table Caption")
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    widths = widths or [15 / len(headers)] * len(headers)
    for col, width in zip(t.columns, widths):
        col.width = Cm(width)
    for i, values in enumerate([headers] + rows):
        row = t.rows[0] if i == 0 else t.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        if i == 0:
            row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Cm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.line_spacing = 1.0
            font(p.add_run(str(value)), 11, i == 0)
            prop = cell._tc.get_or_add_tcPr()
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "E8ECEF" if i == 0 else ("F7F8F9" if i % 2 == 0 else "FFFFFF"))
            prop.append(shade)
            margins = OxmlElement("w:tcMar")
            for side in ["top", "left", "bottom", "right"]:
                el = OxmlElement("w:" + side)
                el.set(qn("w:w"), "90")
                el.set(qn("w:type"), "dxa")
                margins.append(el)
            prop.append(margins)
    borders = OxmlElement("w:tblBorders")
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        el = OxmlElement("w:" + side)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D9D9D9")
        borders.append(el)
    t._tbl.tblPr.append(borders)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = Pt(2)
    story.append(caption + "\n" + " | ".join(headers) + "\n" + "\n".join(" | ".join(map(str, row)) for row in rows))


def figure(filename, title, width=14.6):
    global figure_counter
    figure_counter += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ROOT / "artifacts/figures" / filename), width=Cm(width))
    caption = f"Hình {figure_counter}. {title}"
    doc.add_paragraph(caption, "Figure Caption")
    story.append(f"![{caption}](../artifacts/figures/{filename})")


front_heading("MỤC LỤC")
field('TOC \\o "1-2" \\h \\z \\u')
front_heading("DANH MỤC HÌNH ẢNH")
field('TOC \\h \\z \\t "Figure Caption,1"')
front_heading("DANH MỤC BẢNG BIỂU")
field('TOC \\h \\z \\t "Table Caption,1"')
front_heading("DANH MỤC CÁC TỪ VIẾT TẮT")
table("Các từ viết tắt và đơn vị", ["Ký hiệu", "Ý nghĩa"], [
    ["AI / ML", "Trí tuệ nhân tạo / học máy"], ["EDA", "Phân tích khám phá dữ liệu"],
    ["CV", "Kiểm định chéo"], ["MAE", "Sai số tuyệt đối trung bình"],
    ["RMSE", "Căn bậc hai sai số bình phương trung bình"], ["R²", "Hệ số xác định"],
    ["USD", "Đô la Mỹ"], ["ft²", "Feet vuông; 1 ft² = 0,09290304 m²"],
    ["CSV", "Tệp dữ liệu phân cách bằng dấu phẩy"], ["PID", "Mã định danh bất động sản"]], [3, 12])

heading("CHƯƠNG 1 TỔNG QUAN ĐỀ TÀI", new_page=True)
heading("1.1 Bối cảnh và mục tiêu", 2)
paragraph("Giá nhà chịu tác động đồng thời của vị trí, quy mô, chất lượng và các đặc điểm công trình. Việc chỉ so sánh diện tích với giá khó thể hiện đầy đủ sự khác biệt giữa các căn nhà. Tiểu luận xây dựng một quy trình phân tích dữ liệu và ứng dụng học máy nhằm ước tính giá bán từ thông tin đầu vào, đồng thời giải thích cách đánh giá chất lượng dự đoán.")
paragraph("Sản phẩm gồm dữ liệu có nguồn gốc, chương trình tiền xử lý, các biểu đồ Matplotlib và Seaborn, các mô hình hồi quy được so sánh trên cùng cách chia dữ liệu, cùng ứng dụng Streamlit tiếng Việt. Người dùng có thể khám phá dữ liệu, nhập một căn nhà hoặc tải CSV để dự đoán nhiều căn nhà và xuất kết quả.")
heading("1.2 Phạm vi và câu hỏi nghiên cứu", 2)
paragraph("Đề tài sử dụng Ames Housing do Dean De Cock công bố, mô tả 2.930 giao dịch nhà ở Ames, Iowa, Mỹ trong giai đoạn 2006–2010 [1]. Đơn vị giá là USD và diện tích là ft². Dữ liệu được dùng để thực nghiệm hồi quy; kết quả không được diễn giải thành mức giá hiện tại tại Việt Nam.")
paragraph("Ba câu hỏi chính là: giá nhà phân bố ra sao và thay đổi như thế nào giữa các khu vực; những thuộc tính nào có liên hệ đáng chú ý với giá; mô hình nào đạt sai số kiểm định chéo thấp hơn một cách dự đoán đơn giản bằng trung vị. Việc chọn mô hình dựa trên kết quả thực nghiệm thay vì giả định thuật toán phức tạp luôn tốt hơn.")
heading("1.3 Công nghệ và sản phẩm", 2)
table("Công nghệ sử dụng", ["Thành phần", "Vai trò"], [
    ["Python, Pandas, NumPy", "Đọc dữ liệu, kiểm tra kiểu, thống kê và xử lý mảng"],
    ["Matplotlib, Seaborn", "Phân phối, scatter, boxplot, heatmap và biểu đồ sai số"],
    ["scikit-learn, joblib", "Pipeline, huấn luyện, đánh giá và lưu mô hình"],
    ["Streamlit", "Giao diện khám phá và dự đoán tiếng Việt"],
    ["pytest, AppTest", "Kiểm thử đầu vào, mô hình lưu và luồng giao diện"]], [5, 10])
paragraph("Mã nguồn được tách theo trách nhiệm: src/housing.py chứa xử lý dùng chung; scripts/train.py huấn luyện; scripts/visualize.py tạo hình; app.py phục vụ giao diện; tests/test_project.py kiểm tra hành vi. Cấu trúc này giúp cùng một quy tắc tiền xử lý được sử dụng khi huấn luyện và khi dự đoán.")

heading("CHƯƠNG 2 DỮ LIỆU VÀ TIỀN XỬ LÝ", new_page=True)
heading("2.1 Nguồn và cấu trúc dữ liệu", 2)
paragraph(f"Tệp gốc tải từ kho của Journal of Statistics Education có {audit['raw_rows']:,} dòng và {audit['raw_columns']} cột, bao gồm mã định danh, các đặc điểm bất động sản và SalePrice. Dataset được giữ nguyên ở data/raw/AmesHousing.tsv; bản CSV được xuất để thuận tiện nộp và đọc lại. Từ điển biến đi kèm giúp phân biệt một giá trị không có tiện ích với dữ liệu thật sự thiếu [1], [2].")
paragraph("Dự án chọn 15 thuộc tính đầu vào dễ diễn giải và nhập khi demo, gồm 11 biến số và 4 biến phân loại. PID dùng để kiểm tra trùng và lưu phép chia train/test, không dùng dự đoán. SalePrice là nhãn; các cột chỉ biết sau giao dịch như Sale Condition và Sale Type không được đưa vào mô hình.")
table("Các nhóm thuộc tính được chọn", ["Nhóm", "Các cột", "Ý nghĩa và đơn vị"], [
    ["Quy mô", "Lot Area, Gr Liv Area, Garage Area, Total Bsmt SF", "Diện tích đất, diện tích ở trên mặt đất, gara và tầng hầm; ft²"],
    ["Chất lượng", "Overall Qual, Overall Cond", "Thang 1–10 về chất lượng và tình trạng"],
    ["Thời gian", "Year Built, Year Remod/Add", "Năm xây dựng và năm cải tạo"],
    ["Số lượng", "Bedroom AbvGr, Full Bath, Garage Cars", "Phòng ngủ, phòng tắm đầy đủ trên mặt đất, sức chứa gara"],
    ["Phân loại", "Neighborhood, Bldg Type, House Style, Central Air", "Khu vực, loại nhà, kiểu nhà, điều hòa trung tâm"]], [2.6, 6.5, 5.9])
heading("2.2 Kiểm tra chất lượng và làm sạch", 2)
paragraph("Các tên mã dạng chuỗi được bỏ khoảng trắng hai đầu. Các cột số được chuyển kiểu bằng Pandas; giá trị không chuyển được hoặc vô hạn trở thành thiếu. Bản ghi thiếu giá, có giá không dương hoặc diện tích ở/đất không dương bị loại. Mã PID trùng được giữ bản cuối. Đây là các quy tắc hợp lệ cố định, không dùng kết quả của tập test để quyết định ngưỡng.")
table("Kết quả kiểm tra dữ liệu thực tế", ["Nội dung", "Số lượng"], [
    ["Dòng gốc", audit['raw_rows']], ["Dòng sau kiểm tra", audit['clean_rows']],
    ["Mã trùng đã loại", audit['duplicate_ids_removed']], ["Dòng không hợp lệ đã loại", audit['invalid_rows_removed']],
    ["Ô thiếu trong toàn bộ dữ liệu gốc", audit['raw_missing_cells']],
    ["Ô thiếu trong 15 thuộc tính được chọn", audit['selected_missing_cells']]], [11, 4])
paragraph("Không coi mọi NA trong khoảng 80 trường là lỗi cần điền giống nhau: chẳng hạn tiện ích không tồn tại có thể được tác giả ghi NA. Dự án không sử dụng các cột định tính thiếu nhiều đó. Với các cột đã chọn, dữ liệu thiếu số được điền trung vị và dữ liệu thiếu phân loại được điền mốt học từ train. Giá trị số 0 có nghĩa như không có gara/tầng hầm được giữ là 0.")
heading("2.3 Chuẩn hóa và xử lý giá trị cực đoan", 2)
paragraph("Mỗi cột số được cắt ngọn tại phân vị 1% và 99% để hạn chế ảnh hưởng của các giá trị cực đoan. QuantileClipper tính hai ngưỡng trong fit và chỉ áp dụng trong transform. Tiếp theo StandardScaler chuẩn hóa bằng trung bình và độ lệch chuẩn của train. Các biến phân loại được OneHotEncoder chuyển thành biến chỉ báo; cấu hình handle_unknown='ignore' bảo vệ tầng mô hình khi gặp mã chưa xuất hiện trong một fold [3].")
paragraph("Việc cắt ngọn không xóa các căn nhà đắt khỏi test và không thay đổi nhãn SalePrice. Đánh đổi là mô hình có thể khó phân biệt các căn nhà vượt ngưỡng của cùng một thuộc tính. Các ngưỡng được học riêng trong từng fold thông qua Pipeline; không chuẩn hóa hoặc điền thiếu trên toàn bộ dữ liệu trước khi chia.")
heading("2.4 Phân chia và khả năng tái lập", 2)
paragraph(f"Dữ liệu được chia ngẫu nhiên 80/20 với random_state=42: {meta['train_rows']:,} mẫu train và {meta['test_rows']:,} mẫu test. Trên train, KFold 5 phần có shuffle và cùng seed được dùng cho mọi mô hình. Các mã PID của hai phần được lưu ở artifacts/split.json để kiểm tra không giao nhau; phiên bản thư viện và SHA-256 nguồn dữ liệu được ghi trong metadata.json.")
paragraph("Phân chia này đo khả năng dự đoán cho căn nhà khác trong cùng thị trường và giai đoạn dữ liệu. Nó chưa phải kiểm định dự báo giá ở một thời điểm tương lai. Muốn khẳng định hiệu quả dự báo tương lai cần giữ các năm sau làm test và cập nhật dữ liệu mới.")

heading("CHƯƠNG 3 PHÂN TÍCH VÀ TRỰC QUAN HÓA", new_page=True)
heading("3.1 Phân phối giá và quan hệ với diện tích", 2)
paragraph("Các hình khám phá trong chương này được tạo từ tập train. Histogram mô tả phân phối giá; đường KDE hỗ trợ quan sát hình dạng tổng thể. Scatter thể hiện từng căn nhà, dùng màu cho chất lượng tổng thể để xem xét đồng thời nhiều yếu tố.")
figure("01_price_distribution.png", "Phân phối giá nhà trong tập huấn luyện")
paragraph("Phân phối tập trung ở các mức giá phổ biến và có đuôi về phía nhà giá cao. Vì vậy trung vị là mốc mô tả hữu ích, còn sai số bình phương có thể bị chi phối bởi một số căn nhà đắt. Đây là lý do báo cáo cả MAE và RMSE thay vì chỉ một chỉ số.")
figure("02_area_price.png", "Quan hệ giữa diện tích ở, chất lượng và giá bán")
paragraph("Nhìn chung, diện tích ở lớn hơn đi cùng mức giá cao hơn, nhưng các điểm không nằm trên một đường thẳng. Các căn cùng diện tích vẫn có giá khác nhau; màu chất lượng giúp nhận diện một phần sự khác biệt. Một số căn diện tích rất lớn có giá không tương xứng, cho thấy cần xem xét giá trị cực đoan và loại giao dịch thay vì tự động kết luận dữ liệu nhập sai.")
heading("3.2 So sánh khu vực và tương quan", 2)
figure("03_neighborhood.png", "Phân phối giá tại tám khu vực nhiều mẫu nhất")
paragraph("Boxplot cho thấy trung vị, độ phân tán và các điểm giá khác biệt theo khu vực. Chỉ đưa tám khu vực nhiều mẫu nhất vào hình để tránh biểu đồ quá dày; cách chọn dựa trên số lượng mẫu, không chọn các khu vực có giá cao để tô đậm kết luận. Neighborhood được giữ làm biến phân loại trong mô hình để phản ánh khác biệt vị trí.")
figure("04_correlation.png", "Ma trận tương quan giữa một số thuộc tính số")
paragraph("Heatmap giúp đọc nhanh dấu và độ lớn của quan hệ tuyến tính giữa các biến số. Diện tích ở, chất lượng, tiện ích gara và quy mô tầng hầm là các nhóm thông tin đáng chú ý. Tương quan không đo toàn bộ quan hệ phi tuyến và không chứng minh nhân quả; những thuộc tính cùng liên quan tới quy mô nhà có thể chứa thông tin chồng lặp.")

heading("CHƯƠNG 4 HUẤN LUYỆN VÀ ĐÁNH GIÁ", new_page=True)
heading("4.1 Thiết kế thực nghiệm", 2)
paragraph("Bốn phương án sử dụng cùng 15 đầu vào và cùng phép chia: baseline dự đoán trung vị, hồi quy tuyến tính, Random Forest và Gradient Boosting. Baseline kiểm tra lợi ích của việc học mối quan hệ từ thuộc tính. Linear Regression là mô hình tuyến tính có thể liên hệ với bài học trên lớp; hai mô hình cây giúp mô tả các quan hệ và tương tác phi tuyến [3].")
table("Cấu hình mô hình trong thực nghiệm", ["Mô hình", "Cấu hình chính"], [
    ["Median baseline", "DummyRegressor(strategy='median')"], ["Linear Regression", "LinearRegression; tiền xử lý chung bằng Pipeline"],
    ["Random Forest", "200 cây; min_samples_leaf=2; random_state=42"],
    ["Gradient Boosting", "250 cây; max_depth=2; learning_rate=0,05; loss='huber'; seed=42"]], [5, 10])
paragraph("Cấu hình được cố định trước phép so sánh. Dự án chưa chạy một cuộc tìm kiếm siêu tham số lớn; đây là giới hạn về phạm vi, không được trình bày thành kết quả tối ưu toàn cục. Mô hình được chọn bằng RMSE trung bình thấp nhất qua 5 fold trên train. Test dùng báo cáo cuối cùng; không thay đổi cấu hình dựa trên thứ hạng test.")
heading("4.2 Các thước đo", 2)
paragraph("MAE = (1/n) × Σ|yᵢ − ŷᵢ| là mức sai số tuyệt đối trung bình. RMSE = √[(1/n) × Σ(yᵢ − ŷᵢ)²] đặt trọng số lớn hơn cho lỗi lớn. Hai chỉ số cùng đơn vị USD và càng thấp càng tốt. R² = 1 − Σ(yᵢ − ŷᵢ)² / Σ(yᵢ − ȳ)² so sánh sai số với việc dùng trung bình của tập được đánh giá; R² có thể âm và không phải tỷ lệ dự đoán đúng.")
figure("05_model_comparison.png", "RMSE kiểm định chéo của các mô hình")
table("Kết quả kiểm định chéo và tập kiểm tra", ["Mô hình", "CV RMSE", "Test MAE", "Test RMSE", "Test R²"], [
    [r["model"], f"{float(r['cv_rmse_mean']):,.0f}", f"{float(r['test_mae']):,.0f}",
     f"{float(r['test_rmse']):,.0f}", f"{float(r['test_r2']):.4f}"] for r in scores], [4.5, 2.6, 2.6, 2.8, 2.5])
paragraph(f"Theo tiêu chí đặt trước, {meta['selected_model']} được chọn với CV RMSE {float(best['cv_rmse_mean']):,.2f} USD. Trên {meta['test_rows']} mẫu test, MAE là {float(best['test_mae']):,.2f} USD, RMSE là {float(best['test_rmse']):,.2f} USD và R² là {float(best['test_r2']):.4f}. Các giá trị lấy trực tiếp từ artifacts/metrics.csv và được kiểm thử lại từ mô hình đã lưu.")
heading("4.3 Phần dư và vai trò đặc trưng", 2)
figure("06_predictions_residuals.png", "Giá dự đoán và phần dư trên tập kiểm tra")
paragraph("Đường chéo biểu thị dự đoán trùng giá thực. Khoảng cách tới đường chéo thể hiện độ lệch; phần dư được định nghĩa là thực tế trừ dự đoán. Phần dư dương nghĩa là mô hình dự đoán thấp. Các sai số lớn ở vùng giá cao cần được trình bày như giới hạn mô hình, không loại khỏi kết quả đã báo cáo.")
figure("07_feature_importance.png", "Độ quan trọng bằng hoán vị trên tập kiểm tra")
paragraph("Permutation importance xáo trộn từng thuộc tính rồi đo mức tăng RMSE, lặp lại năm lần với seed 42. Các biến đứng đầu trong lần chạy này là " + ", ".join(row['feature'] for row in importance[:3]) + ". Biểu đồ được dùng giải thích mô hình sau khi đã chốt mô hình, không dùng để chọn lại thuộc tính trên test. Với các biến tương quan, mức quan trọng có thể được chia sẻ và không đồng nghĩa tác động nhân quả.")

heading("CHƯƠNG 5 ỨNG DỤNG VÀ KIỂM THỬ", new_page=True)
heading("5.1 Luồng sử dụng và tổ chức chương trình", 2)
paragraph("Ứng dụng Streamlit gồm bốn trang: Tổng quan, Khám phá dữ liệu, Dự đoán giá nhà và Đánh giá mô hình. Trang tổng quan trình bày phạm vi, số giao dịch, số thuộc tính và mô hình được chọn. Trang khám phá cho phép lọc khu vực và tải dữ liệu; trang đánh giá hiển thị thước đo và hình phân tích. Tất cả nhãn chính bằng tiếng Việt, giữ đơn vị gốc rõ ràng [4].")
paragraph("Luồng dự đoán là giao diện nhận dữ liệu → validate_inputs kiểm tra schema và miền → Pipeline biến đổi bằng các tham số đã học → mô hình hồi quy → kết quả USD và tệp CSV. Ứng dụng chỉ tải mô hình đã huấn luyện, không huấn luyện lại sau mỗi lần người dùng bấm dự đoán. st.cache_resource giữ mô hình trong bộ nhớ; st.cache_data dùng cho dữ liệu lịch sử.")
paragraph("Chế độ một căn nhà cung cấp 11 ô số và 4 lựa chọn phân loại. Giá trị điền sẵn lấy trung vị hoặc mốt trên train và được giải thích ngay trên giao diện. Chế độ theo lô nhận CSV tối đa 2.000 dòng, 4 MB; tệp mẫu gồm 10 dòng lấy từ train chỉ để minh họa thao tác, không dùng để công bố chất lượng tổng quát hóa.")
if (ROOT / "artifacts/figures/08_app_overview.png").exists():
    figure("08_app_overview.png", "Giao diện tổng quan của ứng dụng", 14.6)
if (ROOT / "artifacts/figures/09_app_prediction.png").exists():
    figure("09_app_prediction.png", "Giao diện nhập thông tin và kết quả dự đoán", 14.6)
heading("5.2 Kiểm tra đầu vào", 2)
paragraph("Ứng dụng từ chối thiếu cột, cột trùng, chuỗi ở ô số, số vô hạn, giá trị ngoài miền train và số lẻ ở trường đếm. Khu vực và mã loại nhà phải thuộc danh sách đã biết. Năm cải tạo không được trước năm xây dựng. Ô số thiếu trong CSV được phép giữ NaN để bộ imputer áp dụng trung vị train. Kết quả không hữu hạn hoặc không dương không được xuất như một giá hợp lệ.")
heading("5.3 Kết quả kiểm thử", 2)
paragraph(f"Bộ pytest có {test_count} trường hợp kiểm thử và tất cả đều đạt trong lần chạy dùng cho báo cáo. Ngoài kiểm tra đầu vào, bộ kiểm thử xác nhận train/test không giao nhau, ngưỡng cắt ngọn không học từ test, dự đoán từ mô hình lưu khớp tệp kết quả và các thước đo tính lại khớp bảng báo cáo. AppTest chạy các trang, dự đoán thành công và kiểm tra thông báo lỗi năm cải tạo [5].")
table("Nhóm kiểm thử và hành vi mong đợi", ["Nhóm", "Kết quả xác nhận"], [
    ["Tính toàn vẹn dữ liệu", "PID train/test rời nhau, tổng bao phủ dữ liệu sạch"],
    ["Tiền xử lý", "Transform không thay đổi ngưỡng đã học; số thiếu được điền"],
    ["Mô hình và số liệu", "Bản joblib tái tạo dự đoán, MAE, RMSE và R² đã báo cáo"],
    ["Dữ liệu sai", "Từ chối schema sai, vô hạn, ngoài miền, mã lạ, năm bất hợp lý"],
    ["Ứng dụng", "Các trang chạy; dự đoán đúng luồng; lỗi được hiển thị có giải thích"]], [4.6, 10.4])
heading("5.4 Hướng dẫn chạy và demo", 2)
paragraph("Tạo môi trường Python 3.12, cài requirements.txt rồi chạy python -m streamlit run app.py tại thư mục dự án. Mô hình và dữ liệu được đóng gói nên không cần Internet cho các chức năng demo sau khi cài thư viện. Để tái lập kết quả, chạy lần lượt python -m scripts.train, python -m scripts.visualize và python -m pytest -q. README có các lệnh PowerShell đầy đủ.")
paragraph("Kịch bản bảo vệ đi từ phạm vi dữ liệu, phân tích biểu đồ, phương pháp đánh giá đến nhập một căn nhà và dự đoán CSV. Khi trình bày cần phân biệt đơn vị ft² với m², R² với độ chính xác phân loại, và dữ liệu demo với test độc lập. Hướng dẫn chi tiết và câu hỏi ôn tập được đặt trong docs/KICH_BAN_DEMO.md.")

heading("CHƯƠNG 6 KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", new_page=True)
heading("6.1 Kết quả đạt được", 2)
paragraph(f"Tiểu luận hoàn thành quy trình từ dataset gốc đến ứng dụng dự đoán, gồm kiểm tra dữ liệu, xử lý thiếu và giá trị cực đoan, trực quan hóa, so sánh mô hình, kiểm thử và đóng gói. Mô hình được chọn theo CV là {meta['selected_model']}; kết quả test và dự đoán có thể kiểm tra lại từ mã nguồn, dữ liệu và các tệp kết quả đi kèm.")
paragraph("Về kiến thức, đề tài kết nối hồi quy tuyến tính với các mô hình phi tuyến và làm rõ vai trò của phân chia dữ liệu, Pipeline và kiểm định chéo. Về ứng dụng, giao diện cho phép người dùng khám phá các mối liên hệ và nhận dự đoán từ bộ thông số được kiểm tra.")
heading("6.2 Giới hạn", 2)
paragraph("Dữ liệu chỉ mô tả một thành phố và một giai đoạn lịch sử; còn thiếu các yếu tố thị trường hiện tại, lãi suất, pháp lý và trạng thái công trình chi tiết. Mô hình dùng 15 biến để cân bằng khả năng nhập liệu và chất lượng dự đoán, chưa khai thác mọi biến gốc. Kết quả một phép chia với seed cố định chưa phản ánh đầy đủ bất định của mọi cách lấy mẫu.")
paragraph("Ngưỡng cắt ngọn làm giảm tác động ngoại lai nhưng cũng có thể mất thông tin ở hai đuôi phân phối. Giới hạn từng trường đầu vào không bảo đảm mọi tổ hợp trường đều phổ biến trong train. Ứng dụng hiện chưa cung cấp khoảng dự đoán đã hiệu chuẩn hoặc cơ chế phát hiện mọi trường hợp ngoài phân phối.")
heading("6.3 Hướng phát triển", 2)
paragraph("Có thể bổ sung dữ liệu có nguồn rõ ràng tại Việt Nam, kiểm tra quyền sử dụng, chuẩn hóa địa chỉ và đơn vị tiền; sau đó huấn luyện lại theo thị trường địa phương. Các bước tiếp theo gồm đánh giá theo thời gian, mở rộng thuộc tính phù hợp thời điểm dự đoán, tìm kiếm siêu tham số trong train, xây dựng khoảng dự đoán và kiểm thử giao diện theo nhiều kịch bản sử dụng.")

heading("TÀI LIỆU THAM KHẢO", new_page=True)
for text in [
    '[1] D. De Cock, “Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project,” Journal of Statistics Education, vol. 19, no. 3, 2011. DOI: 10.1080/10691898.2011.11889627. https://jse.amstat.org/v19n3/decock.pdf',
    '[2] D. De Cock, “Ames Housing Data Documentation.” https://jse.amstat.org/v19n3/decock/DataDocumentation.txt. Truy cập ngày 17/10/2026.',
    '[3] scikit-learn developers, “Common pitfalls and recommended practices.” https://scikit-learn.org/stable/common_pitfalls.html. Truy cập ngày 17/10/2026.',
    '[4] Streamlit, “Streamlit documentation.” https://docs.streamlit.io/. Truy cập ngày 17/10/2026.',
    '[5] Streamlit, “st.testing.v1.AppTest.” https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest. Truy cập ngày 17/10/2026.',
    '[6] scikit-learn developers, “Ensemble methods.” https://scikit-learn.org/stable/modules/ensemble.html. Truy cập ngày 17/10/2026.',
]:
    paragraph(text)

heading("BẢNG PHÂN CÔNG NHIỆM VỤ", new_page=True)
paragraph("Nhóm 8 thực hiện theo hình thức cá nhân. Thành viên duy nhất là Nguyễn Duy Trường, MSSV 24150180, STT 6. Bảng dưới đây phân bổ các hạng mục của sản phẩm, tổng tỷ lệ đóng góp là 100%.")
table("Phân công và tỷ lệ đóng góp cá nhân", ["Hạng mục", "Người thực hiện", "Tỷ lệ"], [
    ["Khảo sát bài toán, nguồn dữ liệu và làm sạch", "Nguyễn Duy Trường", "25%"],
    ["Trực quan hóa và phân tích", "Nguyễn Duy Trường", "20%"],
    ["Mô hình, đánh giá và kiểm thử", "Nguyễn Duy Trường", "25%"],
    ["Giao diện và đóng gói ứng dụng", "Nguyễn Duy Trường", "15%"],
    ["Báo cáo và chuẩn bị demo", "Nguyễn Duy Trường", "15%"],
    ["Tổng cộng", "Nguyễn Duy Trường", "100%"]], [7.8, 4.8, 2.4])
paragraph("Các tỷ lệ thể hiện phân bổ hạng mục trong bài cá nhân, không phải số liệu đo thời gian thực hiện. Không có thành viên khác trong nhóm.")

# Numbering for the report body, while leaving the source cover unchanged.
section = doc.sections[1]
section.footer.is_linked_to_previous = False
section.footer_distance = Cm(1)
p = section.footer.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
font(p.add_run(""), 11)
f = OxmlElement("w:fldSimple")
f.set(qn("w:instr"), "PAGE")
p._p.append(f)
update = OxmlElement("w:updateFields")
update.set(qn("w:val"), "true")
doc.settings.element.append(update)
doc.core_properties.author = "Nguyễn Duy Trường"
doc.core_properties.title = "Phân tích dữ liệu bất động sản và xây dựng ứng dụng dự đoán giá nhà"
doc.core_properties.subject = "Tiểu luận Lập trình Python – Nhóm 8"
buffer = BytesIO()
doc.save(buffer)
# Preserve source package parts unless they were intentionally edited or new.
editable = {"word/document.xml", "word/styles.xml", "word/settings.xml", "word/_rels/document.xml.rels",
            "[Content_Types].xml", "docProps/core.xml", "docProps/app.xml"}
with ZipFile(buffer) as created, ZipFile(OUTPUT, "w", ZIP_DEFLATED) as final:
    for name in created.namelist():
        payload = original_parts[name] if name in original_parts and name not in editable else created.read(name)
        final.writestr(name, payload)
    for name in set(original_parts) - set(created.namelist()):
        final.writestr(name, original_parts[name])
(ROOT / "docs/noi_dung_bao_cao.md").write_text("\n\n".join(story), encoding="utf-8")
print(OUTPUT)
print(f"Tables: {table_counter}; figures: {figure_counter}; tests: {test_count}")
