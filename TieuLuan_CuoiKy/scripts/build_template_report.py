"""Patch the retained university report package without rebuilding its styles."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

from lxml import etree as X
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'real_estate_ai/artifacts/vietnam'
REFERENCE=ROOT/'docs/templates/mau_bao_cao_goc.docx'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
qn=lambda name:'{'+NS[name.split(':')[0]]+'}'+name.split(':')[1]


def fmt(value,n=0):
    return f'{value:,.{n}f}'.replace(',','_').replace('.',',').replace('_','.')


def billion(value):return fmt(value/1e9,2)
def pct(value):return fmt(value*100,1)+'%'


def content(evidence):
    M,L=evidence['metadata'],evidence['linear']; blocks=[]
    def h(text,level=2):blocks.append({'type':'heading','text':text,'level':level})
    def p(text):blocks.append({'type':'paragraph','text':text})
    def code(text):blocks.append({'type':'code','text':text})
    def table(caption,headers,rows,widths):blocks.append({'type':'table','caption':caption,'headers':headers,'rows':rows,'widths':widths})
    def fig(name,caption,height=4.1):blocks.append({'type':'figure','name':name,'caption':caption,'max_height':height})
    h('CHƯƠNG 1 TỔNG QUAN ĐỀ TÀI',1)
    h('1.1 Bài toán và kết quả chính')
    p('Đề tài phân tích giá rao bán nhà ở tại TP.HCM và Hà Nội bằng House Price Prediction Dataset Vietnam 2024 của Nguyen Tien Nhan trên Kaggle. '
      'Giá là đại lượng liên tục nên sử dụng hồi quy có giám sát. Sản phẩm gồm notebook thực nghiệm, mô hình, giao diện web và API lưu lịch sử dự đoán.')
    p(f'CSV gốc có {fmt(M["audit"]["raw_rows"])} dòng và 12 cột; phạm vi nghiên cứu giữ {fmt(M["audit"]["accepted_rows"])} tin. '
      f'OLS chọn 6 trong 12 nhóm đầu vào sau xử lý. Mô hình XGBoost phục vụ đạt R² {fmt(M["test"]["r2"],3)}, '
      f'MAE {billion(M["test"]["mae_vnd"])} tỷ VND và MdAPE {pct(M["test"]["median_ape"])} trên {fmt(M["test"]["n"])} tin test.')
    p('Đây là nghiên cứu giá rao theo nguồn năm 2024, chưa xác minh giá chốt giao dịch. Dataset không có ngày đăng từng tin nên kết quả chia theo nhóm '
      'không chứng minh khả năng dự báo giá ở thời kỳ tương lai hoặc giá thị trường hiện tại.')
    h('1.2 Phạm vi và câu hỏi nghiên cứu')
    p('Nghiên cứu xem xét số lượng đặc trưng có thể sử dụng, đặc trưng nào bổ sung nhiều thông tin tuyến tính nhất và mô hình dự đoán tốt đến mức nào '
      'trên các nhóm tin chưa được fit. Các lý do kinh tế giúp diễn giải kết quả; phép kiểm tra validation là bằng chứng lựa chọn biến.')
    table('Phạm vi dữ liệu và sản phẩm',['Nội dung','Notebook và báo cáo','Ứng dụng'],[
        ['Nguồn','Kaggle Việt Nam 2024, phiên bản 8','Cùng model và danh mục Kaggle'],
        ['Đơn vị','Price tỷ VND được nhân 1e9','VND và triệu VND/m²'],
        ['Lựa chọn biến','OLS đầy đủ và OLS chọn 6 nhóm','XGBoost dùng 12 nhóm'],
        ['Đánh giá','Train, validation, calibration, test theo nhóm','Dự đoán, khoảng và tin đối chiếu']],[1.15,2.4,2.35])
    h('1.3 Công nghệ và cấu trúc sản phẩm')
    table('Công nghệ sử dụng',['Thành phần','Vai trò'],[
        ['Python 3.12','Môi trường thực thi trong .venv'],['NumPy và Pandas','Làm sạch, thống kê và xử lý bảng'],
        ['Matplotlib','Biểu đồ EDA và sai số'],['scikit-learn','Pipeline, OLS, chuẩn hóa và chia nhóm'],
        ['XGBoost và joblib','Huấn luyện, TreeSHAP và lưu model'],['Flask và HTML CSS JavaScript','Giao diện và JSON API'],
        ['SQLAlchemy và SQLite','Lưu catalog quan sát và lịch sử'],['pytest','Kiểm tra đơn vị, model, API và launcher']],[2,3.9])
    p('Dữ liệu và chỉ số được lưu trong artifacts/vietnam. Word, PowerPoint và notebook đọc cùng artifact đánh giá; '
      'các ví dụ được chọn theo quy tắc cố định trước khi xem sai số.')

    h('CHƯƠNG 2 DỮ LIỆU VÀ TIỀN XỬ LÝ',1)
    h('2.1 Nguồn và đặc điểm bộ dữ liệu')
    p('Nguyen Tien Nhan công bố dataset House Price Prediction Dataset Vietnam 2024 trên Kaggle. Theo mô tả tác giả, dữ liệu được thu thập từ batdongsan.vn. '
      'Bản sử dụng là phiên bản 8, cập nhật ngày 22/09/2024, giấy phép CC0 Public Domain theo metadata Kaggle. Một dòng là một tin trong nguồn, '
      'không có ID căn nhà độc lập để xác minh mỗi dòng là một tài sản khác nhau. [1]')
    p('Price có đơn vị tỷ VND. Ví dụ 6,3 tương ứng 6.300.000.000 VND; nhãn được nhân 1.000.000.000 trước khi học. Area dùng m², Frontage và Access Road dùng mét. '
      'Ngày cập nhật dataset không thay thế cho ngày đăng từng tin. Không suy đoán loại nhà, ngày đăng hoặc tọa độ khi nguồn không cung cấp.')
    p('CSV gốc và manifest lưu schema, phiên bản và SHA256. Pipeline kiểm tra checksum trước khi đọc. '
      'Nguồn trực tiếp: '+M['source']['source_url'])
    h('2.2 Các thuộc tính và lựa chọn đầu vào')
    p('Trong 12 cột gốc, Price là nhãn và 11 cột còn lại là ứng viên ban đầu. Loại Balcony direction vì thiếu trên 80% ở train; '
      'Address được tách thành thành phố, quận/huyện và phường/xã. Mười cột nguồn còn sử dụng tạo thành 12 nhóm đầu vào: 6 biến số và 6 nhóm danh mục.')
    table('Các thuộc tính trong CSV Kaggle',['Cột','Đơn vị hoặc dạng','Cách sử dụng'],[
        ['Address','Chuỗi địa chỉ','Tách ba nhóm địa bàn'],['Area','m²','Giữ; lấy log trong OLS'],
        ['Frontage','m','Giữ; điền thiếu từ train'],['Access Road','m','Giữ; điền thiếu từ train'],
        ['House direction','8 hướng','Giữ; mức Không rõ nếu thiếu'],['Balcony direction','8 hướng','Loại; thiếu '+pct(M['audit']['training_missing_fraction']['balcony_direction'])],
        ['Floors','Số tầng','Giữ'],['Bedrooms','Số phòng ngủ','Giữ'],['Bathrooms','Số phòng tắm','Giữ'],
        ['Legal status','Giấy chứng nhận hoặc hợp đồng','Giữ'],['Furniture state','Full hoặc Basic','Giữ'],['Price','Tỷ VND','Nhãn y, loại khỏi X']],[1.5,1.7,2.7])
    p(f'Sau one-hot và thêm cờ thiếu, OLS đầy đủ có {L["encoded_column_count"]} cột thiết kế. '
      'Cần phân biệt cột nguồn, nhóm đầu vào và cột sau mã hóa. Giá/m² quan sát được suy ra từ nhãn nên không đưa vào X. '
      'Đơn giá dự đoán chỉ được tính sau khi mô hình dự đoán tổng giá.')
    h('2.3 Kiểm tra chất lượng và làm sạch')
    p('Địa chỉ được chuẩn hóa Unicode, khoảng trắng, dấu chấm cuối và một số alias TP.HCM/Hà Nội. Quận/huyện được lấy từ phần cuối địa chỉ; '
      'chỉ nhận phường/xã khi có tiền tố phù hợp, phần không chắc chắn ghi Không rõ. Tên địa bàn được giữ theo nguồn năm 2024.')
    table('Kết quả kiểm tra dữ liệu',['Hạng mục','Kết quả'],[
        ['CSV gốc',fmt(M['audit']['raw_rows'])+' dòng, 12 cột'],['Hai thành phố',fmt(M['audit']['in_scope_rows'])],
        ['Ngoài phạm vi hoặc địa chỉ không hợp lệ',fmt(M['audit']['invalid_or_outside_price_scope'])],
        ['Dòng trùng toàn bộ 12 cột bị loại',fmt(M['audit']['exact_duplicate_rows_removed'])],['Tin giữ lại',fmt(M['audit']['accepted_rows'])],
        ['Nhóm địa chỉ và diện tích',fmt(M['audit']['property_proxy_groups'])]],[3.9,2])
    p('Giới hạn nghiên cứu là giá 0,5–200 tỷ VND, diện tích 15–1.000 m² và đơn giá 5–800 triệu VND/m². '
      'Đây là phạm vi đánh giá, không khẳng định mọi quan sát ngoài khoảng đều là lỗi. Dữ liệu thực tế giữ lại có giá 1–11,5 tỷ VND; '
      'không suy rộng chất lượng sang phân khúc cao hơn.')
    fig('missingness','Tỷ lệ thiếu của các biến số trên tập train',3.4)
    p('Giá trị kết cấu ngoài miền hợp lệ được chuyển thành thiếu. Trung vị điền thiếu, cờ thiếu và các bước mã hóa được học trong train. '
      f'Hướng nhà thiếu {pct(M["audit"]["training_missing_fraction"]["house_direction"])} và đường trước nhà thiếu '
      f'{pct(M["audit"]["training_missing_fraction"]["road_width"])}; các diễn giải liên quan cần thận trọng.')
    h('2.4 Chia dữ liệu và kiểm soát rò rỉ')
    p('Khóa nhóm gồm địa chỉ chuẩn hóa và diện tích làm tròn 0,1 m², không chứa giá. Các tin cùng khóa được giữ cùng một tập để hạn chế tin đăng lại '
      'xuất hiện ở cả train và test. Khóa vẫn có thể gộp các căn khác nhau cùng địa chỉ/diện tích và bỏ sót tin đổi cách ghi. [2]')
    table('Phân chia dữ liệu theo nhóm',['Tập','Số tin','Số nhóm','Vai trò'],[
        [key,fmt(part['n']),fmt(part['groups']),{'train':'Fit và học tiền xử lý','validation':'Chọn biến và mô hình','calibration':'Hiệu chỉnh khoảng','test':'Đánh giá cuối'}[key]]
        for key,part in M['splits'].items()],[1.05,.85,.95,3.05])
    p('GroupShuffleSplit tách xấp xỉ 60%/15%/10%/15% số nhóm với seed 42, 43 và 44 ở các bước. Không có khóa nhóm chung giữa hai tập. '
      'Sau chọn XGBoost, chỉ fit lại train và validation. Calibration dùng hiệu chỉnh khoảng; test không dùng để chọn biến. '
      'Do thiếu ngày đăng, đây chưa phải đánh giá dự báo theo thời gian.')

    h('CHƯƠNG 3 PHÂN TÍCH KHÁM PHÁ DỮ LIỆU',1)
    h('3.1 Phân bố giá rao bán')
    p('Biểu đồ phân bố được dựng riêng trên train. Giá nguồn bị giới hạn trong miền quan sát; hình log hỗ trợ xem thay đổi theo tỷ lệ. '
      'Mô hình học log giá, nhưng MAE, RMSE và R² được tính lại trên VND. Sai số log nhỏ hơn không tự động bảo đảm RMSE VND nhỏ hơn.')
    fig('price_distribution','Phân bố giá rao và giá sau biến đổi log trên train',3.7)
    h('3.2 Quan hệ giữa diện tích số phòng và giá')
    p('Mỗi thành phố lấy mẫu cố định 1.200 tin train để nhìn mối liên hệ diện tích và giá. Cùng diện tích vẫn có nhiều mức giá; '
      'quy mô đơn lẻ chưa đủ định giá một căn nhà. Diện tích khai báo có thể là diện tích đất hoặc sàn, chưa được đối chiếu hồ sơ.')
    fig('area_price','Diện tích và giá rao trong mẫu train của hai thành phố',3.5)
    fig('rooms','Giá trung vị theo số phòng với ít nhất 50 tin train mỗi nhóm',3.4)
    p('Số phòng tương quan với diện tích và kết cấu. Không suy ra một phòng ngủ hoặc phòng tắm luôn cộng một khoản tiền cố định. '
      'Dataset không có cột loại nhà nên biểu đồ gộp bất động sản trong nguồn, không được gọi riêng là nhà riêng hoặc căn hộ.')
    h('3.3 Phân bố giá theo địa bàn')
    fig('districts','Đơn giá trung vị ở các quận huyện có ít nhất 100 tin train',3.8)
    p('Đơn giá giữa các địa bàn khác nhau, phù hợp với việc giữ vị trí trong mô hình. Bảng mẫu không đại diện bảng giá hiện tại của toàn thành phố. '
      'Nguồn không có tọa độ hoặc khoảng cách trường học/cửa hàng đã xác minh nên không sử dụng các đặc trưng tiện ích này.')

    h('CHƯƠNG 4 MÔ HÌNH VÀ ĐÁNH GIÁ',1)
    h('4.1 Lựa chọn thuật toán và cấu hình')
    table('Các mô hình trong thực nghiệm',['Mô hình','Đặc điểm','Vai trò'],[
        ['Trung vị khu vực','Trung vị giá/m² theo thành phố và quận','Đối chứng'],['OLS đầy đủ','Học log giá với 12 nhóm','Giải thích và xếp hạng'],
        ['OLS chọn lọc','Bộ gọn theo validation','Chọn nhóm biến tuyến tính'],['XGBoost','Cây tăng cường, có hoặc không địa bàn','Mô hình phi tuyến phục vụ']],[1.45,2.9,1.55])
    p('XGBoost dùng 430 cây, max_depth 6, learning_rate 0,055, min_child_weight 12, subsample 0,85, colsample_bytree 0,9, '
      'reg_lambda 6, tree_method hist, n_jobs 2 và random_state 42. Đây là cấu hình thực nghiệm, chưa tìm kiếm tối ưu toàn diện. [3]')
    h('4.2 Tiền xử lý và thước đo đánh giá')
    p('OLS học y = ln(giá VND); diện tích được lấy log. Sáu biến số được điền trung vị, thêm cờ thiếu và chuẩn hóa từ train. '
      'Danh mục được one-hot với nhóm tham chiếu, gộp mức hiếm. Các hệ số danh mục phụ thuộc nhóm tham chiếu nên không xếp hạng trực tiếp cùng hệ số số học. [4]')
    p('MAE là độ lệch tuyệt đối trung bình; RMSE nhạy hơn với sai số lớn; R² là hệ số xác định và không phải tỷ lệ dự đoán đúng. '
      'MdAPE là trung vị sai số phần trăm tuyệt đối. Các mô hình được chọn bằng validation; test được giữ cho đánh giá cuối.')
    h('4.3 Độ quan trọng bằng hồi quy tuyến tính')
    p('Mỗi lần bỏ một nhóm đầu vào, fit lại OLS trên train rồi đo mức tăng RMSE log trên cùng validation. Sai số tăng nhiều khi bỏ nhóm nghĩa là '
      'nhóm có thêm thông tin tuyến tính trong mô hình này. Cách này so sánh được biến số và danh mục, tránh xếp hạng hệ số thô khác đơn vị.')
    fig('linear_importance','Mức tăng RMSE log khi bỏ nhóm và fit lại OLS',4.0)
    p(f'Diện tích đứng đầu với mức tăng {fmt(L["importance"][0]["delta_rmse_log"],4)}; tiếp theo là quận/huyện và số tầng. '
      'Giá trị gần 0 hoặc âm nghĩa là ít bổ sung thông tin sau các biến khác, chưa chứng minh biến không liên quan đến giá hoặc không có tương tác phi tuyến.')
    fig('linear_coefficients','Hệ số của sáu biến số sau chuẩn hóa trong OLS đầy đủ',3.4)
    p('Hệ số thể hiện thay đổi dự đoán log giá khi biến số tăng một độ lệch chuẩn, với các biến khác giữ nguyên. '
      'Đây là quan hệ có điều kiện trong mẫu, chưa phải tác động nhân quả hoặc mức cộng tiền cố định.')
    h('4.4 Chọn số biến và lý do sử dụng')
    fig('linear_selection','Sai số validation khi thêm nhóm theo thứ hạng OLS',3.2)
    p(f'Chọn prefix nhỏ nhất có RMSE log không quá 1% so với bộ tốt nhất. Kết quả chọn {L["selected"]["k"]} nhóm, '
      f'RMSE log validation {fmt(L["selected"]["validation"]["rmse_log"],4)}, so với {fmt(L["full_validation"]["rmse_log"],4)} ở OLS đầy đủ. '
      'Tiêu chí chấp nhận sai số nhỉnh hơn để có mô hình tuyến tính gọn hơn.')
    table('Các nhóm biến OLS được chọn',['Nhóm biến','Lý do dự báo','Lưu ý'],[
        ['Diện tích','Mô tả quy mô tài sản','Đất hay sàn chưa xác minh'],['Quận/huyện','Mặt bằng giá khu vực','Địa danh theo nguồn'],
        ['Số tầng','Bổ sung thông tin kết cấu','Không phải tiền cộng mỗi tầng'],['Phường/xã','Vị trí chi tiết hơn','Có mức hiếm và chưa rõ'],
        ['Pháp lý','Danh mục giấy tờ và khai báo','Chưa xác minh hồ sơ'],['Đường trước nhà','Khả năng tiếp cận','Thiếu '+pct(M['audit']['training_missing_fraction']['road_width'])]],[1.3,2.6,2])
    p('Số phòng có thể chia sẻ thông tin với diện tích; thành phố lồng trong quận/huyện. Việc không chọn một nhóm vào OLS gọn không có nghĩa '
      'nhóm đó không liên quan đến giá. Pháp lý cũng có mức Không rõ nên liên hệ dự báo có thể phản ánh chất lượng khai báo và cơ cấu khu vực.')
    h('4.5 So sánh mô hình trên Validation')
    rows=[[r['model'],billion(r['rmse_vnd']),fmt(r['r2'],3)] for r in M['validation_comparison']]
    rows += [['OLS đủ 12 nhóm',billion(L['full_validation']['rmse_vnd']),fmt(L['full_validation']['r2_vnd'],3)],
             ['OLS chọn 6 nhóm',billion(L['selected']['validation']['rmse_vnd']),fmt(L['selected']['validation']['r2_vnd'],3)]]
    table('Kết quả trên tập Validation',['Mô hình','RMSE tỷ VND','R²'],rows,[3.4,1.4,1.1])
    fig('model_comparison','RMSE của các mô hình XGBoost và đối chứng trên Validation',3.5)
    p('Thêm địa bàn làm RMSE XGBoost giảm từ 1,58 xuống 1,24 tỷ VND trên validation. Ứng dụng phục vụ XGBoost với 12 nhóm. '
      'Bộ OLS sáu nhóm là thí nghiệm riêng; chưa so XGBoost sáu nhóm với XGBoost 12 nhóm, nên không khẳng định giữ 12 nhóm tốt hơn sáu nhóm cho mọi thuật toán.')
    h('4.6 Kết quả Test và khoảng dự đoán')
    table('Kết quả trên tập Test giữ riêng',['Phạm vi','Số tin','R²','MdAPE','Độ phủ'],[
        ['Toàn bộ',fmt(M['test']['n']),fmt(M['test']['r2'],3),pct(M['test']['median_ape']),pct(M['test']['coverage_90'])]]+
        [[r['label'],fmt(r['n']),fmt(r['r2'],3),pct(r['median_ape']),pct(r['coverage_90'])] for r in M['test_breakdown']],[1.5,.9,.8,1.2,1.5])
    p(f'MAE test {billion(M["test"]["mae_vnd"])} tỷ VND và RMSE {billion(M["test"]["rmse_vnd"])} tỷ VND. '
      f'{pct(M["test"]["within_20pct"])} tin có sai lệch không quá ±20%. Baseline có RMSE test {billion(M["baseline_test"]["rmse_vnd"])} tỷ VND. '
      'Không so trực tiếp các chỉ số này với dataset khác có miền giá và cách chia khác.')
    fig('test_errors','Giá nguồn dự đoán và phân bố sai số trên Test',3.5)
    p('Khoảng danh nghĩa 90% được hiệu chỉnh bằng phân vị phần dư tuyệt đối log giá trên calibration theo split conformal. '
      f'Độ phủ quan sát trên test là {pct(M["test"]["coverage_90"])}; bề rộng trung vị {billion(M["test"]["median_interval_width_vnd"])} tỷ VND. '
      'Độ phủ hai thành phố khác nhau; nhiều tin trong cùng nhóm có thể phụ thuộc nhau. Không bảo đảm mức phủ cho mọi phân khúc hoặc thời kỳ mới.')
    h('4.7 Minh họa dự đoán và giới hạn diễn giải')
    table('Ví dụ test được chọn theo quy tắc cố định',['Thành phố','m²','Ngủ/tắm','Giá rao tỷ','Dự đoán tỷ'],[
        [c['input']['input']['province_name'],fmt(c['input']['input']['area']),fmt(c['input']['input']['bedroom_count'])+'/'+fmt(c['input']['input']['bathroom_count']),
         billion(c['input']['asking_vnd']),billion(c['result']['predicted_vnd'])] for c in evidence['examples']],[1.45,.65,1,1.4,1.4])
    p('Mỗi thành phố chọn tin có giá nguồn trung vị trong nhóm test khai báo đủ phòng và thuộc địa bàn được hỗ trợ, trước khi xem sai số. '
      'Ví dụ TP.HCM là Quận 2, Phường Bình Trưng Tây, 52 m²; giá rao 6,30 tỷ và dự đoán 6,56 tỷ VND. '
      'Ví dụ Hà Nội là Hà Đông, Phường Vạn Phúc, 31 m²; giá rao 5,80 tỷ và dự đoán 5,21 tỷ VND.')
    fig('example_explanation','Đóng góp TreeSHAP của ví dụ TP HCM trên thang log VND',3.8)
    p('TreeSHAP cộng các đóng góp với mức nền trên log giá rồi lấy hàm mũ để tái tạo dự đoán trong sai số dấu phẩy động. '
      'Không đổi từng thanh thành VND rồi cộng trực tiếp. TreeSHAP giải thích XGBoost, khác phép bỏ biến và fit lại OLS. [3]')

    h('CHƯƠNG 5 ỨNG DỤNG WEB API VÀ KIỂM THỬ',1)
    h('5.1 Kiến trúc và tổ chức mã nguồn')
    p('Trình duyệt hiển thị HTML/CSS và xử lý tương tác JavaScript; Flask phục vụ JSON API; SQLAlchemy đọc ghi SQLite. '
      'Model, quy tắc đầu vào và danh mục địa bàn cùng thuộc nguồn Kaggle 2024. Lịch sử dự đoán lưu theo phiên bản để không nhầm kết quả từ nguồn cũ.')
    table('Trách nhiệm các thành phần ứng dụng',['Thành phần','Vai trò'],[
        ['backend/launch_ui.py','Kiểm tra môi trường, model và cổng chạy'],['backend/kaggle_vietnam.py','Nguồn, địa chỉ và chia nhóm'],
        ['backend/vietnam.py','Pipeline, kiểm tra đầu vào, dự đoán và TreeSHAP'],['backend/train_vietnam.py','Train, validation, calibration và test'],
        ['backend/vietnam_api.py','API và lịch sử model hiện hành'],['backend/import_vietnam_data.py','Catalog nguồn Kaggle riêng'],
        ['frontend/templates và static','Giao diện nhập liệu và xem kết quả']],[2.5,3.4])
    h('5.2 Giao diện và luồng thao tác')
    p('Chọn tin mẫu chưa dùng fit hoặc nhập thành phố, quận/huyện, phường/xã và diện tích. Các thông tin số phòng, số tầng, mặt tiền, '
      'đường, hướng nhà, pháp lý và nội thất có thể để chưa biết. Bấm Dự đoán và lưu kết quả để xem giá, đơn giá, khoảng 90%, giải thích và tin đối chiếu.')
    fig('app_ui','Giao diện kết quả và giải thích dự đoán từ Kaggle 2024',6.2)
    p('Tin đối chiếu cùng quận/huyện được lấy từ train và validation; ưu tiên gần diện tích, số phòng và phường/xã. '
      'Không hiển thị ngày đăng hoặc loại nhà chưa có, không gọi là giao dịch đã bán hoặc các căn gần nhất khi thiếu tọa độ. '
      'Nguồn và giới hạn được hiển thị ngay trên giao diện.')
    h('5.3 API và lưu trữ dữ liệu')
    table('Các API Việt Nam',['Phương thức','Đường dẫn','Chức năng'],[
        ['GET','/api/vietnam/info','Nguồn, metric, schema và tin mẫu'],['POST','/api/vietnam/predict','Kiểm tra, dự đoán, giải thích và lưu'],
        ['GET','/api/vietnam/history','Lịch sử phiên bản model hiện hành']],[1,2.1,2.8])
    p('Catalog quan sát lưu trong vietnam_2024_listings, tách khỏi dữ liệu đã nhập trước. vietnam_predictions lưu đầu vào, dự đoán và model_version. '
      'Không dùng giá mô hình tự dự đoán làm nhãn. API từ chối giá, giá/m² hoặc cột ngoài schema; giá trị không hợp lệ không được ghi lịch sử.')
    p('SQLite đặt tại real_estate_ai/storage/real_estate.db; không cần bật PostgreSQL khi chạy chay_ui.cmd. '
      'Các bảng cũ và lịch sử vẫn được giữ; API lọc theo model hiện hành. Chương trình là ứng dụng cục bộ, chưa có xác thực để triển khai công khai.')
    h('5.4 Cài đặt và khởi động')
    p('Máy hiện tại đã có .venv và model. Từ thư mục Python_k18, mở TieuLuan_CuoiKy/chay_ui.cmd. Máy mới chạy scripts/cai_dat.cmd trước bằng Python 3.12. '
      'File chạy luôn dùng Python trong .venv của dự án, tránh phụ thuộc interpreter đang chọn trong VS Code.')
    code('.\\TieuLuan_CuoiKy\\chay_ui.cmd')
    p('Launcher kiểm tra model Kaggle và SQLite. Nếu có phiên đang chạy khớp mã nguồn và model, dùng lại phiên đó; nếu cổng 8000 bị phiên khác chiếm, '
      'tự chọn cổng kế tiếp và in đúng URL. Mặc định truy cập http://127.0.0.1:8000. Giữ terminal mở khi sử dụng và Ctrl+C để dừng.')
    p('Huấn luyện lại bằng scripts/huan_luyen.cmd. Chạy scripts/analyze_vietnam_linear.py và scripts/build_vietnam_evidence.py bằng Python trong .venv '
      'để tạo lại phân tích. Notebook PhanTich_GiaNha_VietNam.ipynb kiểm tra checksum và tính lại metric từ mô hình đã khóa.')
    h('5.5 Kiểm thử và kết quả vận hành')
    p('Bản sửa hiện tại đạt 100 kiểm thử, bỏ qua một kiểm thử PostgreSQL do chưa cấu hình dịch vụ test. '
      'Đã kiểm tra file chay_ui.cmd thực tế, chạy mới và dùng lại phiên tương thích. Giao diện được thử dự đoán cho cả hai thành phố trên máy tính và điện thoại.')
    table('Các nhóm hành vi được kiểm thử',['Nhóm','Hành vi xác nhận'],[
        ['Nguồn và đơn vị','Schema 12 cột, checksum và Price nhân 1e9'],['Chia nhóm','Tin cùng khóa cùng tập; holdout không dùng fit'],
        ['Model','Metric khớp dự đoán và tổng đóng góp TreeSHAP'],['API và database','Từ chối nhãn trong X, chỉ lưu đầu vào hợp lệ, giữ lịch sử cũ'],
        ['Khởi động','Dùng lại phiên khớp, tránh phiên mã nguồn cũ và cổng bận']],[1.6,4.3])
    p('Kiểm thử hành vi phần mềm không thay thế đánh giá chất lượng dự đoán thị trường. Cấu hình Docker đã chứa nguồn cần thiết cho các kiểm thử; '
      'chưa công bố image mới bằng thao tác này.')

    h('CHƯƠNG 6 KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN',1)
    h('6.1 Kết quả đạt được')
    p('Đề tài hoàn thành quy trình từ dataset Kaggle 2024 đến làm sạch, khám phá, chọn feature OLS và phục vụ XGBoost. '
      'Word, PPT và notebook dùng cùng số liệu. Bộ OLS gọn có diện tích, quận/huyện, số tầng, phường/xã, pháp lý và đường trước nhà; '
      'diện tích có thêm thông tin tuyến tính lớn nhất theo phép bỏ biến.')
    p(f'Test gồm {fmt(M["test"]["n"])} tin và có R² {fmt(M["test"]["r2"],3)}, MdAPE {pct(M["test"]["median_ape"])}. '
      'Kết quả cho thấy mô hình học được tín hiệu dự báo trong mẫu, đồng thời vẫn còn sai số và độ bất định đáng kể.')
    h('6.2 Hạn chế')
    p('Giá là giá rao năm 2024; chưa có giá chốt giao dịch, ID nhà thật, ngày đăng, loại nhà hoặc tọa độ xác minh. '
      'Phạm vi giá quan sát 1–11,5 tỷ VND không đại diện toàn thị trường. Diện tích có thể là đất hoặc sàn; tỷ lệ thiếu một số thuộc tính cao.')
    p('Chia nhóm địa chỉ và diện tích chỉ hạn chế một phần trùng lặp. Chưa kiểm định theo thời gian hoặc độ bền qua nhiều lần chia. '
      'Các hệ số OLS và đóng góp TreeSHAP không chứng minh nhân quả. Khoảng dự đoán hiệu chỉnh gộp không bảo đảm độ phủ ở mọi thành phố hoặc phân khúc.')
    h('6.3 Hướng phát triển')
    p('Ưu tiên bổ sung ngày đăng, ID ổn định, nguồn giao dịch đã xác minh và diện tích thống nhất. Khi có dữ liệu mới, '
      'đánh giá theo thời gian/vùng, kiểm tra độ bền lựa chọn biến và so XGBoost sáu nhóm với XGBoost 12 nhóm trên validation riêng.')
    p('Có thể bổ sung tiện ích khi có tọa độ và snapshot POI cùng thời kỳ, rồi đo phần cải thiện trên holdout mới. '
      'Phân tích sai số và hiệu chỉnh khoảng theo phân khúc cần được kiểm tra trước khi sử dụng ngoài mục đích học tập.')
    h('TÀI LIỆU THAM KHẢO',1)
    for text in [
        '[1] Nguyen Tien Nhan. House Price Prediction Dataset Vietnam 2024. Kaggle, phiên bản 8, CC0 Public Domain. '+M['source']['source_url'],
        '[2] Scikit-learn. GroupShuffleSplit. https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html',
        '[3] XGBoost. Prediction và pred_contribs. https://xgboost.readthedocs.io/en/stable/prediction.html',
        '[4] Scikit-learn. LinearRegression. https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html',
        'Các nguồn được đối chiếu ngày 07/11/2026. Số liệu tái lập trong artifacts/vietnam/metadata.json, linear_analysis.json, split.json và test_predictions.csv.',
        'Mã model: '+M['model_version']+'. SHA256 CSV nguồn: '+M['source']['files'][0]['sha256']+'.']:
        p(text)
    h('BẢNG PHÂN CÔNG NHIỆM VỤ',1)
    table('Các hạng mục thực hiện',['Hạng mục','Sản phẩm','Người phụ trách'],[
        ['Dữ liệu và tiền xử lý','CSV xác minh, nhóm và notebook','Nguyễn Duy Trường'],['Mô hình và phân tích','OLS, XGBoost, biểu đồ và metric','Nguyễn Duy Trường'],
        ['Ứng dụng và kiểm thử','Giao diện, API, SQLite và launcher','Nguyễn Duy Trường'],['Tài liệu','Word và PowerPoint cùng nguồn Kaggle','Nguyễn Duy Trường']],[1.7,2.7,1.5])
    return blocks


def patch_report(output,page_map=None):
    evidence=json.loads((ART/'evidence.json').read_text(encoding='utf-8'))
    blocks=content(evidence)
    image_hashes={b['name']:hashlib.sha256((ART/'charts'/(b['name']+'.png')).read_bytes()).hexdigest() for b in blocks if b['type']=='figure'}
    content_fingerprint=hashlib.sha256(json.dumps({'blocks':blocks,'images':image_hashes},ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
    if page_map and page_map.get('content_fingerprint')!=content_fingerprint:
        raise ValueError('Page map does not match report content. Rebuild with --draft, render, and update_report_pages.py.')
    manifest=json.loads((REFERENCE.parent/'manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(REFERENCE.read_bytes()).hexdigest()!=manifest['sha256']:
        raise ValueError('Reference template changed; repeat template distillation.')
    with ZipFile(REFERENCE) as z: package={n:z.read(n) for n in z.namelist()}
    document=X.fromstring(package['word/document.xml']);body=document.find('w:body',NS)
    original=list(body);relations=X.fromstring(package['word/_rels/document.xml.rels'])
    added={};headings=[];figures=[];tables=[];new_body=[];bookmark_id=5000
    pages=(page_map or {}).get('anchors',{})
    def paragraph(value,prototype=94,anchor=None):
        nonlocal bookmark_id
        item=deepcopy(original[prototype]);props=item.find('w:pPr',NS)
        source_run=item.find('.//w:r',NS);run_props=source_run.find('w:rPr',NS) if source_run is not None else None
        for child in list(item):
            if child is not props:item.remove(child)
        if anchor:
            start=X.SubElement(item,qn('w:bookmarkStart'));start.set(qn('w:id'),str(bookmark_id));start.set(qn('w:name'),anchor)
        run=X.SubElement(item,qn('w:r'))
        if run_props is not None:run.append(deepcopy(run_props))
        for index,line in enumerate(value.split('\n')):
            if index:X.SubElement(run,qn('w:br'))
            text=X.SubElement(run,qn('w:t'));text.text=str(line);text.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
        if anchor:
            end=X.SubElement(item,qn('w:bookmarkEnd'));end.set(qn('w:id'),str(bookmark_id));bookmark_id+=1
        return item
    def toc_entry(title,anchor,level=1,prototype=None):
        item=deepcopy(original[prototype if prototype is not None else (34 if level==1 else 35)])
        link=item.find('w:hyperlink',NS);link.set(qn('w:anchor'),anchor)
        texts=item.findall('.//w:t',NS)
        if len(texts)<2:raise ValueError('Unsupported TOC pattern')
        for t in texts:t.text=''
        texts[0].text=title;texts[-1].text=str(pages.get(anchor,'?'))
        return item
    def table_element(headers,rows,widths):
        item=deepcopy(original[100]);proto_rows=item.findall('w:tr',NS)
        for r in proto_rows:item.remove(r)
        grid=item.find('w:tblGrid',NS)
        for c in list(grid):grid.remove(c)
        sizes=[round(8504*x/sum(widths)) for x in widths];sizes[-1]=8504-sum(sizes[:-1])
        for width in sizes:c=X.SubElement(grid,qn('w:gridCol'));c.set(qn('w:w'),str(width))
        for row_index,row in enumerate([headers]+rows):
            source=proto_rows[0 if row_index==0 else 1];tr=deepcopy(source)
            cells=source.findall('w:tc',NS)
            for c in tr.findall('w:tc',NS):tr.remove(c)
            trpr=tr.find('w:trPr',NS)
            if trpr is None:trpr=X.Element(qn('w:trPr'));tr.insert(0,trpr)
            for x in list(trpr):
                if x.tag in [qn('w:trHeight'),qn('w:tblHeader')]:trpr.remove(x)
            X.SubElement(trpr,qn('w:cantSplit'))
            if row_index==0:X.SubElement(trpr,qn('w:tblHeader'))
            for col,value in enumerate(row):
                cell=deepcopy(cells[min(col,len(cells)-1)]);props=cell.find('w:tcPr',NS)
                width=props.find('w:tcW',NS);width.set(qn('w:w'),str(sizes[col]));width.set(qn('w:type'),'dxa')
                cp=cell.find('w:p',NS);rpr=cp.find('.//w:rPr',NS);ppr=cp.find('w:pPr',NS)
                for ch in list(cell):
                    if ch is not props:cell.remove(ch)
                p=X.SubElement(cell,qn('w:p'))
                if ppr is not None:p.append(deepcopy(ppr))
                run=X.SubElement(p,qn('w:r'))
                if rpr is not None:run.append(deepcopy(rpr))
                t=X.SubElement(run,qn('w:t'));t.text=str(value)
                tr.append(cell)
            item.append(tr)
        return item
    def table_caption(title):
        anchor='kaggle_table_'+str(len(tables)+1);caption='Bảng '+str(len(tables)+1)+'. '+title
        tables.append({'anchor':anchor,'text':caption})
        return paragraph(caption,89,anchor)
    # Preserve cover, grade form, and source page furniture.
    front=[deepcopy(e) for e in original[:33]]
    front[8]=paragraph('PHÂN TÍCH DỮ LIỆU VÀ\nDỰ ĐOÁN GIÁ NHÀ VIỆT NAM\nVỚI OLS VÀ XGBOOST',8)
    abbr_caption=table_caption('Các từ viết tắt và đơn vị')
    abbr=table_element(['Ký hiệu','Ý nghĩa'],[
        ['OLS','Hồi quy bình phương tối thiểu'],['XGBoost','Mô hình cây tăng cường'],['EDA','Phân tích khám phá dữ liệu'],['CSV','Tệp dữ liệu dạng bảng'],
        ['MAE','Sai số tuyệt đối trung bình'],['RMSE','Căn sai số bình phương trung bình'],['R²','Hệ số xác định'],['MdAPE','Trung vị sai số phần trăm tuyệt đối'],
        ['VND','Đồng Việt Nam'],['m²','Mét vuông'],['UI','Giao diện người dùng'],['API','Giao diện lập trình ứng dụng'],['JSON','Định dạng trao đổi dữ liệu']],[1.4,4.5])
    code_index=next(i for i,p in enumerate(original) if ''.join(p.xpath('.//w:t/text()',namespaces=NS)).startswith('$python'))
    for block in blocks:
        kind=block['type']
        if kind=='heading':
            anchor='kaggle_heading_'+str(len(headings)+1);headings.append({'anchor':anchor,'text':block['text'],'level':block['level']})
            new_body.append(paragraph(block['text'],92 if block['level']==1 else 93,anchor))
        elif kind=='paragraph':new_body.append(paragraph(block['text']))
        elif kind=='code':new_body.append(paragraph(block['text'],code_index))
        elif kind=='table':
            new_body.append(table_caption(block['caption']));new_body.append(table_element(block['headers'],block['rows'],block['widths']))
            new_body.append(paragraph('',101))
        elif kind=='figure':
            image=ART/'charts'/(block['name']+'.png')
            with Image.open(image) as picture:w,h=picture.size
            cx=min(5.8,block['max_height']*w/h)*914400;cy=cx*h/w
            number=len(figures)+1;relation_id='rIdKaggle'+str(number)
            drawing=deepcopy(original[134])
            for bookmark in drawing.xpath('.//w:bookmarkStart|.//w:bookmarkEnd',namespaces=NS):bookmark.getparent().remove(bookmark)
            for extent in drawing.xpath('.//wp:extent|.//a:xfrm/a:ext',namespaces=NS):extent.set('cx',str(round(cx)));extent.set('cy',str(round(cy)))
            for prop in drawing.findall('.//wp:docPr',NS):prop.set('id',str(1000+number));prop.set('name',block['name']);prop.set('descr',block['caption'])
            drawing.find('.//a:blip',NS).set(qn('r:embed'),relation_id)
            relation=X.SubElement(relations,'{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
            relation.set('Id',relation_id);relation.set('Type',NS['r']+'/image');relation.set('Target','media/kaggle_'+block['name']+'.png')
            added['word/media/kaggle_'+block['name']+'.png']=image.read_bytes()
            new_body.append(drawing)
            anchor='kaggle_figure_'+str(number);caption='Hình '+str(number)+'. '+block['caption'];figures.append({'anchor':anchor,'text':caption})
            new_body.append(paragraph(caption,135,anchor))
    for child in list(body):body.remove(child)
    front.append(deepcopy(original[33]))
    front.extend(toc_entry(h['text'],h['anchor'],h['level']) for h in headings)
    front.append(deepcopy(original[67]))
    front.extend(toc_entry(c['text'],c['anchor'],prototype=68) for c in figures)
    front.extend(toc_entry(c['text'],c['anchor'],prototype=74) for c in tables)
    front.extend([deepcopy(original[88]),abbr_caption,abbr,deepcopy(original[91])])
    for element in front+new_body+[deepcopy(original[-1])]:body.append(element)
    def serial(tree):return X.tostring(tree,encoding='UTF-8',xml_declaration=True,standalone=True)
    package['word/document.xml']=serial(document);package['word/_rels/document.xml.rels']=serial(relations)
    settings=X.fromstring(package['word/settings.xml']);update=settings.find('w:updateFields',NS)
    if update is None:update=X.SubElement(settings,qn('w:updateFields'))
    update.set(qn('w:val'),'true');package['word/settings.xml']=serial(settings)
    app=X.fromstring(package['docProps/app.xml'])
    for element in app:
        if X.QName(element).localname=='Pages':element.text=str((page_map or {}).get('pages',0))
    package['docProps/app.xml']=serial(app)
    core=X.fromstring(package['docProps/core.xml'])
    for element in core:
        if X.QName(element).localname=='title':element.text='Phân tích dữ liệu và dự đoán giá nhà Việt Nam với OLS và XGBoost'
        if X.QName(element).localname=='modified':element.text=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    package['docProps/core.xml']=serial(core)
    output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(output,'w',ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in package.items():z.writestr(name,data)
        for name,data in added.items():z.writestr(name,data)
    allowed={'word/document.xml','word/_rels/document.xml.rels','word/settings.xml','docProps/app.xml','docProps/core.xml'}
    with ZipFile(REFERENCE) as before,ZipFile(output) as after:
        assert after.testzip() is None
        for name in before.namelist():
            if name not in allowed:assert before.read(name)==after.read(name),name
        b=X.fromstring(before.read('word/document.xml'));a=X.fromstring(after.read('word/document.xml'))
        assert [X.tostring(e) for e in b.findall('.//w:sectPr',NS)] == [X.tostring(e) for e in a.findall('.//w:sectPr',NS)]
        source_body=b.find('w:body',NS)
        final_body=a.find('w:body',NS)
        for index in [23,28]:
            assert X.tostring(source_body[index],method='c14n',exclusive=True)==X.tostring(final_body[index],method='c14n',exclusive=True)
        from collections import Counter
        assert Counter(a.xpath('//w:bookmarkStart/@w:id',namespaces=NS))==Counter(a.xpath('//w:bookmarkEnd/@w:id',namespaces=NS))
        names=set(a.xpath('//w:bookmarkStart/@w:name',namespaces=NS))
        assert all(anchor in names for anchor in a.xpath('//w:hyperlink/@w:anchor',namespaces=NS))
    locators={'headings':headings,'figures':figures,'tables':tables,'reference_sha256':manifest['sha256'],'content_fingerprint':content_fingerprint}
    output.with_suffix('.locators.json').write_text(json.dumps(locators,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Template report:',output,'headings',len(headings),'figures',len(figures),'tables',len(tables))
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'docs/44_NguyenDuyTruong_24150180.docx')
    parser.add_argument('--page-map',type=Path)
    parser.add_argument('--draft',action='store_true',help='Create a private draft before computing page numbers.')
    args=parser.parse_args()
    map_path=args.page_map or ART/'report_page_map.json'
    pages=json.loads(map_path.read_text(encoding='utf-8')) if map_path.exists() and not args.draft else None
    patch_report(args.output,pages)


if __name__=='__main__':main()
