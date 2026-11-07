import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const ROOT=path.resolve(import.meta.dirname,'..','..');
const WORK=path.join(ROOT,'.tools/repair-kaggle-20261107/presentation');
const SKILL='C:/Users/Truong Nguyen/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const RUNTIME='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES ||= RUNTIME+'/node/node_modules';
const {importRuntimeModule}=await import(pathToFileURL(SKILL+'/container_tools/runtime_helpers.mjs').href);
const {Presentation,PresentationFile}=await importRuntimeModule('@oai/artifact-tool');
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs').href);
const ART=path.join(ROOT,'TieuLuan_CuoiKy/real_estate_ai/artifacts/vietnam');
const E=JSON.parse(await fs.readFile(path.join(ART,'evidence.json'),'utf8'));
const M=E.metadata,L=E.linear;
const P=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#172C36',green:'#17664F',copper:'#B47B49',paper:'#F7F8F3',muted:'#586B73',white:'#FFFFFF',line:'#DCE3DB'};
const label={area:'Diện tích',bedroom_count:'Phòng ngủ',bathroom_count:'Phòng tắm',floor_count:'Số tầng',frontage_width:'Mặt tiền',road_width:'Đường trước nhà',province_name:'Thành phố',district_name:'Quận/huyện',ward_name:'Phường/xã',property_type_name:'Loại nhà'};
const fmt=(v,n=0)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:n,minimumFractionDigits:n}).format(v);
const bn=v=>fmt(v/1e9,2), pct=v=>fmt(v*100,1)+'%';
const sources={dataset:M.source.source_url,ols:'https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html',pitfalls:'https://scikit-learn.org/stable/common_pitfalls.html',shap:'https://xgboost.readthedocs.io/en/stable/prediction.html'};
const chartSlides=[],tableSlides=[],allCharts=[];
function text(s,value,x,y,w,h,size=28,color=C.ink,bold=false,align='left'){
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=value;a.text.style={typeface:'Arial',fontSize:size,color,bold,alignment:align,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};return a;
}
function slide(title,subtitle='',dark=false){const s=P.slides.add();s.background.fill=dark?C.ink:C.paper;text(s,title,64,45,1148,100,44,dark?C.white:C.ink,true);if(subtitle)text(s,subtitle,66,150,1145,62,25,dark?'#C6D7D1':C.muted);text(s,String(P.slides.items.length).padStart(2,'0'),1148,677,66,24,17,dark?'#C6D7D1':C.muted,false,'right');return s;}
function foot(s,value){text(s,value,66,627,1125,43,19,C.muted);}
function note(s,body,urls=Object.values(sources)){s.speakerNotes.text=body+'\n\nArtifact: '+ART+'\nRevision nguồn: '+M.source.revision+'\n'+urls.join('\n');}
function stat(s,value,caption,x,y,w=340){text(s,value,x,y,w,89,value.length>8?53:72,C.green,true);text(s,caption,x,y+105,w,88,26,C.muted);}
function chart(s,type,config){const rounded={...config,series:config.series.map(series=>({...series,values:series.values?.map(v=>Number(v.toPrecision(10))),xValues:series.xValues?.map(v=>Number(v.toPrecision(10)))}))};const ch=s.charts.add(type,{chartFill:C.paper,plotAreaFill:C.paper,chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},...rounded});applyPresentationChartFont(ch,{fontFamily:'Arial'});allCharts.push(ch);chartSlides.push(P.slides.items.length);return ch;}
function bar(s,categories,values,x,y,w,h,{horizontal=false,color=C.green,unit='',size=22,format='0.0',show=true,valueAxis={}}={}){
 return chart(s,'bar',{position:{left:x,top:y,width:w,height:h},categories,series:[{name:unit||'Giá trị',values,fill:color}],hasLegend:false,barOptions:{direction:horizontal?'bar':'column',grouping:'clustered',gapWidth:80},xAxis:{textStyle:{fontSize:size,fill:C.muted},tickLabelPosition:horizontal?'low':'nextTo'},yAxis:{title:unit,textStyle:{fontSize:size,fill:C.muted},numberFormatCode:format,majorGridlines:{fill:C.line,width:1},...valueAxis},dataLabels:{showValue:show,position:'outEnd',numberFormatCode:format,textStyle:{fontSize:size,fill:C.ink}}});
}
function table(s,values,x,y,w,h,widths,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});t.borders.assign({fill:C.line,width:1});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?'#E8EDE5':C.paper;cell.text.style={typeface:'Arial',fontSize:size,color:C.ink,bold:r===0,verticalAlignment:'middle',insets:9,wrap:'square'};}
 tableSlides.push(P.slides.items.length);return t;
}

// 1
{
 const s=P.slides.add();s.background.fill=C.ink;
 text(s,'TIỂU LUẬN LẬP TRÌNH PYTHON',68,68,1130,45,26,'#A9CCBB',true);
 text(s,'DỰ ĐOÁN GIÁ NHÀ\nTẠI VIỆT NAM',66,180,1140,185,68,C.white,true);
 text(s,'TP.HCM và Hà Nội\nKaggle Vietnam Housing Dataset 2024',70,415,1090,96,32,'#C6D7D1');
 text(s,'Nguyễn Duy Trường · MSSV 24150180\nNhóm 8 · Tháng 11 năm 2026',70,592,1100,66,24,C.white);
 note(s,'Nguồn chính là Nguyen Tien Nhan trên Kaggle, phiên bản 8. Price theo tỷ VND được nhân 1e9. Giá rao bán chưa phải giá giao dịch đã chốt.');
}
// 2
{
 const s=slide('Nguồn dữ liệu và đơn vị','House Price Prediction Dataset Vietnam 2024 của Nguyen Tien Nhan');
 stat(s,fmt(M.audit.raw_rows),'dòng trong CSV gốc',68,242);stat(s,'12','cột gồm nhãn Price',482,242);stat(s,'× 10⁹','tỷ VND thành VND',884,242,330);
 text(s,'Phiên bản 8 cập nhật ngày 22/09/2024',68,477,1115,65,35,C.green,true);
 foot(s,'Kaggle công bố CC0 Public Domain. Theo tác giả, dữ liệu được thu thập từ batdongsan.vn.');
 note(s,'Nguồn '+M.source.source_url+'\nSHA256 CSV '+M.source.files[0].sha256+'\nKhông có ngày đăng từng tin hoặc cột loại nhà. Ngày cập nhật dataset không thay cho ngày đăng.');
}
// 3
{
 const s=slide('Dữ liệu trong phạm vi nghiên cứu','Chỉ giữ TP.HCM và Hà Nội theo địa chỉ đã chuẩn hóa');
 table(s,[['Bước xử lý','Số tin'],['Toàn bộ CSV',fmt(M.audit.raw_rows)],['Hai thành phố',fmt(M.audit.in_scope_rows)],['Ngoài phạm vi hoặc lỗi địa chỉ',fmt(M.audit.invalid_or_outside_price_scope)],['Dữ liệu giữ lại',fmt(M.audit.accepted_rows)],['Nhóm địa chỉ và diện tích',fmt(M.audit.property_proxy_groups)]],66,228,755,350,[550,205],23);
 text(s,'Giá thực tế giữ lại\n1 đến 11,5 tỷ VND',871,260,335,135,31,C.green,true);
 text(s,'Các dòng cùng khóa\nđược giữ cùng một tập',871,464,335,100,26,C.muted);
 foot(s,'Khóa nhóm không chứa giá. Chưa có ID căn nhà thật để xác minh mọi tin đăng lại.');
 note(s,M.audit.deduplication+'\nGiới hạn nghiên cứu: giá 0,5–200 tỷ, diện tích 15–1000m², đơn giá 5–800 triệu/m².');
}
// 4
{
 const s=slide('Số cột nguồn và số nhóm đầu vào','12 cột gồm nhãn Price và 11 cột dự báo ban đầu');
 text(s,'6 biến số',68,237,510,55,34,C.green,true);
 text(s,'Diện tích\nPhòng ngủ và phòng tắm\nSố tầng\nMặt tiền và đường trước nhà',68,316,535,245,30);
 text(s,'6 nhóm danh mục',680,237,530,55,34,C.copper,true);
 text(s,'Thành phố, quận/huyện, phường/xã\nHướng nhà\nPháp lý\nNội thất',680,316,535,245,28);
 foot(s,'Sau loại hướng ban công và tách Address: 10 cột nguồn tạo thành 12 nhóm đầu vào.');
 note(s,'Phân biệt ba khái niệm: 12 cột CSV gốc bao gồm nhãn, 10 cột nguồn giữ làm predictor, 12 nhóm sau xử lý Address. '+JSON.stringify(M.features));
}
// 5
{
 const s=slide('Sàng lọc các cột trước khi học','Quy tắc thiếu dữ liệu được đo trên train');
 table(s,[['Cột nguồn','Xử lý và lý do'],['Price','Nhãn y theo tỷ VND, không đưa vào X'],['Balcony direction','Loại vì thiếu '+pct(M.audit.training_missing_fraction.balcony_direction)+' trên train'],['Address','Chỉ tách ba nhóm địa bàn, bỏ chuỗi nguyên văn']],66,237,1135,265,[320,815],25);
 text(s,'Nguồn chưa có loại nhà, ngày đăng hoặc tọa độ',68,552,1120,65,31,C.green,true);
 foot(s,'Không tự gán dữ liệu chưa có và không dùng giá/m² quan sát làm feature.');
 note(s,'Ngưỡng loại hướng ban công là trên 80% thiếu ở train. Các biến số khác điền trung vị và thêm cờ thiếu; danh mục thiếu dùng Không rõ.');
}
// 6
{
 const s=slide('Hồi quy tuyến tính để đánh giá feature','OLS học log tự nhiên của giá VND');
 table(s,[['Bước','Cách thực hiện'],['Biến diện tích','Lấy log để mô tả thay đổi theo tỷ lệ'],['Sáu biến số','Điền trung vị, thêm cờ thiếu, chuẩn hóa trên train'],['Sáu nhóm danh mục','One-hot, nhóm tham chiếu và gộp mức hiếm'],['Ma trận OLS đầy đủ',String(L.encoded_column_count)+' cột sau mã hóa']],66,236,1135,325,[340,795],25);
 foot(s,'Tất cả bước tiền xử lý học từ train. Validation dùng chọn biến; test giữ riêng.');
 note(s,L.method+'\nKhông so trực tiếp các hệ số thô khác đơn vị. Hệ số danh mục phụ thuộc nhóm tham chiếu.');
}
// 7
{
 const s=slide('Diện tích quan trọng nhất trong OLS','Độ quan trọng là RMSE log tăng khi bỏ nhóm và fit lại');
 const rows=[...L.importance].reverse();
 bar(s,rows.map(x=>x.label),rows.map(x=>x.delta_rmse_log),66,225,805,380,{horizontal:true,unit:'Mức tăng RMSE log',size:21,format:'0.00',show:false});
 stat(s,'+'+fmt(L.importance[0].delta_rmse_log,4),'khi bỏ diện tích',922,264,290);
 text(s,'Tiếp theo là\nquận/huyện\nvà số tầng',924,465,288,125,29,C.green,true);
 foot(s,'Giá trị gần 0 hoặc âm nghĩa là ít thêm thông tin tuyến tính sau các biến còn lại.');
 note(s,L.importance_method+'\n'+JSON.stringify(L.importance));
}
// 8
{
 const s=slide('Hệ số của các biến số đã chuẩn hóa','So sánh trên cùng đơn vị một độ lệch chuẩn');
 const rows=[...L.numeric_coefficients].sort((a,b)=>Math.abs(a.standardized_log_coefficient)-Math.abs(b.standardized_log_coefficient));
 bar(s,rows.map(x=>x.label),rows.map(x=>x.standardized_log_coefficient),66,235,1135,355,{horizontal:true,unit:'Hệ số log VND',size:23,format:'0.00',show:false});
 foot(s,'Diện tích được lấy log. Hệ số có điều kiện và chưa chứng minh tác động nhân quả.');
 note(s,'Chỉ so hệ số sáu biến số đã chuẩn hóa. Toàn bộ 12 nhóm được xếp hạng bằng bỏ nhóm rồi fit lại. '+JSON.stringify(rows));
}
// 9
{
 const s=slide('Bộ tuyến tính chọn 6 trong 12 nhóm','Bộ nhỏ nhất có sai số trong phạm vi 1% so với bộ tốt nhất');
 chart(s,'line',{position:{left:66,top:240,width:790,height:355},categories:L.subsets.map(x=>String(x.k)),series:[{name:'RMSE log validation',values:L.subsets.map(x=>x.validation.rmse_log),line:{fill:C.green,width:3},marker:{symbol:'circle',size:6,fill:C.green}}],hasLegend:false,xAxis:{title:'Số nhóm biến',textStyle:{fontSize:22}},yAxis:{title:'RMSE log validation',numberFormatCode:'0.00',textStyle:{fontSize:22},min:.23,max:.38,majorUnit:.05}});
 stat(s,'6 / 12','nhóm biến được chọn',918,259,292);
 text(s,fmt(L.selected.validation.rmse_log,4)+'\nRMSE log validation',920,475,290,115,31,C.green,true);
 foot(s,'Thêm nhóm theo thứ hạng độ quan trọng OLS. Tiêu chí chọn không sử dụng test.');
 note(s,L.selection_rule+'\n'+JSON.stringify(L.subsets));
}
// 10
{
 const s=slide('Lý do sử dụng sáu nhóm được chọn','Bằng chứng lựa chọn đến từ sai số validation của OLS');
 table(s,[['Nhóm biến','Thông tin liên quan đến giá'],['Diện tích','Quy mô của tài sản, đứng đầu kiểm tra bỏ biến'],['Quận/huyện','Khác biệt mặt bằng giá theo khu vực'],['Số tầng','Kết cấu và quy mô sử dụng bổ sung'],['Phường/xã','Vị trí chi tiết trong cùng quận/huyện'],['Pháp lý','Danh mục giấy tờ và chất lượng khai báo'],['Đường trước nhà','Khả năng tiếp cận, cần thận trọng vì thiếu nhiều']],66,228,1135,365,[290,845],23);
 foot(s,'Quan hệ dự báo không đồng nghĩa với mức cộng tiền cố định hoặc tác động nhân quả.');
 note(s,'Bộ được chọn '+JSON.stringify(L.selected.features)+'. Pháp lý có mức Không rõ; đường thiếu '+pct(M.audit.training_missing_fraction.road_width)+'. Các biến còn lại có thể chứa tương tác phi tuyến.');
}
// 11
{
 const s=slide('OLS chọn biến và XGBoost phục vụ','Hai mô hình dùng cùng dữ liệu nhưng có cấu trúc khác nhau');
 text(s,'OLS dùng 6 nhóm',68,245,530,65,36,C.green,true);
 text(s,'Giải thích hệ số và chọn\nthông tin tuyến tính\n\nRMSE validation '+bn(L.selected.validation.rmse_vnd)+' tỷ',68,338,530,240,29);
 text(s,'XGBoost dùng 12 nhóm',680,245,535,65,36,C.copper,true);
 text(s,'Học quan hệ phi tuyến\nvà tương tác giữa thuộc tính\n\nRMSE validation '+bn(M.validation_comparison[2].rmse_vnd)+' tỷ',680,338,535,240,29);
 foot(s,'Chưa so XGBoost sáu nhóm với XGBoost 12 nhóm; không suy rộng kết luận chọn biến OLS.');
 note(s,'Ứng dụng đang phục vụ '+M.selected_model+'. Bộ OLS gọn chỉ là kết quả lựa chọn cho mô hình tuyến tính.');
}
// 12
{
 const s=slide('Diện tích và giá rao bán','Mỗi thành phố lấy mẫu cố định 1.200 tin từ train');
 const series=E.area_scatter.map((g,i)=>({name:g.city,xValues:g.x,values:g.y,marker:{symbol:'circle',size:4,fill:i?C.copper:C.green},line:{fill:'none',width:0}}));
 chart(s,'scatter',{position:{left:66,top:228,width:1135,height:365},series,hasLegend:true,legend:{position:'right',textStyle:{fontSize:22}},scatterOptions:{style:'marker'},xAxis:{title:'Diện tích khai báo m²',textStyle:{fontSize:22},numberFormatCode:'0',min:0,max:600,majorUnit:200},yAxis:{title:'Giá rao tỷ VND',textStyle:{fontSize:22},numberFormatCode:'0',min:0,max:12,majorUnit:2}});
 foot(s,'Cùng mẫu điểm với Word. Slide dùng thang tuyến tính; hình trong Word dùng thang log.');
 note(s,'Mẫu mô tả chỉ lấy từ train. Cùng diện tích có nhiều mức giá; địa bàn và kết cấu bổ sung thông tin. Không có nhãn loại nhà trong nguồn.');
}
// 13
{
 const s=slide('Phòng ngủ và phòng tắm','Giá rao trung vị, mỗi nhóm có ít nhất 50 tin train');
 for(const [i,feature] of ['bedroom_count','bathroom_count'].entries()){
  const groups=E.rooms[feature];
  text(s,label[feature],68+i*612,218,535,45,29,i?C.copper:C.green,true);
  chart(s,'line',{position:{left:66+i*612,top:278,width:535,height:307},categories:groups[0].categories,series:groups.map((x,j)=>({name:x.city,values:x.median_billion,line:{fill:j?C.copper:C.green,width:3},marker:{symbol:'circle',size:6,fill:j?C.copper:C.green}})),hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:19}},xAxis:{title:'Số phòng',textStyle:{fontSize:21}},yAxis:{title:'Tỷ VND',textStyle:{fontSize:21},numberFormatCode:'0'}});
 }
 foot(s,'Diện tích và địa bàn cùng thay đổi giữa các nhóm; không suy ra mức cộng tiền cố định.');
 note(s,JSON.stringify(E.rooms)+'\nNguồn không có cột loại nhà; biểu đồ gộp bất động sản trong phạm vi.');
}
// 14
{
 const s=slide('Vị trí và đơn giá rao bán','Các quận/huyện có ít nhất 100 tin train');
 E.districts.forEach((row,i)=>{
  text(s,row.city,68+i*612,218,535,45,29,i?C.copper:C.green,true);
  bar(s,row.categories,row.median_million,66+i*612,278,535,307,{horizontal:true,unit:'Triệu VND/m²',size:20,color:i?C.copper:C.green,show:false,format:'0',valueAxis:{min:0,max:200,majorUnit:50}});
 });
 foot(s,'Đơn giá mô tả bằng giá rao chia diện tích khai báo. Đây chưa phải bảng giá thị trường hiện tại.');
 note(s,'Bảy khu vực có đơn giá trung vị cao nhất trong phần đủ mẫu của mỗi thành phố. Cùng số liệu với Word. '+JSON.stringify(E.districts));
}
// 15
{
 const s=slide('Các thông tin còn thiếu trong nguồn','Không có ngày đăng, cột loại nhà hoặc tọa độ được xác minh');
 text(s,'Chia theo nhóm địa chỉ và diện tích',68,247,1120,70,37,C.green,true);
 text(s,'Giữ các tin cùng khóa trong cùng một tập\nđể hạn chế tin đăng lại xuất hiện giữa train và test',68,360,1120,115,31);
 text(s,'Chưa kiểm định dự báo ở thời kỳ tương lai',68,540,1120,70,32,C.copper,true);
 note(s,'Không tạo nhãn loại nhà từ tên dự án, không bịa ngày đăng hoặc khoảng cách trường học/cửa hàng. Các tập có 60/15/10/15% nhóm xấp xỉ. '+M.split_method);
}
// 16
{
 const s=slide('So sánh mô hình trên validation','Cùng train và validation theo nhóm địa chỉ và diện tích');
 const rows=M.validation_comparison;
 bar(s,['Trung vị khu vực','XGB chưa địa bàn','XGB thêm địa bàn'],rows.map(x=>x.rmse_vnd/1e9),66,235,790,350,{unit:'RMSE tỷ VND',size:23,format:'0.00'});
 text(s,'− '+fmt((1-rows[2].rmse_vnd/rows[1].rmse_vnd)*100,1)+'%',912,265,300,85,57,C.green,true);
 text(s,'RMSE khi thêm\nthông tin địa bàn',912,370,300,95,28,C.muted);
 text(s,'OLS 12 nhóm '+bn(L.full_validation.rmse_vnd)+' tỷ\nOLS 6 nhóm '+bn(L.selected.validation.rmse_vnd)+' tỷ',912,510,300,90,23);
 foot(s,'Sau chọn cấu hình, fit lại train và validation. Calibration và test được giữ riêng.');
 note(s,JSON.stringify(rows)+'\nBaseline dùng trung vị đơn giá theo thành phố và quận/huyện, chỉ học từ train.');
}
// 17
{
 const s=slide('Kết quả trên '+fmt(M.test.n)+' tin test','Các nhóm tin chưa dùng fit mô hình hoặc chọn biến');
 stat(s,fmt(M.test.r2,3),'R² theo VND',68,244);stat(s,pct(M.test.median_ape),'sai lệch tuyệt đối\ntrung vị',482,244);stat(s,pct(M.test.within_20pct),'sai lệch không quá ±20%',884,244,330);
 text(s,'MAE '+bn(M.test.mae_vnd)+' tỷ VND   ·   RMSE '+bn(M.test.rmse_vnd)+' tỷ VND',68,504,1120,65,34,C.green,true);
 foot(s,'R² không phải tỷ lệ dự đoán đúng. Kết quả áp dụng cho phạm vi giá và dữ liệu đã lọc.');
 note(s,JSON.stringify(M.test)+'\nBaseline test '+JSON.stringify(M.baseline_test));
}
// 18
{
 const s=slide('Sai số và độ phủ theo thành phố','Khoảng 90% danh nghĩa có độ phủ chung '+pct(M.test.coverage_90));
 const rows=M.test_breakdown;
 table(s,[['Thành phố','Số tin test','R²','MdAPE','Độ phủ'],...rows.map(x=>[x.label,fmt(x.n),fmt(x.r2,3),pct(x.median_ape),pct(x.coverage_90)])],66,242,1135,190,[310,200,160,220,245],25);
 text(s,'Độ phủ quan sát khác nhau giữa hai thành phố',68,478,1120,65,35,C.green,true);
 text(s,'Bề rộng khoảng trung vị '+bn(M.test.median_interval_width_vnd)+' tỷ VND',68,559,1120,55,28,C.muted);
 foot(s,'Hiệu chỉnh bằng calibration; không bảo đảm mức phủ cho mọi phân khúc hoặc thời kỳ mới.');
 note(s,JSON.stringify(rows)+'\nKhoảng tính từ phân vị phần dư tuyệt đối log giá. Các tin trong cùng nhóm có thể phụ thuộc nhau.');
}
// 19
{
 const s=slide('Ví dụ dự đoán tại TP.HCM','Tin test có giá nguồn trung vị trong nhóm khai báo đủ số phòng');
 const x=E.main_example.input,r=E.main_example.result,v=x.input;
 table(s,[['Thuộc tính','Thông tin'],['Vị trí',v.district_name+' · '+v.ward_name],['Diện tích',fmt(v.area)+' m²'],['Phòng ngủ / phòng tắm',fmt(v.bedroom_count)+' / '+fmt(v.bathroom_count)],['Số tầng',fmt(v.floor_count)],['Giá rao nguồn',bn(x.asking_vnd)+' tỷ VND']],66,232,670,350,[280,390],23);
 stat(s,bn(r.predicted_vnd)+' tỷ','giá rao dự đoán',820,245,390);
 text(s,fmt(r.price_per_m2_vnd/1e6,1)+' triệu/m²\n\nKhoảng danh nghĩa 90%\n'+r.interval_90_vnd.map(v=>bn(v)+' tỷ').join(' – '),822,452,390,160,26);
 foot(s,'Giá rao trong dataset 2024. Nguồn không có ngày đăng từng tin hoặc giá chốt giao dịch.');
 note(s,JSON.stringify(E.main_example)+'\nQuy tắc chọn ví dụ không dựa vào sai số dự đoán.');
}
// 20
{
 const r=E.main_example.result;
 const s=slide('Giải thích mức giá dự đoán','TreeSHAP phân rã dự đoán trên thang log VND');
 const rows=r.explanations.slice(0,8).reverse();
 chart(s,'bar',{position:{left:66,top:235,width:1135,height:355},categories:rows.map(x=>x.label),series:[{name:'Đóng góp log VND',values:rows.map(x=>x.log_contribution),fill:C.green,points:rows.map((x,idx)=>({idx,fill:x.log_contribution>=0?C.green:C.copper}))}],hasLegend:false,barOptions:{direction:'bar',gapWidth:70},xAxis:{textStyle:{fontSize:22},tickLabelPosition:'low'},yAxis:{title:'Đóng góp log VND',textStyle:{fontSize:22},numberFormatCode:'0.00',majorGridlines:{fill:C.line,width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{fontSize:22}}});
 foot(s,'Cộng với mức nền trên log giá rồi lấy hàm mũ; không cộng từng thanh trực tiếp thành VND.');
 note(s,JSON.stringify(r.explanations)+'\nTreeSHAP giải thích XGBoost, khác phép bỏ biến rồi fit lại OLS. Chưa chứng minh quan hệ nhân quả.');
}
// 21
{
 const caseHN=E.examples.find(x=>x.input.input.province_name==='Hà Nội');
 const x=caseHN.input,r=caseHN.result,v=x.input;
 const s=slide('Ví dụ đối chiếu tại Hà Nội',v.district_name+' · '+fmt(v.area)+' m² · '+fmt(v.bedroom_count)+' phòng ngủ / '+fmt(v.bathroom_count)+' phòng tắm');
 stat(s,bn(x.asking_vnd)+' tỷ','giá rao nguồn',68,245);stat(s,bn(r.predicted_vnd)+' tỷ','giá dự đoán',482,245);stat(s,fmt(r.price_per_m2_vnd/1e6,1),'triệu VND / m²',884,245,330);
 text(s,'Khoảng 90%: '+r.interval_90_vnd.map(v=>bn(v)+' tỷ VND').join(' đến '),68,493,1120,70,33,C.green,true);
 foot(s,'Cùng ví dụ và số liệu với Word. Giá dự đoán không được dùng làm nhãn huấn luyện.');
 note(s,JSON.stringify(caseHN));
}
// 22
{
 const r=E.main_example.result;
 const s=slide('Đơn giá và tin rao đối chiếu','Đơn giá dự đoán bằng tổng giá dự đoán chia diện tích khai báo');
 table(s,[['Quận/huyện','Phường/xã','Diện tích m²','Giá rao tỷ'],...r.comparables.slice(0,5).map(x=>[x.district_name,x.ward_name,fmt(x.area,1),bn(x.price)])],66,235,1135,320,[220,450,230,235],23);
 text(s,'Cùng quận/huyện, lấy từ train và validation',68,577,1120,45,28,C.green,true);
 foot(s,'Nguồn không có ngày đăng hoặc loại nhà; thiếu tọa độ nên không khẳng định gần nhất.');
 note(s,JSON.stringify(r.comparables)+'\nDanh sách chỉ hỗ trợ đối chiếu, không phải công thức trung bình tính giá của XGBoost.');
}
// 23
{
 const s=slide('Ứng dụng và cách chạy','Mở file chay_ui.cmd trong thư mục TieuLuan_CuoiKy');
 text(s,'TieuLuan_CuoiKy\\chay_ui.cmd',68,240,1120,65,37,C.green,true);
 text(s,'Mặc định http://127.0.0.1:8000',68,330,1120,65,34);
 table(s,[['Dữ liệu','Vai trò'],['vietnam_2024_listings','Giá rao quan sát từ Kaggle 2024'],['vietnam_predictions','Đầu vào, dự đoán và phiên bản model'],['Kiểm thử cục bộ','100 bài đạt · 1 bài PostgreSQL bỏ qua']],66,433,1135,165,[370,765],22);
 foot(s,'Launcher kiểm tra model, dùng lại phiên khớp hoặc chọn cổng trống khi có phiên cũ.');
 note(s,'API /api/vietnam/info, /predict và /history. Dùng SQLite mặc định. Giữ nguyên dữ liệu cũ; không lấy giá dự đoán làm nhãn. Docker image chưa được phát hành mới.');
}
// 24
{
 const s=slide('Giới hạn và hướng phát triển','Kết quả phụ thuộc chất lượng và phạm vi dữ liệu',true);
 text(s,'Dataset Kaggle 2024, giá giữ lại 1–11,5 tỷ VND',68,245,1120,85,36,C.white,true);
 text(s,'Thiếu ID nhà thật, ngày đăng, loại nhà và tọa độ',68,368,1120,75,31,'#C6D7D1');
 text(s,'Chia theo nhóm chưa chứng minh dự báo theo thời gian',68,470,1120,75,31,'#C6D7D1');
 text(s,'Cần giao dịch xác minh và đánh giá trên thời kỳ mới',68,574,1120,65,31,'#A9CCBB',true);
 note(s,M.limitations.join('\n')+'\n'+L.caveats.join('\n'));
}

for(const ch of allCharts)applyPresentationChartFont(ch,{fontFamily:'Arial'});
await fs.mkdir(WORK+'/preview',{recursive:true});await fs.mkdir(WORK+'/staging',{recursive:true});await fs.mkdir(WORK+'/output',{recursive:true});
const candidate=WORK+'/staging/candidate.pptx';await(await PresentationFile.exportPptx(P)).save(candidate);console.log('Created draft',P.slides.items.length,'slides');
for(let i=0;i<P.slides.items.length;i++){const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(WORK+'/preview/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await blob.arrayBuffer()));console.log('Rendered',i+1);}
const revision=String(Date.now());
const finalPath=WORK+'/output/Gia_nha_Viet_Nam_'+revision+'.pptx';
const result=await finalizePresentation({workspaceDir:WORK,candidatePath:candidate,finalPath,pythonExecutable:RUNTIME+'/python/python.exe',
 integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[...new Set(tableSlides)].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:24,
 requiredNativeChartOwnerSlides:[...new Set(chartSlides)],requiredNativeTableOwnerSlides:[...new Set(tableSlides)],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:WORK+'/staging/validation-'+revision+'.json'});
console.log(JSON.stringify({finalPath:result.finalPath,sha256:result.finalSha256,integrity:result.packageIntegrity?.status,layoutFindings:result.presentationLayout?.findingCount,nativeCharts:result.nativeChartValidation?.passed}));
await fs.copyFile(finalPath,path.join(ROOT,'TieuLuan_CuoiKy/docs/Thuyet_trinh_TieuLuan_CuoiKy.pptx'));
console.log('Final deck delivered');
