"""Tạo các hình dùng chung cho báo cáo và ứng dụng."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import seaborn as sns
from src.housing import ROOT, TARGET, load_metadata


def main():
    out = ROOT / "artifacts/figures"
    out.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid", font="DejaVu Sans", font_scale=1.05)
    metadata = load_metadata()
    data = pd.read_csv(ROOT / "data/processed/housing.csv")
    ids = json.loads((ROOT / "artifacts/split.json").read_text())["train_pid"]
    train = data[data.PID.isin(ids)]
    money = FuncFormatter(lambda x, p: f"{x / 1000:,.0f}k")

    def save(fig, name):
        fig.tight_layout(pad=1.2)
        fig.savefig(out / name, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    sns.histplot(train[TARGET], bins=35, kde=True, color="#167A78", ax=ax)
    ax.set(xlabel="Giá bán (USD)", ylabel="Số căn nhà", title="Phân phối giá nhà trong tập huấn luyện")
    ax.xaxis.set_major_formatter(money)
    save(fig, "01_price_distribution.png")

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    sns.scatterplot(data=train, x="Gr Liv Area", y=TARGET, hue="Overall Qual", palette="viridis", alpha=.65, s=22, ax=ax)
    ax.set(xlabel="Diện tích ở trên mặt đất (ft²)", ylabel="Giá bán (USD)", title="Diện tích, chất lượng và giá bán")
    ax.yaxis.set_major_formatter(money)
    ax.legend(title="Chất lượng", fontsize=8)
    save(fig, "02_area_price.png")

    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    common = train.Neighborhood.value_counts().head(8).index
    order = train[train.Neighborhood.isin(common)].groupby("Neighborhood")[TARGET].median().sort_values().index
    sns.boxplot(data=train[train.Neighborhood.isin(common)], x="Neighborhood", y=TARGET, order=order,
                color="#83B9B4", fliersize=2, ax=ax)
    ax.set(xlabel="8 khu vực có nhiều mẫu nhất", ylabel="Giá bán (USD)", title="Giá nhà theo khu vực")
    ax.yaxis.set_major_formatter(money)
    save(fig, "03_neighborhood.png")

    fig, ax = plt.subplots(figsize=(8.4, 5.4))
    cols = ["SalePrice", "Gr Liv Area", "Overall Qual", "Year Built", "Garage Cars", "Total Bsmt SF", "Lot Area"]
    aliases = ["Giá bán", "Diện tích ở", "Chất lượng", "Năm xây", "Chỗ đỗ xe", "Tầng hầm", "Diện tích đất"]
    corr = train[cols].corr()
    corr.index, corr.columns = aliases, aliases
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="BrBG", center=0, vmin=-1, vmax=1, ax=ax)
    ax.set(title="Tương quan Pearson trên tập huấn luyện")
    save(fig, "04_correlation.png")

    scores = pd.read_csv(ROOT / "artifacts/metrics.csv")
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    ax.barh(scores.model, scores.cv_rmse_mean, xerr=scores.cv_rmse_std, color="#167A78", capsize=4)
    ax.set(xlabel="RMSE trung bình ± độ lệch chuẩn (USD)", title="So sánh bằng kiểm định chéo 5 phần trên train")
    ax.xaxis.set_major_formatter(money)
    ax.invert_yaxis()
    save(fig, "05_model_comparison.png")

    predictions = pd.read_csv(ROOT / "artifacts/test_predictions.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].scatter(predictions.actual_usd, predictions.predicted_usd, color="#167A78", alpha=.55, s=15)
    maximum = max(predictions.actual_usd.max(), predictions.predicted_usd.max())
    axes[0].plot([0, maximum], [0, maximum], "--", color="#B16B35")
    axes[0].set(xlabel="Giá thực tế (USD)", ylabel="Giá dự đoán (USD)", title="Dự đoán trên tập kiểm tra")
    axes[1].scatter(predictions.predicted_usd, predictions.residual_usd, color="#167A78", alpha=.55, s=15)
    axes[1].axhline(0, color="#B16B35", linestyle="--")
    axes[1].set(xlabel="Giá dự đoán (USD)", ylabel="Thực tế − dự đoán (USD)", title="Phân tích phần dư")
    for ax in axes:
        ax.xaxis.set_major_formatter(money)
        ax.yaxis.set_major_formatter(money)
    save(fig, "06_predictions_residuals.png")

    importance = pd.read_csv(ROOT / "artifacts/feature_importance.csv").head(8).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.barh(importance.feature, importance.increase_rmse, xerr=importance["std"], color="#167A78", capsize=3)
    ax.set(xlabel="Mức tăng RMSE khi xáo trộn đặc trưng (USD)", title="Mức quan trọng của đặc trưng trên tập kiểm tra")
    save(fig, "07_feature_importance.png")
    print(f"Generated 7 figures in {out}")


if __name__ == "__main__":
    main()
