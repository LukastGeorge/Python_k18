"""Bài 3.2: Phân tích điểm thi, thời gian học và chuyên ngành bằng Seaborn."""

from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import seaborn as sns


# Ba list cùng chỉ số mô tả một sinh viên, giữ nguyên dữ liệu trong đề.
study_hours = [2, 3, 3, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 11, 12, 12, 13, 14]
exam_scores = [45, 50, 52, 58, 60, 63, 68, 70, 72, 75, 78, 80, 83, 85, 88, 90, 92,
               94, 95, 98]
majors = ["CNTT", "CNTT", "KTPM", "KTPM", "CNTT", "HTTT", "KTPM", "CNTT",
          "HTTT", "CNTT", "KTPM", "CNTT", "HTTT", "CNTT", "KTPM", "HTTT",
          "CNTT", "KTPM", "CNTT", "KTPM"]

MAJOR_ORDER = ["CNTT", "KTPM", "HTTT"]
OUTPUT_DIR = Path(__file__).resolve().parent


def calculate_medians(major_labels, scores):
    """Gom điểm bằng dictionary và tính trung vị từng ngành bằng median()."""
    if len(major_labels) != len(scores):
        raise ValueError("Danh sách chuyên ngành và điểm phải có cùng độ dài!")
    if not scores:
        raise ValueError("Danh sách điểm không được rỗng!")

    grouped_scores = {}
    for major, score in zip(major_labels, scores):
        grouped_scores.setdefault(major, []).append(score)
    return {major: median(values) for major, values in grouped_scores.items()}


def create_histogram():
    """Nhiệm vụ 1: Histogram 6 khoảng có đường KDE và chủ đề whitegrid."""
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    sns.histplot(x=exam_scores, kde=True, bins=6, color="teal", ax=ax)
    ax.set_title("Phân Bố Điểm Thi Lập Trình Python", fontweight="bold", pad=12)
    ax.set_xlabel("Điểm thi")
    ax.set_ylabel("Tần số (Số sinh viên)")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(40, 100)
    return fig


def create_study_scatter():
    """Nhiệm vụ 2: Phân màu quan hệ giờ học và điểm theo chuyên ngành."""
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    sns.scatterplot(
        x=study_hours, y=exam_scores, hue=majors,
        hue_order=MAJOR_ORDER, palette="Set1", s=85, ax=ax,
    )
    ax.set_title("Thời Gian Học Và Điểm Thi", fontweight="bold", pad=12)
    ax.set_xlabel("Thời gian học (Giờ/tuần)")
    ax.set_ylabel("Điểm thi")
    ax.set_ylim(40, 105)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(title="Chuyên ngành", loc="upper left")
    return fig


def create_major_boxplot():
    """Nhiệm vụ 3: So sánh phân bố và ghi trung vị lên từng hộp."""
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    medians = calculate_medians(majors, exam_scores)
    fig, ax = plt.subplots(figsize=(8, 4.5), layout="constrained")
    sns.boxplot(
        x=majors, y=exam_scores, hue=majors,
        order=MAJOR_ORDER, hue_order=MAJOR_ORDER, palette="Set1",
        dodge=False, legend=False, width=0.5, ax=ax,
    )
    for index, major in enumerate(MAJOR_ORDER):
        ax.annotate(
            f"Trung vị: {medians[major]:g}", xy=(index, medians[major]),
            xytext=(0, 7), textcoords="offset points", ha="center",
            fontsize=10, fontweight="bold",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85},
        )
    ax.set_xticks(range(len(MAJOR_ORDER)),
                  [f"{major}\n(n = {majors.count(major)})" for major in MAJOR_ORDER])
    ax.set_title("Phân Bố Điểm Thi Theo Chuyên Ngành", fontweight="bold", pad=12)
    ax.set_xlabel("Chuyên ngành")
    ax.set_ylabel("Điểm thi")
    ax.set_ylim(40, 105)
    return fig


def main():
    """Xuất ba biểu đồ và kết luận dựa trên trung vị được tính từ dữ liệu."""
    charts = (
        (create_histogram, "phanbo_diem_python.png"),
        (create_study_scatter, "thoigian_hoc_va_diem.png"),
        (create_major_boxplot, "phantich_diem_seaborn.png"),
    )
    for create_chart, filename in charts:
        fig = create_chart()
        output_path = OUTPUT_DIR / filename
        try:
            fig.savefig(output_path, dpi=300)
        finally:
            plt.close(fig)
        print(f"Đã lưu: {output_path}")

    medians = calculate_medians(majors, exam_scores)
    print("\nTrung vị điểm theo chuyên ngành:")
    for major, value in medians.items():
        print(f"  {major}: {value:g} điểm (n = {majors.count(major)})")
    highest = max(medians.values())
    leaders = [major for major, value in medians.items() if value == highest]
    print(f"Trung vị cao nhất: {', '.join(leaders)} - {highest:g} điểm.")
    print("Nhận xét áp dụng cho 20 sinh viên trong bộ dữ liệu mẫu của đề.")


if __name__ == "__main__":
    main()
