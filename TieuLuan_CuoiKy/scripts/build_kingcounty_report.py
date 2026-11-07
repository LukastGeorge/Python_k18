"""Build the Vietnamese analysis report from the same artifacts used by the app."""
from pathlib import Path
import json
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'real_estate_ai/artifacts/kingcounty'
E = json.loads((ART / 'evidence.json').read_text(encoding='utf-8'))
M, X = E['metadata'], E['example']
R, RATE = X['result'], E['exchange_rate']
OUT = ROOT / 'docs/Bao_cao_Phan_tich_Gia_nha_King_County.docx'
DOC = Document()
markdown = []


def f(value, digits=0):
    return f'{value:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def pct(value):
    return f(value * 100, 1) + '%'


def billion(value):
    return f(value / 1e9, 2) + ' tỷ VND'


def p(text, style=None):
    paragraph = DOC.add_paragraph(text, style)
    paragraph.paragraph_format.space_after = Pt(7)
    markdown.append(text + '\n')
    return paragraph


def heading(title, level=1, new_page=False):
    if new_page:
        DOC.add_page_break()
    DOC.add_heading(title, level)
    markdown.append('#' * (level + 1) + ' ' + title + '\n')


def table(headers, rows, widths=None):
    t = DOC.add_table(rows=1, cols=len(headers))
    t.autofit = False
    if widths:
        for col, width in zip(t.columns, widths):
            col.width = Inches(width)
    for cell, value in zip(t.rows[0].cells, headers):
        cell.text = str(value)
        shade = OxmlElement('w:shd')
        shade.set(qn('w:fill'), 'E8EDE5')
        cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    repeat = OxmlElement('w:tblHeader')
    t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in rows:
        for cell, value in zip(t.add_row().cells, values):
            cell.text = str(value)
    for row in t.rows:
        no_split = OxmlElement('w:cantSplit')
        row._tr.get_or_add_trPr().append(no_split)
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(4)
                paragraph.paragraph_format.space_before = Pt(3)
                paragraph.paragraph_format.line_spacing = 1.0
                for run in paragraph.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(10.5)
                    run.font.color.rgb = RGBColor(0, 0, 0)
    markdown.append('| ' + ' | '.join(headers) + ' |\n|' + '|'.join(['---'] * len(headers)) + '|\n' +
                    '\n'.join('| ' + ' | '.join(str(v) for v in row) + ' |' for row in rows) + '\n')
    DOC.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(name, caption, width=6.55):
    picture = DOC.add_paragraph()
    picture.alignment = WD_ALIGN_PARAGRAPH.CENTER
    picture.paragraph_format.keep_with_next = True
    picture.paragraph_format.space_after = Pt(3)
    run = picture.add_run()
    run.add_picture(str(ART / 'charts' / (name + '.png')), width=Inches(width))
    # Alternative text stays with the image in Word.
    run._r.xpath('.//wp:docPr')[0].set('descr', caption)
    cap = DOC.add_paragraph(caption, 'Caption')
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    markdown.append(f'![{caption}](../real_estate_ai/artifacts/kingcounty/charts/{name}.png)\n')


def setup():
    section = DOC.sections[0]
    section.page_width, section.page_height = Inches(8.2677), Inches(11.6929)
    section.top_margin, section.bottom_margin = Inches(.7), Inches(.7)
    section.left_margin, section.right_margin = Inches(.85), Inches(.85)
    section.header_distance, section.footer_distance = Inches(.3), Inches(.3)
    section.different_first_page_header_footer = False
    DOC.settings.odd_and_even_pages_header_footer = False
    for name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3', 'Caption', 'Header', 'Footer']:
        style = DOC.styles[name]
        style.font.name = 'Times New Roman'
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'), 'Times New Roman')
    DOC.styles['Normal'].font.size = Pt(12)
    DOC.styles['Normal'].paragraph_format.line_spacing = 1.12
    DOC.styles['Title'].font.size = Pt(24)
    DOC.styles['Title'].font.bold = True
    for name, size in [('Heading 1', 17), ('Heading 2', 14), ('Heading 3', 12)]:
        DOC.styles[name].font.size = Pt(size)
        DOC.styles[name].paragraph_format.space_before = Pt(10)
        DOC.styles[name].paragraph_format.space_after = Pt(9)
    DOC.styles['Caption'].font.size = Pt(10)
    DOC.styles['Caption'].font.italic = True
    header = section.header.paragraphs[0]
    header.text = 'PHÂN TÍCH DỮ LIỆU GIÁ NHÀ TẠI KING COUNTY'
    header.runs[0].font.size = Pt(9)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('Nguyễn Duy Trường   Nhóm 8   •   Trang ').font.size = Pt(9)
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    DOC.core_properties.title = 'Phân tích dữ liệu và dự đoán giá nhà tại King County'
    DOC.core_properties.author = 'Nguyễn Duy Trường'
    DOC.core_properties.subject = 'Giao dịch 2014–2015 và hiển thị giá VND quy đổi'


def main():
    setup()
    p('BÁO CÁO TIỂU LUẬN CUỐI KỲ', 'Subtitle')
    title = p('Phân tích dữ liệu và dự đoán giá nhà tại King County', 'Title')
    title.paragraph_format.space_before = Pt(45)
    p('Dữ liệu giao dịch nhà tại Washington Hoa Kỳ giai đoạn 2014–2015', 'Subtitle')
    p('Hiển thị kết quả bằng VND quy đổi', 'Subtitle')
    p('Sinh viên  Nguyễn Duy Trường\nMã số sinh viên  24150180\nNhóm  8\nNgày cập nhật  07 tháng 11 năm 2026')
    heading('Tóm tắt nghiên cứu', 2)
    p(f'Nghiên cứu sử dụng {f(M["audit"]["raw_rows"])} giao dịch King County để phân tích mối liên hệ giữa giá bán với diện tích, số phòng, chất lượng, cảnh quan và vị trí. '
      f'Sau kiểm tra quy tắc, giữ lại {f(M["audit"]["accepted_rows"])} giao dịch. Mô hình {M["selected_model"]} được chọn bằng validation theo thời gian và đạt '
      f'R² {f(M["test_metrics"]["r2"], 3)} trên {f(M["splits"]["test"]["rows"])} giao dịch test ở kỳ sau. Tỷ lệ dự đoán sai lệch không quá ±20% là {pct(M["test_metrics"]["within_20pct"])}.')
    p('Báo cáo kết nối các kết quả với ứng dụng Flask, thể hiện giá trên m², khoảng dự đoán và giải thích TreeSHAP của từng căn. Giá VND là phép đổi đơn vị từ giá nhà Mỹ lịch sử. '
      'Khoảng cách đến trường học và cửa hàng chưa có nguồn lịch sử truy xuất thành công, vì vậy chưa được sử dụng làm bằng chứng hay đặc trưng của mô hình hiện tại.')

    heading('1 Mục tiêu và phạm vi dữ liệu', new_page=True)
    p('Mục tiêu là ước tính giá bán của một căn nhà trong phạm vi King County, đồng thời cung cấp căn cứ để người xem hiểu dự đoán. Một đầu ra giá đơn lẻ chưa phản ánh hết độ bất định. '
      'Vì vậy hệ thống kết hợp phân tích khám phá, đánh giá trên giao dịch mới hơn, khoảng dự đoán, đặc trưng đóng góp và các giao dịch tương đồng đã bán trước đó.')
    p('Nguồn chính là House Sales in King County, USA do tài khoản harlfoxem công bố trên Kaggle. GeoDa Center cung cấp mô tả biến và phạm vi thời gian. '
      'CSV có 21 thuộc tính, ngày bán từ 02/05/2014 đến 27/05/2015. Một dòng là một giao dịch, không nhất thiết là một căn nhà riêng biệt. [1][2]')
    table(['Nội dung', 'Giá trị'], [
        ['Đơn vị giá nguồn', 'USD cho từng giao dịch'], ['Đơn vị diện tích nguồn', 'ft²'],
        ['Chuyển đổi diện tích', '1 ft² = 0,09290304 m²'], ['Phạm vi địa lý', 'King County, Washington, Hoa Kỳ'],
        ['Mẫu gốc', f(M['audit']['raw_rows'])], ['Mẫu được chấp nhận', f(M['audit']['accepted_rows'])],
        ['Mã nhà riêng biệt sau lọc', f(M['audit']['unique_houses'])]])
    p('Các thông tin có trong dataset không bao gồm tên cửa hàng, vị trí trường học, chất lượng trường, tội phạm hay thời gian đi lại. Tọa độ và mã bưu chính cho biết vị trí, '
      'nhưng không đủ để tự khẳng định một căn nhà gần tiện ích cụ thể. Những biến này cần một nguồn bổ sung, thời điểm phù hợp và phép đo rõ ràng.')
    p('Tỷ giá chỉ phục vụ hiển thị. Nhân nhãn và dự đoán với cùng tỷ giá sẽ đổi MAE, RMSE sang VND, trong khi R² và sai số phần trăm không đổi. '
      'Nghiên cứu không sử dụng phép quy đổi tiền tệ để khẳng định mô hình phù hợp với thị trường Việt Nam hoặc giá thị trường năm 2026.')

    heading('2 Kiểm tra dữ liệu và lựa chọn đặc trưng', new_page=True)
    p(f'Không có bản ghi trùng hoàn toàn trong snapshot. Bộ quy tắc loại {M["audit"]["invalid_rows"]} dòng vi phạm miền hợp lệ như số phòng bất thường, phòng tắm không hợp lệ '
      'hoặc năm xây/cải tạo sau năm bán. Các mã bị loại được lưu trong metadata. Không tự sửa 33 phòng thành 3 phòng, không điền giá giả và không xóa mọi giao dịch lặp mã căn nhà.')
    table(['Nhóm', 'Đầu vào mô hình', 'Ý nghĩa'], [
        ['Quy mô', 'living_m2, lot_m2', 'Diện tích ở và diện tích đất tách riêng'],
        ['Số phòng', 'bedrooms, bathrooms', 'Phòng ngủ nguyên và phòng tắm quy đổi'],
        ['Kết cấu', 'floors, grade', 'Số tầng và hạng chất lượng xây dựng'],
        ['Tình trạng', 'condition', 'Điểm ghi nhận tình trạng 1–5'],
        ['Môi trường', 'waterfront, view', 'Ven nước và điểm cảnh quan 0–4'],
        ['Tuổi nhà', 'house_age', 'Năm bán trừ năm xây'],
        ['Cải tạo', 'renovated, renovation_age', 'Cờ cải tạo và số năm sau cải tạo'],
        ['Vị trí', 'latitude, longitude, zipcode', 'Tọa độ và mã bưu chính'],
        ['Thời gian', 'month_index', 'Chỉ số tháng từ năm 2014'],
        ['Nhãn', 'price', 'Giá bán USD, không thuộc X']], [1.05, 2.55, 2.95])
    p('Giá trên m² thật là giá bán chia diện tích, nên dẫn xuất trực tiếp từ nhãn. Đưa biến này vào X sẽ làm rò rỉ nhãn. Trong hệ thống, giá trên m² chỉ tính sau dự đoán. '
      'Mã nhà chỉ dùng quản lý giao dịch, chống trùng và chia tập. Hai biến diện tích của 15 nhà gần nhất chưa được dùng khi chưa xác minh vintage của chúng. [3]')
    p('Giới hạn làm sạch có thể loại cả những căn nhà đặc biệt nhưng hợp lệ. Kết quả chỉ áp dụng cho miền dữ liệu được chấp nhận. Các quy tắc hiện tại là lựa chọn nghiên cứu có thể kiểm tra, '
      'không phải bằng chứng rằng mọi bản ghi bị loại đều sai trong hồ sơ thực tế.')

    heading('3 Diện tích và giá trên mỗi mét vuông', new_page=True)
    p(f'Tương quan Pearson giữa diện tích ở và giá trong tập train là {f(E["correlations"]["living_m2"], 3)}. Diện tích ở lớn thường đi cùng giá cao hơn, nhưng các điểm có cùng diện tích '
      'vẫn phân tán đáng kể. Vì vậy mô hình cần mô tả cả chất lượng, vị trí và kết cấu thay vì dùng một đơn giá cố định.')
    figure('area_price', 'Hình 1 Diện tích ở và giá bán quy đổi của mẫu 1.500 giao dịch train', 6.3)
    figure('price_per_m2', 'Hình 2 Giá trung vị trên mỗi m² diện tích ở theo nhóm diện tích trong train', 6.3)
    p('Nguồn hai hình: tập train của snapshot King County, không sử dụng test để khám phá. VND quy đổi theo cùng snapshot tỷ giá. '
      'Giá/m² ở hình 2 là thống kê mô tả của giao dịch thực, không phải đặc trưng dùng huấn luyện và không phải bảng đơn giá thị trường Việt Nam.')

    heading('4 Số phòng chất lượng và môi trường', new_page=True)
    p('Số phòng ngủ và số phòng tắm cùng liên quan đến quy mô tài sản. Biểu đồ dùng giá trung vị và chỉ giữ nhóm có ít nhất 50 giao dịch để giảm ảnh hưởng của nhóm quá ít mẫu. '
      'Phòng tắm quy đổi giữ thông tin 0,25, 0,5 và 0,75 theo dữ liệu nguồn.')
    figure('bedrooms_bathrooms', 'Hình 3 Giá trung vị theo số phòng ngủ và phòng tắm trong train', 6.3)
    p('Grade phản ánh phân loại chất lượng xây dựng. View thể hiện đánh giá cảnh quan, còn waterfront ghi nhận ven nước. Các nhóm grade và view khác nhau có mặt bằng giá khác nhau. '
      'Những mối liên hệ này là cơ sở để kiểm tra thêm đặc trưng trên validation, chưa đủ để tính mức tiền tăng thêm cho riêng một yếu tố. [2]')
    figure('quality_environment', 'Hình 4 Chất lượng xây dựng cảnh quan và ven nước với giá trung vị trong train', 6.3)

    heading('5 Vị trí trường học và cửa hàng', new_page=True)
    p('Phân bố tọa độ cho thấy mặt bằng giá khác nhau ngay trong cùng một quận. Mô hình giữ cả tọa độ và mã bưu chính. Tuy nhiên một tọa độ không tự mô tả đầy đủ tiện ích, '
      'chất lượng khu vực hay tuyến đường tiếp cận căn nhà.')
    figure('location', 'Hình 5 Giá giao dịch theo tọa độ trong mẫu train với màu theo log10 giá USD', 6.1)
    table(['Nguồn hoặc thông tin', 'Kết quả kiểm tra'], [
        ['Trường học và cửa hàng trong CSV gốc', 'Không có thuộc tính tương ứng'],
        ['OpenStreetMap lịch sử trước kỳ bán', 'Các máy chủ Overpass hết thời gian chờ'],
        ['Dịch vụ trích xuất ohsome', 'Trả HTTP 403, không lấy được snapshot'],
        ['Tệp vị trí trường học NCES 2013–2014', 'Kết nối hết thời gian chờ'],
        ['Khoảng cách dùng trong mô hình hiện tại', 'Không sử dụng vì chưa xác minh được nguồn']], [2.9, 3.65])
    p('Mã nguồn đã có adapter đo khoảng cách đường chim bay tới điểm tiện ích trên snapshot OSM trước ngày giao dịch đầu tiên. Khi có dữ liệu, cần kiểm tra checksum, '
      'thời điểm, độ phủ và nguồn cấp phép trước khi đưa vào validation. Không xem địa điểm chưa có trên bản đồ là không tồn tại. Khoảng cách đến trường cũng không xác định quyền tuyển sinh. [7]')

    heading('6 Thiết kế thí nghiệm và chọn mô hình', new_page=True)
    p('Bốn tập đi theo thứ tự thời gian. Nếu một căn xuất hiện ở tập phía sau, các giao dịch trước đó của căn bị loại khỏi tập phía trước. Cách làm này giữ độc lập theo mã nhà '
      'và giúp phép đánh giá phản ánh giao dịch ở kỳ sau. Các biến đổi được fit trong pipeline ở tập huấn luyện tương ứng. [3]')
    table(['Tập', 'Khoảng ngày', 'Giao dịch'], [
        [name, M['splits'][key]['first_date'] + ' đến ' + M['splits'][key]['last_date'], f(M['splits'][key]['rows'])]
        for key, name in [('train', 'Train'), ('validation', 'Validation'), ('calibration', 'Hiệu chỉnh khoảng'), ('test', 'Test')]], [1.45, 3.75, 1.35])
    p(f'Có {M["purged_rows"]} giao dịch cũ bị purge để chống chung căn giữa các tập. Chọn ứng viên theo RMSE validation, sau đó fit lại cấu hình được chọn trên train + validation. '
      'Calibration chỉ dùng xây dựng khoảng dự đoán. Mô hình phục vụ giữ chính bản được đánh giá, không fit lại trên calibration hay test.')
    figure('model_comparison', 'Hình 6 RMSE validation của các ứng viên với cùng tập kiểm chứng', 6.3)
    p('XGBoost dùng 450 cây, độ sâu tối đa 5, learning rate 0,035, subsample và colsample 0,9, reg_lambda 5, seed 42. Các giá trị này cố định trước thí nghiệm. '
      'Không chạy dò tham số trên test. Mô hình mới chỉ được chấp nhận khi vượt median baseline trên MAE và RMSE validation, R² dương và dự đoán hữu hạn.')

    heading('7 Kết quả trên tập test theo thời gian', new_page=True)
    metrics = M['test_metrics']
    table(['Chỉ số', 'Kết quả'], [
        ['Số giao dịch test', f(M['splits']['test']['rows'])], ['MAE', f(metrics['mae_usd'], 2) + ' USD'],
        ['MAE quy đổi', billion(metrics['mae_usd'] * RATE)], ['RMSE', f(metrics['rmse_usd'], 2) + ' USD'],
        ['R²', f(metrics['r2'], 4)], ['Sai lệch không quá ±10%', pct(metrics['within_10pct'])],
        ['Sai lệch không quá ±20%', pct(metrics['within_20pct'])]])
    p('R² phản ánh mức độ giải thích biến thiên so với dự đoán theo giá trung bình trong phép tính chỉ số. R² không phải tỷ lệ dự đoán đúng. '
      'MAE và tỷ lệ sai lệch phần trăm giúp người xem đọc kết quả gần với từng giao dịch hơn. RMSE lớn hơn MAE cho thấy vẫn còn một số sai số lớn.')
    figure('test_errors', 'Hình 7 Giá thật dự đoán và phần dư của giao dịch test', 6.3)
    p('Thí nghiệm bốn biến cũ trong mục 1–4 của notebook có cách chia nhóm ngẫu nhiên và tập test khác. Không dùng chênh lệch R² giữa hai thí nghiệm để kết luận mức cải thiện. '
      'Bằng chứng so sánh đặc trưng nằm ở các ứng viên dùng chung validation trong hình 6.')

    heading('8 Khoảng dự đoán và sai số theo phân khúc', new_page=True)
    p('Nghiên cứu hiệu chỉnh khoảng trên sai số tuyệt đối của log(1 + USD). Với n quan sát calibration, chọn phân vị cao hơn tại mức ceil((n + 1) × 0,9) / n. '
      'Sau đó chuyển cận về USD bằng expm1 và nhân cùng tỷ giá để lấy VND. Đây là khoảng dự đoán cho giá quan sát của một căn, không phải khoảng tin cậy của giá trung bình. [4]')
    table(['Đại lượng', 'Kết quả'], [
        ['Độ phủ danh nghĩa', '90%'], ['Độ phủ thực tế trên test', pct(metrics['interval_coverage'])],
        ['Bề rộng khoảng trung vị trên test', billion(metrics['median_interval_width_usd'] * RATE)]])
    figure('calibration', 'Hình 8 Khoảng dự đoán và giá thật của 50 dòng test đầu theo thời gian', 6.1)
    table(['Nhóm theo giá thật', 'Số mẫu', 'MAE USD', 'Trong ±20%'], [
        [row['segment'], f(row['n']), f(row['mae_usd']), pct(row['within20'])] for row in E['segments']], [2.65, .75, 1.55, 1.6])
    p('Độ phủ conformal cần giả định phù hợp về phân phối của sai số. Thị trường theo thời gian có thể thay đổi, nên mức 90% không được bảo đảm cho mọi kỳ tương lai. '
      'Việc quan sát độ phủ test không loại bỏ nhu cầu hiệu chỉnh lại khi có dữ liệu mới.')

    heading('9 Giải thích mô hình bằng TreeSHAP', new_page=True)
    p('TreeSHAP cho biết mô hình phân bổ dự đoán cho các đặc trưng như thế nào. Trong pipeline này, nhãn được biến đổi log1p trước khi fit, nên các đóng góp thuộc thang '
      'log(1 + USD). Với mỗi căn, cộng các đóng góp vào mức nền rồi dùng expm1 sẽ tái tạo dự đoán USD. Kiểm thử xác nhận phép tái tạo với sai số số học nhỏ. [5]')
    figure('importance', 'Hình 9 Trung bình trị tuyệt đối TreeSHAP trên 1.000 dòng đầu validation', 6.3)
    p('Biểu đồ dùng mô hình cuối đã fit train + validation và mô tả cách mô hình sử dụng 1.000 dòng validation đầu. Đây không phải một điểm kiểm thử độc lập. '
      'Đóng góp của các cột one hot mã bưu chính được cộng về biến zipcode để người xem đọc được theo thuộc tính gốc.')
    p('Mức đóng góp lớn không chứng minh yếu tố đó gây ra mức giá. Các biến có thể tương quan và chia sẻ tín hiệu. Ví dụ diện tích, số phòng và grade có thể cùng phản ánh '
      'quy mô và mức hoàn thiện. Không diễn giải đóng góp của một biến như mức tăng tiền khi can thiệp riêng vào biến đó.')
    p('Đối với câu hỏi vì sao một căn có giá dự đoán cụ thể, hệ thống trình bày đồng thời đầu vào, đóng góp mô hình, mức nền, khoảng dự đoán và giao dịch đối chiếu. '
      'Cách trình bày này cho phép kiểm tra tính hợp lý của dự đoán mà không dựng một công thức đơn giá cố định chưa được mô hình sử dụng.')

    heading('10 Phân tích một căn nhà trong tập test', new_page=True)
    p('Căn ví dụ được chọn theo giá thật gần trung vị của test trước khi xem sai số, giúp tránh lựa riêng trường hợp mô hình đoán tốt. '
      f'Mã nhà {X["input"]["id"]}, giao dịch ngày {X["input"]["sale_date"]}, mã bưu chính {X["input"]["zipcode"]}.')
    table(['Thuộc tính', 'Giá trị'], [
        ['Diện tích ở', f(X['input']['living_m2'], 2) + ' m²'], ['Diện tích đất', f(X['input']['lot_m2'], 2) + ' m²'],
        ['Phòng ngủ và phòng tắm', f(X['input']['bedrooms']) + ' và ' + f(X['input']['bathrooms'], 2)],
        ['Grade và năm xây', str(int(X['input']['grade'])) + ' và ' + str(X['input']['year_built'])],
        ['Giá bán thực', billion(X['actual_vnd'])], ['Giá dự đoán', billion(R['predicted_vnd'])],
        ['Sai lệch tuyệt đối', billion(abs(R['predicted_vnd'] - X['actual_vnd']))],
        ['Sai lệch phần trăm', pct(abs(R['predicted_vnd'] - X['actual_vnd']) / X['actual_vnd'])]])
    figure('example_explanation', 'Hình 10 Các đóng góp lớn nhất vào dự đoán của căn ví dụ', 5.9)
    p('Các thanh thể hiện đóng góp trên thang log. Vị trí và diện tích đất tạo các đóng góp khác hướng, trong khi tuổi nhà và chất lượng bổ sung thông tin. '
      'Không thể từ biểu đồ này kết luận về trường học hay cửa hàng khi chưa có dữ liệu vị trí tiện ích.')
    total_effect = sum(item['log_contribution'] for item in R['explanations'])
    p(f'Mức nền của mô hình cho ví dụ là {f(R["base_price_usd"], 2)} USD. Tổng đóng góp của tất cả đặc trưng là {f(total_effect, 6)} trên thang log. '
      f'Tính expm1(log1p(mức nền) + tổng đóng góp) tái tạo xấp xỉ {f(R["predicted_usd"], 2)} USD, trước khi quy đổi sang VND. '
      'Hình chỉ hiển thị các đóng góp lớn nhất; phép cộng sử dụng đầy đủ mọi đặc trưng.')

    heading('11 Đơn giá quy đổi và giao dịch đối chiếu', new_page=True)
    p(f'Giá dự đoán của căn ví dụ là {f(R["predicted_usd"], 2)} USD. Với tỷ giá {f(RATE)} VND/USD, giá hiển thị bằng '
      f'{f(R["predicted_usd"], 2)} × {f(RATE)} ≈ {f(R["predicted_vnd"])} VND. Diện tích ở là {f(X["input"]["living_m2"], 2)} m², '
      f'nên đơn giá dự đoán bằng {f(R["price_per_m2_vnd"])} VND/m², xấp xỉ {f(R["price_per_m2_vnd"] / 1e6, 2)} triệu VND/m².')
    p(f'Khoảng dự đoán của căn này là {billion(R["interval_vnd"][0])} đến {billion(R["interval_vnd"][1])}. '
      'Bề rộng khoảng nhắc rằng kết quả có độ bất định đáng kể dù dự đoán điểm của ví dụ khá gần giao dịch thực.')
    table(['Ngày bán', 'Diện tích ở m²', 'Ngủ và tắm', 'Cách km', 'Triệu VND mỗi m²'], [
        [row['sale_date'], f(row['living_m2'], 1), str(row['bedrooms']) + ' / ' + str(row['bathrooms']),
         f(row['distance_km'], 2), f(row['price_per_m2_vnd'] / 1e6, 2)] for row in R['comparables']], [1.2, 1.3, 1.1, .95, 2.0])
    p('Các căn đối chiếu được lấy trong train + validation, đã bán trước ngày định giá và không trùng mã căn đang xét. Thước đo tìm kiếm kết hợp khoảng cách đường chim bay, '
      'chênh lệch diện tích và số phòng. Đây là kiểm tra mặt bằng giá, không phải thuật toán nội suy tạo ra giá XGBoost.')
    heading('Nguồn tỷ giá và cách sử dụng', 2)
    p('Snapshot lưu nguyên XML Vietcombank cùng mã SHA-256. Trường thời gian trong XML là ' + M['exchange_rate']['quoted_at'] + '. '
      'Giá bán USD được chọn làm tỷ giá quy đổi có thể tái lập trong bài. Tỷ giá giao dịch thực tế có thể khác và thay đổi theo thời điểm. [6]')
    p('Đổi VND không cập nhật lạm phát, sức mua hay chu kỳ giá bất động sản. Khi đổi tỷ giá, cần hiển thị ngày và nguồn mới. Không gắn các giá trị quy đổi này với nhãn giao dịch '
      'tại Việt Nam hoặc dùng chúng để đánh giá một mô hình nhà Việt Nam.')

    heading('12 Tích hợp ứng dụng và tổ chức mã nguồn', new_page=True)
    p('Giao diện chính sử dụng bộ đầu vào King County. Diện tích ở và diện tích đất tách riêng, có phòng tắm, grade, tình trạng, tuổi nhà, cảnh quan, ven nước và ngày định giá. '
      'Người dùng có thể chọn căn test mẫu để đối chiếu cả giá thực lẫn giá dự đoán. Tọa độ, mã bưu chính và ngày ngoài miền dữ liệu bị từ chối.')
    table(['Thành phần', 'Vai trò'], [
        ['backend/kingcounty.py', 'Làm sạch, chia tập, kiểm tra đầu vào, giải thích, định giá'],
        ['backend/train_kingcounty.py', 'Chọn mô hình, hiệu chỉnh khoảng, lưu artifact'],
        ['backend/kingcounty_api.py', 'API chính và lịch sử dự đoán'],
        ['artifacts/kingcounty', 'Model, split, metrics, ví dụ, dự đoán test và biểu đồ'],
        ['kingcounty_sales', 'Giao dịch theo mã nhà và ngày bán với nhãn USD gốc'],
        ['kingcounty_predictions', 'Đầu vào, đầu ra và phiên bản mô hình của mỗi lần dự đoán']], [2.65, 3.9])
    p('Dataset được ghi vào bảng riêng theo transaction_id để chạy lại không tạo trùng. Bảng dữ liệu cũ được giữ nguyên. Công cụ cũ còn tại /legacy, '
      'tách biệt với mô hình King County. Mỗi dự đoán chính lưu phiên bản model, tỷ giá và đầu vào, giúp truy lại căn cứ của kết quả.')
    heading('Quy trình chạy lại', 2)
    for line in ['Từ thư mục real_estate_ai, đặt DB_BACKEND=sqlite.',
                 'python -m backend.train_kingcounty --import-db',
                 'python ../scripts/build_kingcounty_evidence.py',
                 'python -m pytest -q',
                 'Chạy TieuLuan_CuoiKy/chay_ui.cmd để mở giao diện.']:
        p(line)
    p('Notebook mục 5 tái chạy thí nghiệm mở rộng và xuất các hình. Phần 1–4 giữ lại thí nghiệm tham chiếu bốn biến. Bản notebook đã chạy từ kernel mới với 20 code cell, '
      '15 đầu ra hình ảnh và không có lỗi thực thi. Các script báo cáo và slide đọc cùng evidence.json để tránh điền số liệu khác nhau.')

    heading('13 Kiểm chứng giới hạn và hướng phát triển', new_page=True)
    p('Bộ kiểm thử cục bộ có 73 bài đạt, chưa chạy bài tích hợp PostgreSQL. Các bài mới kiểm tra tách thời gian và mã nhà, quy đổi tiền, giá/m², thứ tự khoảng dự đoán, '
      'TreeSHAP tái tạo đầu ra, kiểm tra đầu vào ngoài miền, giao dịch đối chiếu không dùng tương lai, nhập dataset lặp và lưu chỉ yêu cầu API hợp lệ.')
    p('Kiểm tra chức năng được thực hiện bằng API và bộ kiểm thử. Chưa có kết quả kiểm tra giao diện trực quan trên nhiều kích thước màn hình trong bản báo cáo này. '
      'Cấu hình Docker đã bổ sung dataset và bước huấn luyện để ảnh mới có mô hình King County; '
      'chưa có kết quả build Docker mới được công bố trong bản báo cáo này.')
    table(['Giới hạn', 'Hệ quả và hướng xử lý'], [
        ['Một quận và khoảng 13 tháng', 'Chưa chứng minh chuyển vùng hoặc chu kỳ thị trường dài'],
        ['Nguồn thuộc tính lịch sử', 'Cần đối soát vintage từng thuộc tính trước định giá thực tế'],
        ['Chưa có tiện ích lịch sử', 'Không giải thích bằng gần trường hay cửa hàng'],
        ['Đuôi giá cao và tài sản đặc biệt', 'Báo cáo sai số theo nhóm, mở rộng dữ liệu tương ứng'],
        ['Khoảng dự đoán còn rộng', 'Theo dõi cả độ phủ và bề rộng, hiệu chỉnh trên kỳ mới'],
        ['Giá VND quy đổi', 'Giữ nhãn thị trường Mỹ và ngày tỷ giá trong giao diện']], [2.35, 4.2])
    p('Ưu tiên tiếp theo là thu thập giao dịch mới, đối soát hồ sơ thuộc tính đúng tại ngày bán và lấy dữ liệu tiện ích hợp lệ. Sau đó thiết kế một kỳ test mới trước khi chọn lại '
      'đặc trưng hoặc tham số. Mọi nhận định về tác động của trường học, cửa hàng hoặc điều kiện môi trường cần phân biệt dự đoán với suy luận nhân quả.')
    p('Kết quả hiện tại chứng minh có thể xây một hệ thống học máy nhất quán từ dataset đến giao diện, kèm bằng chứng, kiểm thử và phạm vi sử dụng rõ ràng. '
      'Sai số và giới hạn nguồn dữ liệu vẫn cần được giữ nguyên khi trình bày kết quả hoặc chia sẻ ứng dụng.')

    heading('14 Tài liệu tham khảo và dấu vết dữ liệu', new_page=True)
    refs = [
        '[1] Kaggle, harlfoxem. House Sales in King County, USA. https://www.kaggle.com/datasets/harlfoxem/housesalesprediction',
        '[2] GeoDa Center. 2014–15 Home Sales in King County, WA. https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/',
        '[3] scikit-learn. Cross validation and common pitfalls. https://scikit-learn.org/stable/modules/cross_validation.html và https://scikit-learn.org/stable/common_pitfalls.html',
        '[4] Angelopoulos, A. N. và Bates, S. A Gentle Introduction to Conformal Prediction and Distribution Free Uncertainty Quantification, 2021, bản cập nhật 2022. https://arxiv.org/abs/2107.07511',
        '[5] XGBoost. Prediction và pred_contribs. https://xgboost.readthedocs.io/en/stable/prediction.html',
        '[6] Vietcombank. Bảng tỷ giá ngoại tệ và XML công khai. https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-tien-ich/Ty-gia',
        '[7] OpenStreetMap. Copyright and License, ODbL. https://www.openstreetmap.org/copyright',
        '[8] NCES. Public Elementary Secondary School Universe Survey. https://nces.ed.gov/ccd/pubschuniv.asp',
    ]
    for reference in refs:
        paragraph = p(reference)
        for run in paragraph.runs:
            run.font.size = Pt(11)
    heading('Dấu vết tái lập', 2)
    p('Mã SHA-256 dataset: ' + M['dataset_sha256'])
    p('Mã phiên bản model: ' + M['model_version'])
    p('Snapshot tỷ giá: real_estate_ai/data/context/vietcombank.xml. Mã SHA-256: ' + M['exchange_rate']['sha256'])
    p('Các số liệu và biểu đồ trong báo cáo lấy từ metadata.json, validation_metrics.csv, test_predictions.csv, feature_importance.csv và evidence.json trong artifacts/kingcounty. '
      'Tập test, danh sách chia tập và các mã bị loại đều có file để đối chiếu. Các địa điểm tiện ích chưa có dữ liệu được ghi nhận rõ, không có bản đồ hay con số vị trí nào được dựng giả.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # Remove decorative Title borders inherited from the runtime's default template.
    for element in DOC.styles.element.xpath('.//w:pBdr') + DOC.element.xpath('.//w:pBdr'):
        element.getparent().remove(element)
    for paragraph in DOC.paragraphs:
        if paragraph.style.name == 'Title':
            for run in paragraph.runs:
                run.font.underline = False
    DOC.save(OUT)
    (ROOT / 'docs/Phan_tich_Gia_nha_King_County.md').write_text('\n'.join(markdown), encoding='utf-8')
    print('Report created:', OUT)


if __name__ == '__main__':
    main()
