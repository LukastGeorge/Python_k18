import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const ROOT=path.resolve(import.meta.dirname,'..','..');
const WORK=path.join(ROOT,'.tools/kingcounty-20261107/presentation');
const SKILL='C:/Users/Truong Nguyen/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const {importRuntimeModule}=await import(pathToFileURL(SKILL+'/container_tools/runtime_helpers.mjs').href);
const {Presentation,PresentationFile}=await importRuntimeModule('@oai/artifact-tool');
const PY='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1030-493-0_26.1030.493.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe';
const DATA=path.join(ROOT,'TieuLuan_CuoiKy/real_estate_ai/artifacts/kingcounty');
const E=JSON.parse(await fs.readFile(path.join(DATA,'evidence.json'),'utf8'));
const M=E.metadata, X=E.example, R=X.result;
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(SKILL+'/container_tools/artifact_tool_utils.mjs').href);
const P=Presentation.create({slideSize:{width:1280,height:720}});
const C={ink:'#172C36',green:'#17664F',copper:'#B47B49',paper:'#F7F8F3',muted:'#586B73',white:'#FFFFFF',line:'#DCE3DB'};
const fmt=(v,n=0)=>new Intl.NumberFormat('vi-VN',{maximumFractionDigits:n,minimumFractionDigits:n}).format(v);
const bn=v=>fmt(v/1e9,2), pct=v=>fmt(v*100,1)+'%';
const sources={dataset:'https://www.kaggle.com/datasets/harlfoxem/housesalesprediction',dictionary:'https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/',fx:'https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-tien-ich/Ty-gia',cv:'https://scikit-learn.org/stable/modules/cross_validation.html',shap:'https://xgboost.readthedocs.io/en/stable/prediction.html',osm:'https://www.openstreetmap.org/copyright'};
const chartSlides=[],tableSlides=[],allCharts=[];
function text(s,value,x,y,w,h,size=28,color=C.ink,bold=false,align='left'){
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 a.text=value;a.text.style={typeface:'Arial',fontSize:size,color,bold,alignment:align,verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};return a;
}
function slide(title,subtitle='',dark=false){const s=P.slides.add();s.background.fill=dark?C.ink:C.paper;text(s,title,64,44,1148,105,42,dark?C.white:C.ink,true);if(subtitle)text(s,subtitle,66,145,1145,60,24,dark?'#C6D7D1':C.muted);text(s,String(P.slides.items.length).padStart(2,'0'),1148,674,66,25,17,dark?'#C6D7D1':C.muted,false,'right');return s;}
function note(s,body,urls=[]){s.speakerNotes.text=body+'\n\nNguồn dữ liệu: '+DATA+'\n'+urls.join('\n');}
function foot(s,value){text(s,value,66,626,1130,44,18,C.muted);}
function stat(s,value,label,x,y,w=340,dark=false){text(s,value,x,y,w,94,value.length>8?49:68,dark?C.white:C.green,true);text(s,label,x,y+105,w,75,25,dark?'#C6D7D1':C.muted);}
function chart(s,type,config){const rounded={...config,series:config.series.map(series=>({...series,values:series.values?.map(v=>v===null?v:Number(v.toPrecision(10))),xValues:series.xValues?.map(v=>v===null?v:Number(v.toPrecision(10)))}))};const ch=s.charts.add(type,{chartFill:C.paper,plotAreaFill:C.paper,chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},...rounded});applyPresentationChartFont(ch,{fontFamily:'Arial'});allCharts.push(ch);chartSlides.push(P.slides.items.length);return ch;}
function bar(s,categories,values,x,y,w,h,{horizontal=false,color=C.green,unit='',size=21}={}){
 return chart(s,'bar',{position:{left:x,top:y,width:w,height:h},categories,series:[{name:unit||'Giá trị',values,fill:color}],hasLegend:false,
 barOptions:{direction:horizontal?'bar':'column',grouping:'clustered',gapWidth:80},
 xAxis:{title:horizontal?unit:undefined,textStyle:{fontSize:size,fill:C.muted}},yAxis:{title:horizontal?undefined:unit,textStyle:{fontSize:size,fill:C.muted},numberFormatCode:'0.0',majorGridlines:{fill:C.line,width:1}},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{fontSize:size,fill:C.ink}}});}
function table(s,values,x,y,w,h,widths){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});
 t.borders.assign({fill:C.line,width:1});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const cell=t.getCell(r,c);cell.fill=r===0?'#E8EDE5':C.paper;
  cell.text.style={typeface:'Arial',fontSize:21,color:C.ink,bold:r===0,verticalAlignment:'middle',insets:10,wrap:'square'};
 }
 tableSlides.push(P.slides.items.length);return t;
}
// 1
{
 const s=P.slides.add();s.background.fill=C.ink;
 text(s,'PHÂN TÍCH DỮ LIỆU GIÁ NHÀ',68,65,1120,45,24,'#A9CCBB',true);
 text(s,'GIÁ NHÀ VÀ\nNHỮNG YẾU TỐ LIÊN QUAN',66,173,1145,185,58,C.white,true);
 text(s,'King County, Washington, USA\nGiao dịch 2014–2015 · Hiển thị VND quy đổi',70,395,1090,92,30,'#C6D7D1');
 text(s,'Nguyễn Duy Trường · MSSV 24150180\nNhóm 8 · Tháng 11 năm 2026',70,588,1100,70,23,C.white);
 note(s,'Báo cáo phân tích dataset King County và mô hình định giá theo bối cảnh lịch sử. Tiền VND là phép quy đổi đơn vị của nhà tại Mỹ. Phần mềm không tuyên bố định giá nhà Việt Nam hoặc thị trường hiện tại.',[sources.dataset,sources.dictionary]);
}
// 2
{
 const s=slide('Phạm vi bài toán','Dự đoán giá giao dịch của một căn nhà tại King County');
 stat(s,fmt(M.audit.raw_rows),'giao dịch gốc',68,245);stat(s,fmt(M.audit.accepted_rows),'giao dịch hợp lệ',482,245);stat(s,'2014–2015','thời kỳ giao dịch',884,245,335);
 text(s,'Mô hình học giá USD, sau đó quy đổi kết quả sang VND',68,480,1130,70,31,C.green,true);
 foot(s,'Tỷ giá '+fmt(E.exchange_rate)+' VND/USD từ snapshot Vietcombank. Không điều chỉnh giá nhà sang năm 2026.');
 note(s,'Giá gốc gắn với ngày giao dịch năm 2014–2015. Mô hình học log(1 + USD). Nhân dự đoán với tỷ giá cố định để hiển thị VND; thay đổi tỷ giá không cải thiện R² hay sai số phần trăm. Snapshot XML và checksum được lưu để tái lập.',[sources.dataset,sources.fx]);
}
// 3
{
 const s=slide('Chất lượng dữ liệu','Các quy tắc làm sạch được kiểm tra trước khi huấn luyện');
 table(s,[['Kiểm tra','Kết quả'],['Giao dịch gốc',fmt(M.audit.raw_rows)],['Bản ghi trùng hoàn toàn',fmt(M.audit.exact_duplicates)],['Ngoài quy tắc hợp lệ',fmt(M.audit.invalid_rows)],['Giữ lại',fmt(M.audit.accepted_rows)],['Mã nhà riêng biệt',fmt(M.audit.unique_houses)]],66,223,720,345,[490,230]);
 text(s,'Mã nhà và ngày bán\nphân biệt từng giao dịch',850,245,350,90,29,C.green,true);
 text(s,'Không sửa 33 phòng thành 3\nKhông điền nhãn giá giả\nKhông đưa giá/m² vào đầu vào',850,375,350,160,25,C.ink);
 foot(s,'Loại trường hợp phòng tắm không hợp lệ, năm xây/cải tạo sau ngày bán hoặc số phòng bất thường.');
 note(s,'Quy tắc đầy đủ nằm trong prepare_sales và audit có danh sách mã bị loại. Việc loại bỏ 29 dòng là giới hạn của nghiên cứu, cần đối soát nguồn trước khi kết luận lỗi dữ liệu thực. Chuẩn hóa ft² sang m² bằng hệ số 0,09290304.',[sources.dataset,sources.dictionary]);
}
// 4
{
 const s=slide('Diện tích ở và giá bán','1.500 giao dịch lấy mẫu cố định từ tập train');
 chart(s,'scatter',{position:{left:66,top:220,width:790,height:367},series:[{name:'Giao dịch train',xValues:E.area_scatter.x.slice(0,700),values:E.area_scatter.y.slice(0,700),marker:{symbol:'circle',size:3,fill:C.green},line:{fill:'none',width:0}}],hasLegend:false,scatterOptions:{style:'marker'},xAxis:{title:'Diện tích ở (m²)',textStyle:{fontSize:20},numberFormatCode:'0'},yAxis:{title:'Giá (tỷ VND)',textStyle:{fontSize:20},numberFormatCode:'0'}});
 stat(s,fmt(E.correlations.living_m2,3),'tương quan Pearson\ndiện tích ở và giá',902,251,300);
 text(s,'Cùng diện tích\nvẫn khác giá',904,470,300,100,29,C.green,true);
 foot(s,'Biểu đồ slide hiển thị 700 điểm đầu của mẫu. Quan hệ quan sát không phải bằng chứng nhân quả.');
 note(s,'Mẫu cố định được lấy bằng seed 42. Biểu đồ thưa hơn bản báo cáo để giữ độ đọc trên màn chiếu. Các căn cùng diện tích có giá phân tán do vị trí, chất lượng và những yếu tố chưa quan sát.',[sources.dataset]);
}
// 5
{
 const s=slide('Phòng ngủ và phòng tắm','Giá trung vị theo nhóm, chỉ giữ nhóm có ít nhất 50 giao dịch train');
 text(s,'Phòng ngủ',68,218,540,40,27,C.green,true);text(s,'Phòng tắm quy đổi',690,218,520,40,27,C.copper,true);
 bar(s,E.rooms.bedrooms.categories,E.rooms.bedrooms.median_billion_vnd,66,270,540,307,{unit:'Tỷ VND',size:20});
 const bathChart=bar(s,E.rooms.bathrooms.categories,E.rooms.bathrooms.median_billion_vnd,682,270,540,307,{unit:'Tỷ VND',color:C.copper,size:18});bathChart.dataLabels={showValue:false};
 foot(s,'Chênh lệch giữa các nhóm còn liên quan đến diện tích, chất lượng và vị trí. Không suy ra giá cộng thêm cho mỗi phòng.');
 note(s,'Giá trung vị của các nhóm phòng là thống kê mô tả trên tập train. Một phòng tắm đầy đủ bằng 1, ba phần tư bằng 0,75 và nửa phòng bằng 0,5. Số mẫu cho từng nhóm được lưu trong evidence.json.',[sources.dictionary]);
}
// 6
{
 const s=slide('Chất lượng xây dựng và cảnh quan','Những biến môi trường đã có trực tiếp trong dataset');
 text(s,'Chất lượng xây dựng',68,218,550,40,27,C.green,true);text(s,'Điểm cảnh quan',690,218,520,40,27,C.copper,true);
 bar(s,E.quality.grade.categories,E.quality.grade.values,66,270,545,307,{unit:'Tỷ VND',size:19});
 bar(s,E.quality.view.categories,E.quality.view.values,685,270,530,307,{unit:'Tỷ VND',color:C.copper,size:20});
 foot(s,'Grade phản ánh vật liệu và chất lượng thi công. View là điểm cảnh quan 0–4 theo hồ sơ nguồn.');
 note(s,'Các nhóm có ít nhất 20 giao dịch. Grade và view là thuộc tính có trong dữ liệu, khác với các tiện ích chưa có cột đo. Không quy chênh lệch giá giữa nhóm thành mức tăng giá nhân quả.',[sources.dictionary]);
}
// 7
{
 const s=slide('Mặt bằng giá theo vị trí','Các giao dịch cùng quận vẫn thuộc những khu vực giá khác nhau');
 const index=E.location.price_usd.map((p,i)=>[p,i]).sort((a,b)=>a[0]-b[0]);
 const groups=[index.slice(0,500),index.slice(500,1000),index.slice(1000)];
 chart(s,'scatter',{position:{left:66,top:225,width:790,height:370},hasLegend:true,legend:{position:'bottom',textStyle:{fontSize:18}},series:groups.map((g,i)=>({name:['Nhóm giá thấp','Nhóm giá giữa','Nhóm giá cao'][i],xValues:g.slice(0,230).map(v=>E.location.x[v[1]]),values:g.slice(0,230).map(v=>E.location.y[v[1]]),marker:{symbol:'circle',size:3,fill:[C.copper,'#8FAE9A',C.green][i]},line:{fill:'none',width:0}})),scatterOptions:{style:'marker'},xAxis:{min:-122.6,max:-121.2,title:'Kinh độ',textStyle:{fontSize:18},numberFormatCode:'0.0'},yAxis:{min:47.1,max:47.85,title:'Vĩ độ',textStyle:{fontSize:18},numberFormatCode:'0.0'}});
 text(s,'Vị trí được giữ\ntrong mô hình',900,265,305,130,29,C.green,true);
 text(s,'Vị trí không tự cho biết\ntrường học gần nhất\nhay khoảng cách cửa hàng',900,450,305,125,24,C.muted);
 note(s,'Biểu đồ tọa độ không phải bản đồ hành chính. Ba nhóm giá được tạo trên mẫu train với số điểm tương đương. Không sử dụng nền bản đồ hay giả định đường đi. Giá phân nhóm để tăng độ đọc, không là đầu vào mô hình.',[sources.dataset]);
}
// 8
{
 const s=slide('Dữ liệu trường học và cửa hàng','Giới hạn cần công bố trước khi giải thích giá bằng tiện ích');
 table(s,[['Thông tin','Tình trạng'],['Có cột trong King County gốc','Không'],['Snapshot OSM lịch sử đã xác minh',M.poi_available?'Có':'Chưa lấy được'],['Khoảng cách dùng trong mô hình',R.amenities_used_by_model?'Có':'Không'],['Khoảng cách do suy đoán hoặc điền giả','Không sử dụng']],66,240,1135,270,[640,495]);
 text(s,'Chưa đủ bằng chứng để quy giá cao\ncho việc gần trường hay cửa hàng',68,548,1130,80,30,C.green,true);
 note(s,'Đã thử các máy chủ Overpass, ohsome và tệp NCES 2013–2014. Máy chủ Overpass và NCES hết thời gian chờ, dịch vụ trích xuất ohsome trả 403. Không có địa điểm hay khoảng cách nào được tự điền. Adapter OSM lịch sử được chuẩn bị trong source để chạy khi có nguồn truy cập được. Khi bổ sung cần kiểm tra thời điểm, giấy phép, độ phủ và thử mô hình trên validation. Khoảng cách đường chim bay không xác định quyền tuyển sinh.',[sources.osm,'https://docs.ohsome.org/ohsome-api/v2/']);
}
// 9
{
 const s=slide('Chia dữ liệu theo thời gian','Bốn tập không có mã căn nhà chung');
 table(s,[['Tập','Giai đoạn','Số giao dịch'],['Train','05–10/2014',fmt(M.splits.train.rows)],['Validation','11–12/2014',fmt(M.splits.validation.rows)],['Hiệu chỉnh khoảng','01–02/2015',fmt(M.splits.calibration.rows)],['Test','03–05/2015',fmt(M.splits.test.rows)]],66,230,1135,310,[385,410,340]);
 foot(s,'Loại '+fmt(M.purged_rows)+' giao dịch cũ của căn thuộc tập phía sau. Mô hình phục vụ chỉ fit train + validation.');
 note(s,'Tập validation chọn cấu hình. Tập calibration chỉ xác định phân vị sai số cho khoảng dự đoán. Tập test báo cáo đánh giá cuối. Không refit mô hình phục vụ bằng calibration hay test, vì cần giữ đúng chất lượng đã được kiểm chứng. Không so trực tiếp R² mới với 0,815 của phép chia nhóm ngẫu nhiên cũ.',[sources.cv]);
}
// 10
{
 const s=slide('So sánh mô hình trên validation','Cùng tập dữ liệu và cùng thước đo RMSE, thấp hơn tốt hơn');
 const labels=E.validation.categories.map(v=>v.replace('XGBoost ','XGB '));
 bar(s,labels,[...E.validation.rmse_usd].map(v=>v/1000),66,240,820,340,{horizontal:true,unit:'Nghìn USD',size:21});
 stat(s,fmt(M.validation_metrics.rmse_usd/1000,1),'nghìn USD RMSE\nmô hình được chọn',935,260,280);
 foot(s,'Bổ sung phòng tắm, chất lượng, tuổi nhà và mã bưu chính được kiểm chứng bằng validation.');
 note(s,'Ứng viên gồm median, Ridge bốn biến, XGBoost bốn biến và XGBoost với nhà và vị trí. Các hyperparameter được cố định trước thí nghiệm. Nghiên cứu hiện chưa có snapshot tiện ích hợp lệ nên không chạy ứng viên tiện ích. Chỉ RMSE validation quyết định lựa chọn.',[sources.cv]);
}
// 11
{
 const s=slide('Kết quả trên giao dịch ở giai đoạn sau',fmt(M.splits.test.rows)+' giao dịch test từ tháng 3 đến tháng 5 năm 2015');
 stat(s,fmt(M.test_metrics.r2,3),'R²',66,250);stat(s,fmt(M.test_metrics.mae_usd/1000,1),'nghìn USD MAE',480,250);stat(s,pct(M.test_metrics.within_20pct),'sai lệch không quá ±20%',883,250,330);
 text(s,'MAE quy đổi '+bn(M.test_metrics.mae_usd*E.exchange_rate)+' tỷ VND',68,489,1130,55,34,C.green,true);
 foot(s,'R² không phải tỷ lệ dự đoán đúng. Các chỉ số này không chứng minh chất lượng ở thị trường năm 2026.');
 note(s,'MAE là sai số tuyệt đối trung bình. RMSE bằng '+M.test_metrics.rmse_usd+' USD. Tỷ lệ ±10% là '+pct(M.test_metrics.within_10pct)+'. Các sai số quy đổi đều dùng cùng tỷ giá snapshot. Thời gian test sau train giúp đánh giá tốt hơn tình huống giao dịch mới hơn, trong phạm vi dữ liệu 13 tháng.',[sources.cv]);
}
// 12
{
 const s=slide('Sai số thay đổi theo phân khúc giá','Đánh giá chi tiết giúp nhận diện nhóm nhà khó dự đoán');
 const segmentChart=bar(s,['Dưới 300','300–700','Từ 700'],E.segments.map(v=>v.mae_usd/1000),66,240,770,325,{unit:'MAE nghìn USD',size:20});segmentChart.xAxis={title:'Nhóm giá thật (nghìn USD)',textStyle:{fontSize:20}};
 text(s,'Nhà giá cao còn có\nsai số tuyệt đối lớn',895,260,315,110,31,C.green,true);
 text(s,'Báo cáo cả MAE\nvà tỷ lệ sai số phần trăm\ncho từng nhóm',895,425,315,130,25,C.muted);
 foot(s,'Phân nhóm theo giá thật, dùng để mô tả sai số test. Không dùng kết quả này để chọn lại mô hình.');
 note(s,JSON.stringify(E.segments)+'\nCác nhóm ít mẫu hoặc có nhà rất đặc biệt có thể làm trung bình sai số không ổn định. Khi mở rộng thí nghiệm, cần phép chia test mới nếu thay đổi mô hình dựa trên phân tích sai số này.',[sources.cv]);
}
// 13
{
 const s=slide('Khoảng dự đoán và độ bất định','Hiệu chỉnh sai số trên tập riêng trước khi mở test');
 stat(s,'90%','độ phủ danh nghĩa',68,250);stat(s,pct(M.test_metrics.interval_coverage),'độ phủ thực tế trên test',500,250,420);
 text(s,'Căn khó dự đoán\ncó khoảng rộng',937,265,275,140,30,C.green,true);
 text(s,'Bề rộng khoảng trung vị trên test: '+bn(M.test_metrics.median_interval_width_usd*E.exchange_rate)+' tỷ VND',68,510,1130,70,29,C.ink,true);
 foot(s,'Độ phủ theo thời gian không được bảo đảm khi thị trường thay đổi. Cần kiểm tra lại trên dữ liệu mới.');
 note(s,'Dùng split conformal trên sai số tuyệt đối của log(1 + USD). Chọn phân vị cao hơn với điều chỉnh hữu hạn mẫu ceil((n+1)*0,9)/n. Giả định ổn định phân phối có thể không đúng theo thời gian, vì vậy báo cáo cả độ phủ thực tế và bề rộng. Khoảng dự đoán nói về giá quan sát của căn mới, khác với khoảng tin cậy của giá trung bình.',['https://arxiv.org/abs/2107.07511']);
}
// 14
{
 const s=slide('Mô hình dựa vào những đặc trưng nào','Trung bình trị tuyệt đối TreeSHAP trên 1.000 dòng validation');
 const importanceChart=bar(s,E.importance.categories.slice(0,8),E.importance.values.slice(0,8),66,230,1135,365,{horizontal:true,unit:'|TreeSHAP| log(1 + USD)',size:21});importanceChart.yAxis={numberFormatCode:'0.00'};importanceChart.dataLabels={showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{fontSize:21}};
 foot(s,'Mức đóng góp lớn thể hiện cách mô hình sử dụng tín hiệu. Không chứng minh quan hệ nhân quả.');
 note(s,'Giải thích dùng TreeSHAP của mô hình cuối fit train + validation. Đây là thống kê mô tả trên 1.000 dòng đầu validation, không phải điểm kiểm thử độc lập. Dữ liệu one-hot của zipcode được cộng về cùng một đặc trưng.',[sources.shap]);
}
// 15
{
 const s=slide('Ví dụ một căn nhà trong tập test','Chọn theo giá thật gần trung vị test trước khi xem sai số');
 table(s,[['Thuộc tính','Giá trị'],['Diện tích ở',fmt(X.input.living_m2,2)+' m²'],['Diện tích đất',fmt(X.input.lot_m2,2)+' m²'],['Phòng ngủ / phòng tắm',X.input.bedrooms+' / '+X.input.bathrooms],['Grade / năm xây',X.input.grade+' / '+X.input.year_built],['Mã bưu chính / ngày bán',X.input.zipcode+' / '+X.input.sale_date]],66,220,650,345,[350,300]);
 stat(s,bn(R.predicted_vnd),'tỷ VND dự đoán',805,230,405);
 text(s,'Giá thật '+bn(X.actual_vnd)+' tỷ VND\nSai lệch '+pct(Math.abs(R.predicted_vnd-X.actual_vnd)/X.actual_vnd),808,445,400,100,29,C.ink);
 foot(s,'Mã nhà '+X.input.id+'. Giá gốc và giá dự đoán giữ cùng đơn vị quy đổi.');
 note(s,'Căn này thuộc test chưa được model fit. Giá bán thật bằng '+X.actual_usd+' USD, dự đoán bằng '+R.predicted_usd+' USD. Khu đất lớn và vị trí ở mã 98022 cho thấy chỉ nhìn diện tích ở là chưa đủ để mô tả tài sản.',[sources.dataset]);
}
// 16
{
 const s=slide('Giải thích giá của căn nhà ví dụ','Mức nền '+fmt(R.base_price_usd)+' USD · Tổng đóng góp '+fmt(R.explanations.reduce((sum,e)=>sum+e.log_contribution,0),4)+' trên thang log(1 + USD)');
 const effects=R.explanations.slice(0,8);
 chart(s,'bar',{position:{left:66,top:235,width:1135,height:355},categories:effects.map(e=>e.label),series:[{name:'Đóng góp log',values:effects.map(e=>e.log_contribution),points:effects.map((e,i)=>({idx:i,fill:e.log_contribution>=0?C.green:C.copper})),fill:C.green}],hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:70},xAxis:{textStyle:{fontSize:21},tickLabelPosition:'low'},yAxis:{textStyle:{fontSize:21},min:-.35,max:.35,numberFormatCode:'0.00',majorGridlines:{fill:C.line,width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.00',textStyle:{fontSize:20}}});
 foot(s,'Xanh: đóng góp dương. Nâu: đóng góp âm. Không chuyển các thanh thành khoản tiền VND cộng riêng.');
 note(s,'TreeSHAP trả mức nền và các đóng góp cộng thành log1p của dự đoán. Kiểm thử tự động tái tạo dự đoán bằng expm1(base + sum(contributions)). Nhóm biến tương quan có thể chia sẻ đóng góp theo cách mô hình đã học. Các thanh giải thích dự đoán, không giải thích nhân quả của thị trường.',[sources.shap]);
}
// 17
{
 const s=slide('Giá mỗi mét vuông và giao dịch đối chiếu','Đơn giá được tính từ toàn bộ dự đoán của căn nhà');
 stat(s,fmt(R.price_per_m2_vnd/1e6,1),'triệu VND / m² diện tích ở',68,228,520);
 text(s,bn(R.predicted_vnd)+' tỷ VND ÷ '+fmt(X.input.living_m2,2)+' m²',68,430,610,70,31,C.green,true);
 text(s,'Không có một đơn giá cố định\náp dụng cho mọi căn nhà',735,260,470,100,31,C.ink,true);
 text(s,'Đối chiếu các căn đã bán trước ngày định giá, gần vị trí và tương đồng về diện tích, phòng ngủ và phòng tắm.',735,430,470,135,25,C.muted);
 foot(s,'Giá/m² được tính sau dự đoán. Sử dụng giá/m² thật làm đầu vào sẽ làm rò rỉ nhãn.');
 note(s,'Năm giao dịch đối chiếu được tìm trong train + validation, lọc ngày bán trước ngày định giá và loại cùng mã nhà. Hệ điểm tìm kiếm kết hợp khoảng cách đường chim bay, chênh lệch diện tích và số phòng. Các giao dịch là đối chiếu mô tả, không được cộng trọng số để giả làm phép tính của XGBoost.',[sources.dataset]);
}
// 18
{
 const s=slide('Ứng dụng và dữ liệu cùng một quy trình','Notebook, báo cáo và giao diện dùng cùng artifact đánh giá');
 table(s,[['Thành phần','Nội dung'],['Dữ liệu','Snapshot CSV, checksum, ngày giao dịch và mã căn'],['Mô hình','Train + validation, calibration riêng, test giữ lại'],['Kết quả','VND, VND/m², khoảng dự đoán, TreeSHAP'],['Lưu trữ','kingcounty_sales và kingcounty_predictions'],['Kiểm tra','73 bài đạt cục bộ, chưa chạy PostgreSQL']],66,230,1135,325,[350,785]);
 foot(s,'Khởi động: TieuLuan_CuoiKy/chay_ui.cmd. Công cụ nhập dữ liệu cũ vẫn có tại /legacy.');
 note(s,'Giao diện chính dùng bộ nhập thuộc tính King County. API chặn tọa độ Việt Nam, mã bưu chính ngoài dữ liệu, ngày định giá ngoài kỳ và các giá trị cấu trúc không hợp lệ. Mô hình mới tách biệt với mô hình legacy. Kiểm thử xác nhận chuyển tiền, giải thích cộng chính xác, không chung mã nhà và lưu chỉ các yêu cầu hợp lệ.');
}
// 19
{
 const s=slide('Giới hạn và bước phát triển tiếp theo','Chất lượng mô hình cần đi cùng phạm vi dữ liệu',true);
 text(s,'Dữ liệu lịch sử của một quận tại Mỹ',68,245,1110,55,34,C.white,true);
 text(s,'Chưa xác minh được khoảng cách trường học và cửa hàng',68,337,1110,65,31,'#C6D7D1');
 text(s,'Sai số tuyệt đối và bề rộng khoảng vẫn đáng kể',68,435,1110,55,31,'#C6D7D1');
 text(s,'Ưu tiên bổ sung dữ liệu đúng thời điểm và đánh giá trên kỳ mới',68,545,1110,80,31,'#A9CCBB',true);
 note(s,'Bản hiện tại là nghiên cứu học máy có minh bạch phạm vi. Cần mở rộng kỳ giao dịch, kiểm tra nguồn thuộc tính đúng tại ngày bán, bổ sung dữ liệu tiện ích hợp lệ, hiệu chỉnh lại trên kỳ mới và so sánh với các phương pháp định giá độc lập. Phần tiền VND chỉ đổi đơn vị, không chuyển mô hình sang thị trường Việt Nam.',Object.values(sources));
}
for(const ch of allCharts)applyPresentationChartFont(ch,{fontFamily:'Arial'});
await fs.mkdir(WORK+'/preview',{recursive:true});await fs.mkdir(WORK+'/staging',{recursive:true});await fs.mkdir(WORK+'/output',{recursive:true});
const candidate=WORK+'/staging/candidate.pptx';await(await PresentationFile.exportPptx(P)).save(candidate);console.log('Created draft',P.slides.items.length,'slides');
for(let i=0;i<P.slides.items.length;i++){const blob=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(WORK+'/preview/slide-'+String(i+1).padStart(2,'0')+'.png',new Uint8Array(await blob.arrayBuffer()));console.log('Rendered',i+1);}
const revision=String(Date.now());
const finalPath=WORK+'/output/Phan_tich_Gia_nha_King_County_'+revision+'.pptx';
const result=await finalizePresentation({workspaceDir:WORK,candidatePath:candidate,finalPath,pythonExecutable:PY,
 integrityValidatorPath:SKILL+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SKILL+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[...new Set(tableSlides)].flatMap(n=>['--require-native-table-slide',String(n)])],explicitTotalSlideCount:19,
 requiredNativeChartOwnerSlides:[...new Set(chartSlides)],requiredNativeTableOwnerSlides:[...new Set(tableSlides)],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:WORK+'/staging/validation-'+revision+'.json'});
console.log(JSON.stringify({finalPath:result.finalPath,sha256:result.finalSha256,integrity:result.packageIntegrity?.status,layoutFindings:result.presentationLayout?.findingCount,nativeCharts:result.nativeChartValidation?.passed}));
await fs.copyFile(finalPath,path.join(ROOT,'TieuLuan_CuoiKy/docs/Thuyet_trinh_TieuLuan_CuoiKy.pptx'));
console.log('Final deck delivered');
