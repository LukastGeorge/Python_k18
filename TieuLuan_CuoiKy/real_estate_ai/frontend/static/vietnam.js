'use strict';
const form = document.getElementById('vn-form');
const el = id => document.getElementById(id);
const fmt = (v, n = 0) => new Intl.NumberFormat('vi-VN', {maximumFractionDigits:n}).format(v);
const billion = v => `${fmt(v / 1e9, 2)} tỷ VND`;
const percent = v => `${fmt(v * 100, 1)}%`;
let info;
let example = null;
function options(select, values, empty = false) {
  select.replaceChildren();
  if (empty) select.add(new Option('Chưa biết', 'Không rõ'));
  values.forEach(value => select.add(new Option(value, value)));
}
function updateDistricts() {
  const city = info.metadata.locations[form.elements.province_name.value];
  options(form.elements.district_name, Object.keys(city).sort((a,b) => a.localeCompare(b, 'vi')));
  updateLocation();
}
function updateLocation() {
  const location = info.metadata.locations[form.elements.province_name.value][form.elements.district_name.value];
  options(form.elements.ward_name, location.wards, true);
}
async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? {} : {
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || 'Chưa xử lý được yêu cầu.');
  return body;
}
function loadExample(index) {
  example = info.examples[index];
  if (!example) return;
  const data = example.input;
  form.elements.province_name.value = data.province_name;
  updateDistricts();
  form.elements.district_name.value = data.district_name;
  updateLocation();
  Object.entries(data).forEach(([name,value]) => {
    if (form.elements[name]) form.elements[name].value = value ?? '';
  });
  el('form-message').textContent = 'Đã điền tin trong tập test. Nhấn dự đoán để đối chiếu.';
}
async function history() {
  const body = await api('/api/vietnam/history');
  el('history').replaceChildren();
  body.items.forEach(row => {
    const tr = document.createElement('tr');
    [new Date(row.created_at).toLocaleString('vi-VN'), row.province_name, row.district_name, billion(row.predicted_vnd)].forEach(text => {
      const td = document.createElement('td'); td.textContent = text; tr.append(td);
    });
    el('history').append(tr);
  });
  if (!body.items.length) el('history').textContent = 'Chưa có dự đoán được lưu.';
}
function show(result) {
  el('result-price').textContent = billion(result.predicted_vnd);
  el('exact-price').textContent = `${fmt(result.predicted_vnd)} VND`;
  el('result-unit').textContent = `${fmt(result.price_per_m2_vnd / 1e6, 1)} triệu VND/m²`;
  el('result-interval').textContent = result.interval_90_vnd.map(billion).join(' – ');
  el('actual-price').textContent = example ? `Giá rao của tin test trong dataset 2024: ${billion(example.asking_vnd)}. Sai lệch ${percent(Math.abs(result.predicted_vnd - example.asking_vnd) / example.asking_vnd)}.` : '';
  el('effects').replaceChildren();
  const max = Math.max(...result.explanations.map(x => Math.abs(x.log_contribution)), .001);
  result.explanations.slice(0,8).forEach(item => {
    const row = document.createElement('div'); row.className = `effect${item.log_contribution < 0 ? ' negative' : ''}`;
    const label = document.createElement('span'); label.textContent = item.label;
    const bar = document.createElement('progress'); bar.max = max; bar.value = Math.abs(item.log_contribution);
    bar.setAttribute('aria-label', `${item.label}: ${fmt(item.log_contribution,3)} log VND`);
    const value = document.createElement('b'); value.textContent = `${item.log_contribution > 0 ? '+' : ''}${fmt(item.log_contribution,3)}`;
    row.append(label,bar,value); el('effects').append(row);
  });
  el('warnings').replaceChildren();
  result.warnings.forEach(text => { const p = document.createElement('p'); p.textContent = text; el('warnings').append(p); });
  el('comparables').replaceChildren();
  result.comparables.forEach(row => {
    const tr = document.createElement('tr');
    [row.district_name,row.ward_name,`${fmt(row.area,1)} m²`,billion(row.price),fmt(row.price / row.area / 1e6,1)].forEach(text => {
      const td = document.createElement('td'); td.textContent = text; tr.append(td);
    }); el('comparables').append(tr);
  });
  if (!result.comparables.length) el('comparables').textContent = 'Không có tin cùng địa bàn để đối chiếu.';
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  const button = el('predict-button'); button.disabled = true;
  el('form-message').textContent = 'Đang dự đoán…';
  try {
    const payload = Object.fromEntries(new FormData(form));
    ['area','bedroom_count','bathroom_count','floor_count','frontage_width','road_width'].forEach(name => {
      payload[name] = payload[name] === '' ? null : Number(payload[name]);
    });
    if (example) payload.reference_id = example.input.reference_id;
    const body = await api('/api/vietnam/predict', payload);
    show(body.result); el('form-message').textContent = 'Đã dự đoán và lưu vào database.';
    try { await history(); } catch (_) { el('form-message').textContent += ' Chưa tải được lịch sử.'; }
  } catch (error) { el('form-message').textContent = error.message; }
  finally { button.disabled = false; }
});
form.addEventListener('input', () => { example = null; el('example').value = ''; el('actual-price').textContent = ''; });
form.elements.province_name.addEventListener('change', updateDistricts);
form.elements.district_name.addEventListener('change', updateLocation);
el('example').addEventListener('change', event => loadExample(event.target.value));
(async () => {
  try {
    info = await api('/api/vietnam/info');
    const m = info.metadata;
    options(form.elements.province_name, Object.keys(m.locations)); updateDistricts();
    info.examples.forEach((item,index) => el('example').add(new Option(item.label, String(index))));
    el('metric-rows').textContent = fmt(m.audit.accepted_rows);
    el('metric-r2').textContent = fmt(m.test.r2,3);
    el('metric-20').textContent = percent(m.test.within_20pct);
    el('metric-mape').textContent = percent(m.test.median_ape);
    el('scope-note').textContent = m.scope;
    el('split-note').textContent = `Nguồn gốc ${fmt(m.audit.raw_rows)} dòng, ${m.audit.raw_columns} cột; giữ ${fmt(m.audit.accepted_rows)} tin và ${fmt(m.audit.property_proxy_groups)} nhóm địa chỉ–diện tích. Train ${fmt(m.splits.train.n)} tin; validation ${fmt(m.splits.validation.n)}; calibration ${fmt(m.splits.calibration.n)}; test ${fmt(m.splits.test.n)}. Các tập không chung khóa nhóm. Nguồn không có ngày đăng nên chưa đánh giá theo thời gian.`;
    el('coverage-note').textContent = `Khoảng 90% danh nghĩa có độ phủ test ${percent(m.test.coverage_90)}. ${m.test_breakdown.map(x => `${x.label}: ${percent(x.coverage_90)}`).join('; ')}. Chất lượng có thể thay đổi theo địa bàn và thời kỳ.`;
    if (info.examples.length) { el('example').value = '0'; loadExample(0); }
    el('predict-button').disabled = false;
    await history();
  } catch (error) { el('load-error').hidden = false; el('load-error').textContent = error.message; }
})();
