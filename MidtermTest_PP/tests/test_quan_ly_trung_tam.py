"""Kiểm thử yêu cầu trong đề và các thao tác có thể làm sai trạng thái."""

from contextlib import redirect_stdout
from io import StringIO
import unittest

from src.phan_tich_bo_nho import main as chay_phan_tich_bo_nho
from src.quan_ly_trung_tam import GiangVien, HocVien, Nguoi, QuanLyTrungTam


class PhanTichTests(unittest.TestCase):
    def test_nam_dong_ket_qua_cau_1_1(self):
        output = StringIO()
        with redirect_stdout(output):
            chay_phan_tich_bo_nho()
        self.assertEqual(output.getvalue().splitlines(), [
            "1. list_a[0] = 99",
            "2. list_a[1] = [20, 30, 40]",
            "3. list_a[2] = {'a': 1, 'b': 2}",
            "4. list_b is list_a: True",
            "5. list_c is list_a: False",
        ])


class HocVienTests(unittest.TestCase):
    def setUp(self):
        self.hv = HocVien("HV01", "Nguyen Van A", "a@gmail.com")

    def test_thong_tin_ke_thua_va_str(self):
        self.assertIsInstance(self.hv, Nguoi)
        self.assertEqual(str(self.hv), "[HV01] Nguyen Van A")
        for value in ("HV01", "Nguyen Van A", "a@gmail.com"):
            self.assertIn(value, self.hv.hien_thi_thong_tin())
        self.assertEqual(self.hv.tong_hoc_phi, 0)
        self.assertIsInstance(self.hv.danh_sach_khoa, set)

    def test_dang_ky_trung_khong_thu_hoc_phi_lan_hai(self):
        self.assertTrue(self.hv.dang_ky_khoa_hoc("Python Basic", 1500000))
        self.assertFalse(self.hv.dang_ky_khoa_hoc("Python Basic", 1500000))
        self.assertFalse(self.hv.dang_ky_khoa_hoc("Python Basic", 2000000))
        self.assertEqual(self.hv.danh_sach_khoa, {"Python Basic"})
        self.assertEqual(self.hv.tong_hoc_phi, 1500000)

    def test_nhieu_khoa_hoc_cong_dung_hoc_phi(self):
        self.hv.dang_ky_khoa_hoc("Python Basic", 1500000)
        self.hv.dang_ky_khoa_hoc("IELTS Foundation", 2000000)
        self.assertEqual(len(self.hv.danh_sach_khoa), 2)
        self.assertEqual(self.hv.tong_hoc_phi, 3500000)

    def test_hoc_phi_khong_duong_dung_thong_bao_de(self):
        self.hv.dang_ky_khoa_hoc("Python Basic", 1500000)
        for course in ("Python Basic", "IELTS"):
            for fee in (0, -1):
                with self.subTest(course=course, fee=fee):
                    with self.assertRaisesRegex(ValueError, "^Học phí phải lớn hơn 0!$"):
                        self.hv.dang_ky_khoa_hoc(course, fee)
        self.assertEqual(self.hv.tong_hoc_phi, 1500000)
        self.assertEqual(self.hv.danh_sach_khoa, {"Python Basic"})

    def test_hoc_phi_sai_kieu_va_khong_huu_han(self):
        for fee in ("100", None, True, float("nan"), float("inf")):
            with self.subTest(fee=fee):
                with self.assertRaises((TypeError, ValueError)):
                    self.hv.dang_ky_khoa_hoc("IELTS", fee)
                self.assertEqual(self.hv.danh_sach_khoa, set())
                self.assertEqual(self.hv.tong_hoc_phi, 0)

    def test_ten_khoa_hoc_duoc_kiem_tra(self):
        for name in ("", "   ", None, 123):
            with self.subTest(name=name):
                with self.assertRaises((TypeError, ValueError)):
                    self.hv.dang_ky_khoa_hoc(name, 100)
        self.hv.dang_ky_khoa_hoc("  IELTS  ", 100)
        self.assertFalse(self.hv.dang_ky_khoa_hoc("IELTS", 100))
        self.assertEqual(self.hv.tong_hoc_phi, 100)

    def test_du_lieu_thuoc_rieng_tung_hoc_vien(self):
        other = HocVien("HV02", "B", "b@gmail.com")
        self.hv.dang_ky_khoa_hoc("IELTS", 100)
        self.assertEqual(other.danh_sach_khoa, set())
        self.assertEqual(other.tong_hoc_phi, 0)

    def test_property_tong_hoc_phi_va_private(self):
        self.hv.tong_hoc_phi = 1500000
        self.assertEqual(self.hv.tong_hoc_phi, 1500000)
        for value in (-1, float("inf"), float("nan"), True, "100"):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    self.hv.tong_hoc_phi = value
                self.assertEqual(self.hv.tong_hoc_phi, 1500000)
        with self.assertRaises(AttributeError):
            getattr(self.hv, "__tong_hoc_phi")
        self.hv.tong_hoc_phi = 0
        self.assertEqual(self.hv.tong_hoc_phi, 0)

    def test_tran_tong_hoc_phi_khong_them_khoa(self):
        self.hv.dang_ky_khoa_hoc("A", 1e308)
        with self.assertRaises(ValueError):
            self.hv.dang_ky_khoa_hoc("B", 1e308)
        self.assertEqual(self.hv.tong_hoc_phi, 1e308)
        self.assertEqual(self.hv.danh_sach_khoa, {"A"})

    def test_so_sanh_theo_ma_id(self):
        same = HocVien("HV01", "Ten khac", "khac@gmail.com")
        different = HocVien("HV02", "Nguyen Van A", "a@gmail.com")
        self.assertEqual(self.hv, same)
        self.assertNotEqual(self.hv, different)
        self.assertNotEqual(self.hv, "HV01")
        self.assertNotEqual(self.hv, None)
        self.assertNotEqual(self.hv, Nguoi("HV01", "A", "a@gmail.com"))


class GiangVienTests(unittest.TestCase):
    def test_super_va_thong_tin_bo_sung(self):
        gv = GiangVien("GV01", "Le Van C", "c@gmail.com", "IELTS", 300000)
        self.assertIsInstance(gv, Nguoi)
        for value in ("GV01", "Le Van C", "c@gmail.com", "IELTS", "300000"):
            self.assertIn(value, gv.hien_thi_thong_tin())
        self.assertEqual(str(gv), "[GV01] Le Van C")

    def test_luong_co_getter_setter_va_validation(self):
        gv = GiangVien("GV01", "C", "c@gmail.com", "IELTS", 0)
        gv.luong_theo_gio = 350000
        self.assertEqual(gv.luong_theo_gio, 350000)
        for value in (-1, "300000", True, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    gv.luong_theo_gio = value
                self.assertEqual(gv.luong_theo_gio, 350000)
        with self.assertRaises(AttributeError):
            getattr(gv, "__luong_theo_gio")

    def test_constructor_tu_choi_luong_am(self):
        with self.assertRaises(ValueError):
            GiangVien("GV01", "C", "c@gmail.com", "IELTS", -1)


class QuanLyTests(unittest.TestCase):
    def test_them_tim_len_va_ma_khong_ton_tai(self):
        manager = QuanLyTrungTam()
        self.assertEqual(len(manager), 0)
        self.assertIsNone(manager.tim_hoc_vien("HV99"))
        hv = HocVien("HV01", "A", "a@gmail.com")
        manager.them_hoc_vien(hv)
        self.assertEqual(len(manager), 1)
        self.assertIs(manager.tim_hoc_vien("HV01"), hv)
        self.assertIs(manager.ds_hoc_vien["HV01"], hv)

    def test_ma_trung_khong_ghi_de_hoc_vien_cu(self):
        manager = QuanLyTrungTam()
        original = HocVien("HV01", "A", "a@gmail.com")
        original.dang_ky_khoa_hoc("IELTS", 100)
        manager.them_hoc_vien(original)
        with self.assertRaises(ValueError):
            manager.them_hoc_vien(HocVien("HV01", "B", "b@gmail.com"))
        self.assertEqual(len(manager), 1)
        self.assertIs(manager.tim_hoc_vien("HV01"), original)
        self.assertEqual(manager.tim_hoc_vien("HV01").tong_hoc_phi, 100)

    def test_them_sai_kieu_va_tach_biet_cac_trung_tam(self):
        manager, other = QuanLyTrungTam(), QuanLyTrungTam()
        with self.assertRaises(TypeError):
            manager.them_hoc_vien("HV01")
        manager.them_hoc_vien(HocVien("HV01", "A", "a@gmail.com"))
        self.assertEqual(len(other), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
