"""Streamlit UI with explicit geographic and temporal coverage."""
from io import BytesIO
import hashlib
import json
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from src.us_housing import ROOT, DB, ARTIFACTS, STATES, AREA_LABELS, LIMITATION, read_sales, coverage, predict_prices


@st.cache_resource
def resources(database_stamp, model_stamp):
    meta = json.loads((ARTIFACTS / 'metadata.json').read_text(encoding='utf-8'))
    if hashlib.sha256(DB.read_bytes()).hexdigest() != meta['database_sha256']:
        raise ValueError('Database đã thay đổi. Chạy python -m scripts.train_us để cập nhật mô hình.')
    return joblib.load(ARTIFACTS / 'model.joblib'), meta


@st.cache_data
def history(database_stamp):
    return read_sales()


def predict_page(model, meta):
    st.title('Dự đoán giá từng căn nhà')
    st.write('Chọn vị trí, thời điểm định giá và đặc điểm căn nhà. Giá tính bằng USD.')
    mode = st.radio('Cách nhập', ['Một căn nhà', 'Nhiều căn nhà từ CSV'], horizontal=True)
    st.caption('Ước lượng phục vụ học tập trong phạm vi mẫu đã thu thập. ' + LIMITATION)
    if mode == 'Nhiều căn nhà từ CSV':
        st.download_button('Tải CSV mẫu mới', (ROOT / 'data/us_sample_input.csv').read_bytes(), 'us_sample_input.csv', 'text/csv')
        st.caption('Tối đa 2.000 dòng, 4 MB. area_sqft tính bằng ft²; area_kind phải đúng với khu vực.')
        upload = st.file_uploader('Chọn CSV', type=['csv'])
        if upload is not None:
            try:
                if upload.size > 4 * 1024 * 1024:
                    raise ValueError('File vượt quá 4 MB.')
                result = predict_prices(model, pd.read_csv(BytesIO(upload.getvalue())), meta)
                st.dataframe(result, hide_index=True)
                st.download_button('Tải kết quả', result.to_csv(index=False).encode('utf-8-sig'), 'us_predictions.csv', 'text/csv')
            except (ValueError, UnicodeError, pd.errors.ParserError) as error:
                st.error(str(error))
        return
    supported = {s['state'] for s in meta['scopes'].values()}
    options = sorted(STATES, key=lambda s: (s not in supported, STATES[s]))
    state = st.selectbox('Bang / Đặc khu', options, key='us_state',
        format_func=lambda s: f'{STATES[s]} ({s})' + (' — chưa có mô hình' if s not in supported else ''))
    scopes = [s for s in meta['scopes'].values() if s['state'] == state]
    if not scopes:
        st.warning('Chưa có dữ liệu phù hợp để dự đoán tại khu vực này. Xem trang Độ phủ 51 khu vực để biết phần còn thiếu.')
        return
    locality = st.selectbox('Quận / Thành phố có dữ liệu', [s['locality'] for s in scopes], key='us_locality')
    scope = meta['scopes'][state + '|' + locality]
    st.info(f"Phạm vi: {locality}, {STATES[state]}. {scope['rows']:,} giao dịch; "
            f"{scope['first_date']} đến {scope['last_date']}." + (' Không đại diện toàn bang Colorado.' if state == 'CO' else ''))
    unit = st.radio('Đơn vị diện tích nhập', ['m²', 'ft²'], horizontal=True)
    factor = 0.09290304 if unit == 'm²' else 1.0
    low_date, high_date = pd.Timestamp(scope['first_date']), pd.Timestamp(scope['last_date'])
    year = st.selectbox('Năm định giá', list(range(low_date.year, high_date.year + 1)), index=high_date.year-low_date.year)
    months = list(range(low_date.month if year == low_date.year else 1, (high_date.month if year == high_date.year else 12) + 1))
    month = st.selectbox('Tháng định giá', months, index=len(months)-1)
    with st.form('us_house_form'):
        a, b = st.columns(2)
        lo, hi = scope['bounds']['area_sqft']
        area = a.number_input(f"{AREA_LABELS[scope['area_kind']]} ({unit})", min_value=float(lo*factor),
            max_value=float(hi*factor), value=float(scope['defaults']['area_sqft']*factor), key=f'area_{state}_{unit}')
        lo, hi = scope['bounds']['bedrooms']
        beds = b.number_input('Số phòng ngủ', min_value=int(lo), max_value=int(hi),
            value=int(scope['defaults']['bedrooms']), key=f'beds_{state}')
        lo, hi = scope['bounds']['bathrooms']
        baths = a.number_input('Số phòng tắm quy đổi', min_value=float(lo), max_value=float(hi),
            value=float(scope['defaults']['bathrooms']), step=0.25, key=f'baths_{state}')
        lo, hi = scope['bounds']['year_built']
        built = b.number_input('Năm xây dựng', min_value=int(lo), max_value=int(hi),
            value=int(scope['defaults']['year_built']), key=f'built_{state}')
        st.caption('Phòng tắm đầy đủ = 1; phòng 3/4 = 0,75; phòng 1/2 = 0,5. '
                   'Colorado dùng diện tích hoàn thiện; D.C. dùng diện tích xây dựng GBA.')
        submit = st.form_submit_button('Dự đoán giá', type='primary')
    if submit:
        values = {'state': state, 'locality': locality, 'area_kind': scope['area_kind'],
            'area_sqft': round(area / factor, 6), 'bedrooms': beds, 'bathrooms': baths,
            'year_built': built, 'sale_year': year, 'sale_month': month}
        try:
            result = predict_prices(model, pd.DataFrame([values]), meta)
            st.success(f"Giá dự đoán: ${result.PredictedPrice_USD.iloc[0]:,.0f} USD")
            st.caption(f"Tham chiếu {month:02d}/{year} tại {locality}; mô hình {meta['selected_model']}.")
            st.download_button('Tải kết quả', result.to_csv(index=False).encode('utf-8-sig'), 'us_prediction.csv', 'text/csv')
        except ValueError as error:
            st.error(str(error))


def coverage_page(data, summary):
    st.title('Độ phủ 51 khu vực · 2016–2026')
    st.write('Mục tiêu: 50 bang và Washington, D.C. Số 0 là chưa có bản ghi trong database này; không có nghĩa là không có giao dịch ngoài thị trường.')
    matrix = coverage(data)
    st.warning(f"Có mẫu tại {data.state.nunique()}/51 khu vực. Colorado chỉ có Boulder County. "
               'Có mẫu trong một năm không đồng nghĩa đã thu thập đầy đủ năm đó.')
    pivot = matrix.pivot(index=['state', 'state_name'], columns='year', values='records').reset_index()
    pivot.columns = pivot.columns.map(str)
    st.dataframe(pivot, hide_index=True, width='stretch', height=570)
    st.download_button('Tải bảng độ phủ CSV', matrix.to_csv(index=False).encode('utf-8-sig'), 'coverage_2016_2026.csv', 'text/csv')
    st.caption(f"Xử lý ngày {summary['as_of']}; năm 2026 mới có phần đã công bố đến ngày tải.")
    with st.expander('Nguồn và quy tắc làm sạch'):
        for source in summary['sources']:
            st.markdown(f"[{source['locality']}]({source['url']}) — {source['description']}")
        st.json(summary['audit'])
        st.write(LIMITATION)


def explore_page(data):
    st.title('Khám phá giá bán đã ghi nhận')
    states = sorted(data.state.unique())
    selected = st.multiselect('Khu vực', states, default=states, format_func=lambda s: STATES[s])
    years = st.slider('Năm bán', 2016, 2026, (2016, 2026))
    filtered = data[data.state.isin(selected) & data.sale_year.between(*years)]
    if filtered.empty:
        st.info('Không có bản ghi cho bộ lọc này.')
        return
    a, b, c = st.columns(3)
    a.metric('Giao dịch', f'{len(filtered):,}')
    b.metric('Giá bán trung vị', f'${filtered.price_usd.median():,.0f}')
    c.metric('Căn nhà phân biệt', f'{filtered.property_id.nunique():,}')
    st.caption('Thống kê mô tả mẫu đã làm sạch. Một căn có thể bán nhiều lần; đặc điểm nhà là bản ghi hiện tại.')
    monthly = filtered.assign(month=filtered.sale_date.str.slice(0, 7)).groupby(['month', 'locality']).price_usd.median().unstack()
    st.subheader('Giá bán trung vị theo tháng và khu vực')
    st.line_chart(monthly)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for locality, group in filtered.groupby('locality'):
        axes[0].hist(group.price_usd, bins=35, alpha=0.5, label=locality)
        sample = group.sample(min(1500, len(group)), random_state=42)
        axes[1].scatter(sample.area_sqft, sample.price_usd, s=8, alpha=0.35, label=locality)
    axes[0].set(xlabel='Sale price (USD)', ylabel='Transactions')
    axes[1].set(xlabel='Area (ft²; definition differs by source)', ylabel='Sale price (USD)')
    for axis in axes:
        axis.legend(fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(filtered.drop(columns=['property_id', 'transaction_id']).head(1000), hide_index=True)
    st.caption('Bảng xem trước tối đa 1.000 dòng; CSV chứa toàn bộ kết quả lọc.')
    st.download_button('Tải dữ liệu đã lọc', filtered.to_csv(index=False).encode('utf-8-sig'), 'us_sales_filtered.csv', 'text/csv')


def evaluation_page(meta):
    st.title('Đánh giá mô hình')
    scores = meta['test_metrics']
    a, b, c = st.columns(3)
    a.metric('MAE trên test', f"${scores['mae']:,.0f}")
    b.metric('RMSE trên test', f"${scores['rmse']:,.0f}")
    c.metric('R² trên test', f"{scores['r2']:.3f}")
    st.write('Chọn mô hình bằng RMSE năm 2024; huấn luyện lại bằng train + validation và đánh giá trên 2025–2026. '
             'Các căn nhà trong test bị loại khỏi các tập trước đó.')
    st.write(f"Train: {meta['train_rows']:,}; validation: {meta['validation_rows']:,}; test: {meta['test_rows']:,}; "
             f"loại {meta['purged_rows']:,} giao dịch cũ của các căn nhà thuộc tập giữ lại.")
    st.subheader('So sánh trên validation 2024')
    st.dataframe(pd.read_csv(ARTIFACTS / 'validation_metrics.csv'), hide_index=True)
    st.subheader('Test theo khu vực')
    st.dataframe(pd.DataFrame(meta['test_metrics_by_state']).T.rename_axis('state').reset_index(), hide_index=True)
    st.info('Mô hình trên giao diện được huấn luyện lại bằng toàn bộ dữ liệu hợp lệ. '
            'Điểm test trên thuộc mô hình đánh giá riêng, không phải bản đã học toàn bộ dữ liệu.')
    st.warning(LIMITATION)
    st.caption('R² không phải phần trăm dự đoán đúng. Chưa có chỉ số cho 49 khu vực chưa thu thập dữ liệu.')


def run():
    st.set_page_config(page_title='US House Prices | Nhóm 8', page_icon='🏡', layout='wide')
    try:
        model, meta = resources(DB.stat().st_mtime_ns, (ARTIFACTS / 'model.joblib').stat().st_mtime_ns)
        data = history(DB.stat().st_mtime_ns)
        summary = json.loads((ARTIFACTS / 'data_summary.json').read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError) as error:
        st.error(f'Chưa sẵn sàng: {error}')
        st.code('python -m scripts.fetch_us_data\npython -m scripts.build_us_database\npython -m scripts.train_us')
        return
    st.sidebar.title('🏡 US House Prices')
    st.sidebar.caption('Giá từng căn · Dữ liệu công khai')
    page = st.sidebar.radio('Chức năng', ['Tổng quan', 'Khám phá dữ liệu', 'Dự đoán giá nhà', 'Độ phủ 51 khu vực', 'Đánh giá mô hình'])
    st.sidebar.divider()
    st.sidebar.write('**Nguyễn Duy Trường · Nhóm 8**')
    st.sidebar.caption('MSSV 24150180 · STT 6')
    st.sidebar.caption(f"Mục tiêu 2016–2026\n\nCó mẫu: {data.state.nunique()}/51 khu vực\n\nSQLite · USD")
    if page == 'Dự đoán giá nhà':
        predict_page(model, meta)
    elif page == 'Độ phủ 51 khu vực':
        coverage_page(data, summary)
    elif page == 'Khám phá dữ liệu':
        explore_page(data)
    elif page == 'Đánh giá mô hình':
        evaluation_page(meta)
    else:
        st.caption('PHÂN TÍCH BẤT ĐỘNG SẢN MỸ · 2016–2026')
        st.title('Từ giao dịch thực tế đến ước tính giá từng căn')
        st.write('Nhập diện tích, số phòng, năm xây dựng, bang và thời điểm để thử mô hình từ dữ liệu nhà ở công khai.')
        a, b, c = st.columns(3)
        a.metric('Giao dịch đã làm sạch', f'{len(data):,}')
        b.metric('Khu vực có mẫu / mục tiêu', f'{data.state.nunique()} / 51')
        c.metric('Năm có giao dịch', f'{data.sale_year.min()}–{data.sale_year.max()}')
        st.warning('Độ phủ hiện tại: Washington, D.C. và Boulder County thuộc Colorado. '
                   '49 bang còn lại chưa có dữ liệu trong bản này; Colorado chưa phủ toàn bang.')
        grouped = data.groupby(['state', 'locality']).agg(giao_dich=('price_usd', 'size'),
            tu_ngay=('sale_date', 'min'), den_ngay=('sale_date', 'max'), gia_trung_vi_USD=('price_usd', 'median')).reset_index()
        st.dataframe(grouped, hide_index=True, width='stretch')
        st.write('**Khám phá dữ liệu** để xem xu hướng. **Dự đoán giá nhà** để nhập một căn hoặc CSV. '
                 '**Độ phủ 51 khu vực** liệt kê số bản ghi từng bang, từng năm.')
        st.caption(LIMITATION)
        for source in summary['sources']:
            st.link_button('Nguồn: ' + source['locality'], source['url'])
