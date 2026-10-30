"""Ứng dụng demo: python -m streamlit run app.py."""
from io import BytesIO
import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from src.housing import ROOT, FEATURES, NUMERIC, CATEGORICAL, INTEGER_FIELDS, LABELS, load_metadata, predict_prices

st.set_page_config(page_title="Ames Housing | Nhóm 8", page_icon="🏡", layout="wide")


@st.cache_resource
def resources():
    return joblib.load(ROOT / "artifacts/model.joblib"), load_metadata()


@st.cache_data
def historical_data():
    return pd.read_csv(ROOT / "data/processed/housing.csv")


try:
    model, meta = resources()
    data = historical_data()
except FileNotFoundError:
    st.error("Chưa có mô hình. Chạy: python -m scripts.train và python -m scripts.visualize")
    st.stop()

st.sidebar.title("🏡 Ames Housing")
st.sidebar.caption("Tiểu luận Lập trình Python · Nhóm 8")
page = st.sidebar.radio("Chức năng", ["Tổng quan", "Khám phá dữ liệu", "Dự đoán giá nhà", "Đánh giá mô hình"])
st.sidebar.divider()
st.sidebar.write("**Nguyễn Duy Trường**")
st.sidebar.caption("MSSV 24150180 · STT 6")
st.sidebar.caption("Thị trường Ames, Iowa, Mỹ\n\nDữ liệu giao dịch 2006–2010 · USD")

if page == "Tổng quan":
    st.caption("PHÂN TÍCH DỮ LIỆU & HỌC MÁY")
    st.title("Hiểu dữ liệu. Ước tính giá nhà.")
    st.write("Khám phá những yếu tố gắn với giá bán và thử mô hình dự đoán từ thông tin của một căn nhà tại Ames.")
    cols = st.columns(3)
    cols[0].metric("Giao dịch trong dataset", f"{len(data):,}")
    cols[1].metric("Thông tin đầu vào", len(FEATURES))
    cols[2].metric("Mô hình được chọn", meta["selected_model"])
    a, b = st.columns([1.4, 1])
    with a:
        st.image(str(ROOT / "artifacts/figures/01_price_distribution.png"), width="stretch")
    with b:
        st.subheader("Bắt đầu từ đâu?")
        st.write("**1. Khám phá dữ liệu** — lọc khu vực, xem phân phối giá và mối liên hệ với diện tích.")
        st.write("**2. Dự đoán giá nhà** — điền các thông số hoặc tải CSV theo mẫu để xử lý nhiều căn nhà.")
        st.write("**3. Đánh giá mô hình** — xem sai số và so sánh kết quả của các thuật toán.")
        st.caption("Giá dự đoán phản ánh phạm vi dữ liệu lịch sử tại Ames; không quy đổi thành giá thị trường Việt Nam hiện tại.")
        st.link_button("Nguồn dữ liệu và nghiên cứu gốc", "https://jse.amstat.org/v19n3/decock.pdf")

elif page == "Khám phá dữ liệu":
    st.title("Khám phá dữ liệu bất động sản")
    neighborhoods = st.multiselect("Lọc khu vực", sorted(data.Neighborhood.unique()))
    selected = data[data.Neighborhood.isin(neighborhoods)] if neighborhoods else data
    st.caption("Bảng và biểu đồ tại đây mô tả toàn bộ dữ liệu lịch sử; các hình phân tích trong báo cáo dùng tập train.")
    a, b, c = st.columns(3)
    a.metric("Số căn nhà", len(selected))
    b.metric("Giá trung vị", f"${selected.SalePrice.median():,.0f}")
    c.metric("Diện tích ở trung vị", f"{selected['Gr Liv Area'].median():,.0f} ft²")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(selected.SalePrice, bins=25, color="#167A78", ax=axes[0])
    axes[0].set(xlabel="Giá bán (USD)", ylabel="Số căn nhà")
    sns.scatterplot(data=selected, x="Gr Liv Area", y="SalePrice", hue="Overall Qual", palette="viridis", ax=axes[1], s=20)
    axes[1].set(xlabel="Diện tích ở (ft²)", ylabel="Giá bán (USD)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    st.dataframe(selected, hide_index=True, width="stretch")
    st.download_button("Tải dữ liệu đã lọc", selected.to_csv(index=False).encode("utf-8-sig"), "ames_filtered.csv", "text/csv")

elif page == "Dự đoán giá nhà":
    st.title("Dự đoán giá nhà")
    st.caption("Giá tính bằng USD. Diện tích tính bằng ft²; 1 m² ≈ 10,764 ft². Các giá trị điền sẵn là trung vị/mốt từ tập train.")
    mode = st.radio("Cách nhập", ["Một căn nhà", "Nhiều căn nhà từ CSV"], horizontal=True)
    if mode == "Một căn nhà":
        with st.form("house_form"):
            values = {}
            columns = st.columns(3)
            for i, col in enumerate(NUMERIC):
                low, high = meta["input_bounds"][col]
                with columns[i % 3]:
                    if col in INTEGER_FIELDS:
                        values[col] = st.number_input(LABELS[col], min_value=int(low), max_value=int(high),
                                                     value=int(meta["defaults"][col]), step=1, key=col)
                    else:
                        values[col] = st.number_input(LABELS[col], min_value=float(low), max_value=float(high),
                                                     value=float(meta["defaults"][col]), step=10., key=col)
            categories = st.columns(4)
            for col, container in zip(CATEGORICAL, categories):
                with container:
                    options = meta["categories"][col]
                    values[col] = st.selectbox(LABELS[col], options, index=options.index(meta["defaults"][col]), key=col)
            submitted = st.form_submit_button("Dự đoán giá", type="primary")
        if submitted:
            try:
                result = predict_prices(model, pd.DataFrame([values]), meta)
                price = result.PredictedPrice_USD.iloc[0]
                st.success(f"Giá dự đoán: ${price:,.0f} USD")
                st.caption(f"Mô hình: {meta['selected_model']}. Đây là ước lượng từ thông số đã nhập, không phải giá giao dịch được bảo đảm.")
                st.download_button("Tải kết quả", result.to_csv(index=False).encode("utf-8-sig"), "du_doan_gia_nha.csv", "text/csv")
            except ValueError as error:
                st.error(str(error))
        with st.expander("Giải thích mã loại nhà"):
            st.write("1Fam: nhà một gia đình; 2fmCon: nhà chuyển đổi cho hai gia đình; Duplex: nhà song lập; Twnhs/TwnhsE: nhà liền kề. 1Story: một tầng; 2Story: hai tầng; SLvl: lệch tầng; SFoyer: lối vào chia tầng. Central Air Y/N: có/không điều hòa trung tâm.")
            st.caption("Các mã khác được mô tả trong data/raw/DataDocumentation.txt.")
    else:
        st.write("CSV cần đủ 15 cột như file mẫu. Tối đa 2.000 dòng, 4 MB; ô số để trống sẽ được điền từ tập train.")
        st.download_button("Tải CSV mẫu", (ROOT / "data/sample_input.csv").read_bytes(), "sample_input.csv", "text/csv")
        uploaded = st.file_uploader("Chọn CSV", type=["csv"])
        if uploaded is not None:
            try:
                if uploaded.size > 4 * 1024 * 1024:
                    raise ValueError("File vượt quá 4 MB.")
                frame = pd.read_csv(BytesIO(uploaded.getvalue()))
                result = predict_prices(model, frame, meta)
                st.success(f"Đã dự đoán {len(result)} căn nhà.")
                st.dataframe(result, hide_index=True, width="stretch")
                st.download_button("Tải CSV kết quả", result.to_csv(index=False).encode("utf-8-sig"), "batch_predictions.csv", "text/csv")
            except (ValueError, UnicodeError, pd.errors.ParserError) as error:
                st.error(f"Không xử lý được CSV: {error}")

else:
    st.title("Đánh giá mô hình")
    scores = pd.read_csv(ROOT / "artifacts/metrics.csv")
    best = scores.loc[scores.model == meta["selected_model"]].iloc[0]
    a, b, c = st.columns(3)
    a.metric("MAE trên test", f"${best.test_mae:,.0f}")
    b.metric("RMSE trên test", f"${best.test_rmse:,.0f}")
    c.metric("R² trên test", f"{best.test_r2:.3f}")
    st.write(f"{meta['train_rows']:,} mẫu train, {meta['test_rows']:,} mẫu test. Chọn mô hình theo RMSE kiểm định chéo 5 phần trên train.")
    st.dataframe(scores.round(3), hide_index=True, width="stretch")
    st.caption("MAE là sai số tuyệt đối trung bình; RMSE nhạy với lỗi lớn; R² biểu thị mức giải thích biến thiên, không phải phần trăm dự đoán đúng.")
    st.image(str(ROOT / "artifacts/figures/05_model_comparison.png"), width="stretch")
    st.image(str(ROOT / "artifacts/figures/06_predictions_residuals.png"), width="stretch")
    with st.expander("Đặc trưng và giới hạn mô hình"):
        st.image(str(ROOT / "artifacts/figures/07_feature_importance.png"), width="stretch")
        st.write("Độ quan trọng là sự thay đổi sai số khi xáo trộn dữ liệu; không chứng minh quan hệ nhân quả. Sai số có thể lớn với căn nhà hiếm hoặc tổ hợp thông số khác xa các mẫu huấn luyện.")
