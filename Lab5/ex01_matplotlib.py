"""Bài 3.1: Trực quan hóa doanh số, quảng cáo và lượng mưa năm 2025."""

from pathlib import Path

import matplotlib

# Xuất ảnh trực tiếp, chạy được cả khi không có giao diện đồ họa.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# Dữ liệu mẫu của đề, đơn vị: tháng, triệu VNĐ và mm.
months = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
sales = [120, 135, 160, 190, 210, 250, 230, 220, 195, 170, 200, 280]
ad_budget = [10, 12, 15, 20, 22, 30, 25, 24, 18, 15, 22, 35]
rainfall = [20, 15, 30, 80, 150, 220, 250, 210, 180, 120, 50, 25]

OUTPUT_DIR = Path(__file__).resolve().parent


def create_sales_plot():
    """Nhiệm vụ 1: Biểu đồ đường doanh số với màu, nét và marker theo đề."""
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    ax.plot(
        months, sales, color="darkblue", linestyle="dashed",
        marker="o", linewidth=2, label="Doanh số năm 2025",
    )
    ax.set_title("Xu Hướng Doanh Số Năm 2025", fontweight="bold", pad=12)
    ax.set_xlabel("Tháng")
    ax.set_ylabel("Doanh số (Triệu VNĐ)")
    ax.set_ylim(0, 320)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left")
    return fig


def create_advertising_plot():
    """Nhiệm vụ 2: Tô màu và chú thích tháng có ngân sách lớn nhất."""
    highest_budget = max(ad_budget)
    # Đề ghi 'xám skyblue'; dùng đúng mã màu skyblue (xanh da trời).
    colors = ["crimson" if value == highest_budget else "skyblue"
              for value in ad_budget]

    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    bars = ax.bar(months, ad_budget, color=colors, width=0.65)
    ax.set_title("Chi Tiêu Quảng Cáo Theo Tháng", fontweight="bold", pad=12)
    ax.set_xlabel("Tháng")
    ax.set_ylabel("Chi tiêu quảng cáo (Triệu VNĐ)")
    ax.set_ylim(0, highest_budget * 1.35)
    ax.set_axisbelow(True)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    for index, bar in enumerate(bars):
        if ad_budget[index] == highest_budget:
            ax.annotate(
                f"Cao nhất: {months[index]}\n{highest_budget} Triệu VNĐ",
                xy=(bar.get_x() + bar.get_width() / 2, highest_budget),
                xytext=(-18, 25), textcoords="offset points",
                ha="right", fontsize=10, color="crimson",
                arrowprops={"arrowstyle": "->", "color": "crimson"},
            )
    return fig


def create_business_report():
    """Nhiệm vụ 3: Subplots 1x2, gồm scatter và hai chuỗi theo tháng."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
    ax_scatter, ax_sales = axes

    ax_scatter.scatter(
        ad_budget, sales, color="darkblue", s=60, alpha=0.85,
        edgecolors="white", linewidths=0.6,
    )
    ax_scatter.set_title("Quảng Cáo Và Doanh Số", fontweight="bold", pad=12)
    ax_scatter.set_xlabel("Chi tiêu quảng cáo (Triệu VNĐ)")
    ax_scatter.set_ylabel("Doanh số (Triệu VNĐ)")
    ax_scatter.grid(True, linestyle=":", alpha=0.5)
    ax_scatter.set_axisbelow(True)

    # Hai đại lượng khác đơn vị: dùng hai trục Y và ghi rõ từng đơn vị.
    ax_rain = ax_sales.twinx()
    sales_line = ax_sales.plot(
        months, sales, color="darkblue", marker="o",
        linewidth=2, label="Doanh số (Triệu VNĐ)",
    )
    rain_line = ax_rain.plot(
        months, rainfall, color="teal", linestyle="--", marker="s",
        linewidth=2, label="Lượng mưa (mm)",
    )
    ax_sales.set_title("Doanh Số Và Lượng Mưa", fontweight="bold", pad=12)
    ax_sales.set_xlabel("Tháng")
    ax_sales.set_ylabel("Doanh số (Triệu VNĐ)", color="darkblue")
    ax_rain.set_ylabel("Lượng mưa (mm)", color="teal")
    ax_sales.tick_params(axis="y", labelcolor="darkblue")
    ax_rain.tick_params(axis="y", labelcolor="teal")
    ax_sales.set_ylim(0, 350)
    ax_rain.set_ylim(0, 350)
    ax_rain.grid(False)
    ax_sales.grid(True, linestyle=":", alpha=0.5)
    lines = sales_line + rain_line
    ax_sales.legend(lines, [line.get_label() for line in lines],
                    loc="upper left", fontsize=8)
    return fig


def main():
    """Lưu cả ba nhiệm vụ cạnh file mã nguồn, ở độ phân giải 300 DPI."""
    charts = (
        (create_sales_plot, "xu_huong_doanhso_2025.png"),
        (create_advertising_plot, "chitieu_quangcao_2025.png"),
        (create_business_report, "baocao_doanhso_2025.png"),
    )
    for create_chart, filename in charts:
        fig = create_chart()
        output_path = OUTPUT_DIR / filename
        try:
            fig.savefig(output_path, dpi=300)
        finally:
            plt.close(fig)
        print(f"Đã lưu: {output_path}")

    highest_budget = max(ad_budget)
    highest_months = [month for month, value in zip(months, ad_budget)
                      if value == highest_budget]
    print(f"Quảng cáo cao nhất: {', '.join(highest_months)} - {highest_budget} Triệu VNĐ")


if __name__ == "__main__":
    main()
