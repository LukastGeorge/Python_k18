'use strict';

const $ = (id) => document.getElementById(id);
const form = $('house-form');
const money = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 0 });
const number = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 });
let page = 1;
let totalPages = 1;
let listVersion = 0;
let searchTimer;

async function api(path, payload) {
  const options = { signal: AbortSignal.timeout(15000) };
  if (payload !== undefined) {
    options.method = 'POST';
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(payload);
  }
  let response;
  try {
    response = await fetch(path, options);
  } catch (_error) {
    throw new Error('Không nhận được phản hồi từ API. Kiểm tra cửa sổ chạy chay_ui.cmd rồi thử lại.');
  }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Không xử lý được yêu cầu.');
  return data;
}

function feedback(message, isError = false) {
  $('feedback').hidden = false;
  $('feedback').classList.toggle('error', isError);
  $('feedback').textContent = message;
}

async function busy(button, label, action) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try { await action(); }
  finally { button.disabled = false; button.textContent = original; }
}

async function loadStatus() {
  try {
    const status = await api('/api/status');
    const backend = status.database.backend === 'sqlite' ? 'SQLite' : 'PostgreSQL';
    $('connection').textContent = `${backend} đã kết nối`;
    $('connection').className = 'badge success';
    $('connection-error').hidden = true;
    $('database-name').textContent = backend;
    for (const key of ['total', 'real', 'demo']) $('count-' + key).textContent = number.format(status.counts[key]);
    $('model-name').textContent = status.model.error ? 'Lỗi nạp mô hình' : status.model.method === 'trained_model' ? 'Đã huấn luyện' : 'Chưa huấn luyện';
    $('model-note').textContent = status.model.error || (status.model.method === 'trained_model'
      ? 'Sử dụng mô hình VND đã huấn luyện của dự án.'
      : 'Chế độ Minh họa dùng công thức mẫu. Dữ liệu thật được lưu với giá dự đoán trống đến khi có mô hình.');
    return true;
  } catch (error) {
    $('connection').textContent = 'Mất kết nối database';
    $('connection').className = 'badge danger';
    $('connection-error-text').textContent = error.message;
    $('connection-error').hidden = false;
    $('database-name').textContent = 'Chưa kết nối';
    $('model-name').textContent = 'Chưa kiểm tra';
    for (const key of ['total', 'real', 'demo']) $('count-' + key).textContent = '—';
    return false;
  }
}

const methods = { demo_formula: 'Công thức minh họa', trained_model: 'Mô hình đã huấn luyện', unavailable: 'Chưa có mô hình' };

function cell(row, content) {
  const td = document.createElement('td');
  if (typeof content === 'string') td.textContent = content;
  else td.append(content);
  row.append(td);
  return td;
}

function renderRows(items) {
  $('records-body').replaceChildren();
  for (const item of items) {
    const row = document.createElement('tr');
    const name = document.createElement('strong');
    name.textContent = item.title;
    const nameCell = cell(row, name);
    const id = document.createElement('small');
    id.textContent = `${item.id} · ${item.source}`;
    nameCell.append(id);
    cell(row, `${number.format(item.dien_tich)} m²`);
    cell(row, String(item.so_phong_ngu));
    const priceCell = cell(row, item.predicted_price === null ? 'Chưa có dự đoán' : `${money.format(item.predicted_price)} ₫`);
    const method = document.createElement('small');
    method.textContent = methods[item.prediction_method] || item.prediction_method;
    priceCell.append(method);
    if (item.actual_price !== null) {
      const actual = document.createElement('small');
      actual.textContent = `Giá bán: ${money.format(item.actual_price)} ₫`;
      priceCell.append(actual);
    }
    const badge = document.createElement('span');
    badge.className = `badge ${item.is_demo ? 'demo' : 'real'}`;
    badge.textContent = item.is_demo ? 'Minh họa' : 'Dữ liệu thật';
    cell(row, badge);
    cell(row, new Date(item.updated_at).toLocaleString('vi-VN', { dateStyle: 'short', timeStyle: 'short' }));
    $('records-body').append(row);
  }
}

async function loadRecords() {
  const version = ++listVersion;
  const params = new URLSearchParams({ page, page_size: 10, q: $('search').value.trim(), mode: $('filter-mode').value });
  $('records-summary').textContent = 'Đang tải danh sách…';
  try {
    const data = await api('/api/records?' + params);
    if (version !== listVersion) return;
    totalPages = data.total_pages;
    renderRows(data.items);
    $('empty-state').hidden = data.items.length !== 0;
    $('empty-state').querySelector('strong').textContent = data.total === 0 ? 'Chưa có căn nhà phù hợp' : 'Không có dữ liệu ở trang này';
    $('empty-state').querySelector('p').textContent = 'Nhập căn nhà, nạp tin mẫu hoặc thay đổi bộ lọc để xem dữ liệu.';
    $('records-summary').textContent = `${number.format(data.total)} căn nhà phù hợp với bộ lọc`;
    $('page-info').textContent = `Trang ${page} / ${totalPages}`;
    $('previous-page').disabled = page <= 1;
    $('next-page').disabled = page >= totalPages;
  } catch (error) {
    if (version !== listVersion) return;
    renderRows([]);
    $('empty-state').hidden = false;
    $('empty-state').querySelector('strong').textContent = 'Chưa tải được dữ liệu';
    $('empty-state').querySelector('p').textContent = error.message;
    $('records-summary').textContent = 'Database chưa sẵn sàng';
    $('previous-page').disabled = true;
    $('next-page').disabled = true;
  }
}

async function refresh() {
  await loadStatus();
  await loadRecords();
}

function newHouse() {
  const demo = form.elements.mode.value === 'demo';
  form.elements.id.value = 'WEB-' + crypto.randomUUID().slice(0, 8).toUpperCase();
  for (const field of ['title', 'area', 'rooms', 'latitude', 'longitude', 'actual_price']) form.elements[field].value = '';
  if (demo) {
    form.elements.title.value = '[DEMO] Nhà 50 m², 2 phòng ngủ';
    form.elements.area.value = 50;
    form.elements.rooms.value = 2;
    form.elements.latitude.value = 10.762622;
    form.elements.longitude.value = 106.660172;
  }
  $('actual-price-field').hidden = demo;
  $('mode-note').textContent = demo
    ? 'Thông tin và tọa độ dưới đây là mẫu. Giá tính bằng công thức khi chưa có mô hình; không dùng để huấn luyện.'
    : 'Nhập tọa độ và thông tin thực tế. Nếu chưa có mô hình, dữ liệu vẫn được lưu và giá dự đoán để trống.';
  $('form-error').hidden = true;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  $('form-error').hidden = true;
  await busy($('submit-house'), 'Đang dự đoán & lưu…', async () => {
    const payload = Object.fromEntries(new FormData(form));
    if (payload.mode === 'demo' || payload.actual_price === '') delete payload.actual_price;
    try {
      const data = await api('/api/records', payload);
      const item = data.item;
      $('result-title').textContent = item.title;
      $('prediction').textContent = item.predicted_price === null ? 'Chưa có dự đoán' : money.format(item.predicted_price);
      $('result-method').textContent = methods[item.prediction_method];
      $('result-method').className = `badge ${item.prediction_method === 'demo_formula' ? 'demo' : item.prediction_method === 'trained_model' ? 'real' : 'neutral'}`;
      $('result-note').textContent = data.message;
      $('result-details').hidden = false;
      $('result-details').textContent = `${number.format(item.dien_tich)} m² · ${item.so_phong_ngu} phòng ngủ · ${item.id}`;
      feedback(data.message);
      page = 1;
      await refresh();
    } catch (error) {
      $('form-error').hidden = false;
      $('form-error').textContent = error.message;
    }
  });
});

$('seed-demo').addEventListener('click', () => busy($('seed-demo'), 'Đang nạp…', async () => {
  try {
    const data = await api('/api/demo', {});
    feedback(data.message);
    page = 1;
    await refresh();
  } catch (error) { feedback(error.message, true); }
}));
$('new-house').addEventListener('click', newHouse);
form.querySelectorAll('input[name="mode"]').forEach((input) => input.addEventListener('change', newHouse));
$('refresh').addEventListener('click', () => busy($('refresh'), 'Đang tải…', refresh));
$('retry').addEventListener('click', refresh);
$('search').addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { page = 1; loadRecords(); }, 300);
});
$('filter-mode').addEventListener('change', () => { page = 1; loadRecords(); });
$('previous-page').addEventListener('click', () => { if (page > 1) { page--; loadRecords(); } });
$('next-page').addEventListener('click', () => { if (page < totalPages) { page++; loadRecords(); } });
newHouse();
refresh();
