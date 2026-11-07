"""Kiểm thử dữ liệu, thống kê và nội dung biểu đồ của Lab5."""

import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

import ex01_matplotlib as business
import ex02_seaborn as students


class StatisticsTests(unittest.TestCase):
    def test_business_sample_data(self):
        self.assertEqual(business.months, [f"T{i}" for i in range(1, 13)])
        self.assertEqual(business.sales,
                         [120, 135, 160, 190, 210, 250, 230, 220, 195, 170, 200, 280])
        self.assertEqual(business.ad_budget,
                         [10, 12, 15, 20, 22, 30, 25, 24, 18, 15, 22, 35])
        self.assertEqual(business.rainfall,
                         [20, 15, 30, 80, 150, 220, 250, 210, 180, 120, 50, 25])

    def test_medians_and_group_sizes(self):
        self.assertEqual(len(students.study_hours), 20)
        self.assertEqual(len(students.exam_scores), 20)
        self.assertEqual(len(students.majors), 20)
        self.assertEqual(
            students.calculate_medians(students.majors, students.exam_scores),
            {"CNTT": 75, "KTPM": 78, "HTTT": 77.5},
        )
        self.assertEqual({m: students.majors.count(m) for m in students.MAJOR_ORDER},
                         {"CNTT": 9, "KTPM": 7, "HTTT": 4})

    def test_median_handles_unsorted_even_and_odd_groups(self):
        self.assertEqual(
            students.calculate_medians(["A", "B", "A", "B", "A"],
                                       [90, 40, 10, 80, 50]),
            {"A": 50, "B": 60},
        )

    def test_median_rejects_empty_or_mismatched_data(self):
        for labels, scores in (([], []), (["A"], []), ([], [50])):
            with self.subTest(labels=labels, scores=scores):
                with self.assertRaises(ValueError):
                    students.calculate_medians(labels, scores)


class ChartTests(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_sales_line_contains_all_months_and_required_style(self):
        fig = business.create_sales_plot()
        ax = fig.axes[0]
        line = ax.lines[0]
        self.assertEqual(list(line.get_xdata()), business.months)
        self.assertEqual(list(line.get_ydata()), business.sales)
        self.assertEqual(to_rgba(line.get_color()), to_rgba("darkblue"))
        self.assertEqual(line.get_linestyle(), "--")
        self.assertEqual(line.get_marker(), "o")
        self.assertEqual(ax.get_title(), "Xu Hướng Doanh Số Năm 2025")
        self.assertTrue(any(line.get_visible() for line in ax.get_xgridlines()))

    def test_advertising_bars_highlight_and_annotate_maximum(self):
        fig = business.create_advertising_plot()
        ax = fig.axes[0]
        self.assertEqual([bar.get_height() for bar in ax.patches], business.ad_budget)
        self.assertEqual([bar.get_facecolor() for bar in ax.patches],
                         [to_rgba("skyblue")] * 11 + [to_rgba("crimson")])
        self.assertEqual(len(ax.texts), 1)
        self.assertIn("T12", ax.texts[0].get_text())
        self.assertIn("35", ax.texts[0].get_text())

    def test_report_preserves_data_units_and_figure_size(self):
        fig = business.create_business_report()
        self.assertEqual(list(fig.get_size_inches()), [12, 4])
        # Hai ô subplot; ô thứ hai có thêm một Axes cho trục Y lượng mưa.
        self.assertEqual(len(fig.axes), 3)
        scatter, sales_ax, rain_ax = fig.axes
        self.assertEqual(scatter.collections[0].get_offsets().tolist(),
                         [list(pair) for pair in zip(business.ad_budget, business.sales)])
        self.assertEqual(list(sales_ax.lines[0].get_ydata()), business.sales)
        self.assertEqual(list(rain_ax.lines[0].get_ydata()), business.rainfall)
        self.assertIn("Triệu VNĐ", sales_ax.get_ylabel())
        self.assertIn("mm", rain_ax.get_ylabel())
        self.assertEqual(len(sales_ax.get_legend().get_texts()), 2)

    def test_histogram_has_six_bins_twenty_students_and_kde(self):
        fig = students.create_histogram()
        ax = fig.axes[0]
        self.assertEqual(len(ax.patches), 6)
        self.assertEqual(sum(bar.get_height() for bar in ax.patches), 20)
        self.assertEqual(len(ax.lines), 1)
        self.assertGreater(len(ax.lines[0].get_xdata()), 20)
        self.assertEqual(ax.get_title(), "Phân Bố Điểm Thi Lập Trình Python")

    def test_study_scatter_has_twenty_points_and_three_majors(self):
        fig = students.create_study_scatter()
        ax = fig.axes[0]
        points = ax.collections[0]
        self.assertEqual(points.get_offsets().tolist(),
                         [list(pair) for pair in zip(students.study_hours,
                                                    students.exam_scores)])
        self.assertEqual([text.get_text() for text in ax.get_legend().get_texts()],
                         students.MAJOR_ORDER)
        colors = points.get_facecolors()
        for major in students.MAJOR_ORDER:
            group_colors = {tuple(colors[i]) for i, value in enumerate(students.majors)
                            if value == major}
            self.assertEqual(len(group_colors), 1)
        self.assertEqual(len({tuple(color) for color in colors}), 3)

    def test_boxplot_has_three_groups_and_correct_median_labels(self):
        fig = students.create_major_boxplot()
        ax = fig.axes[0]
        self.assertEqual(len(ax.patches), 3)
        self.assertEqual([text.get_text() for text in ax.texts],
                         ["Trung vị: 75", "Trung vị: 78", "Trung vị: 77.5"])
        self.assertEqual([tick.get_text() for tick in ax.get_xticklabels()],
                         ["CNTT\n(n = 9)", "KTPM\n(n = 7)", "HTTT\n(n = 4)"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
