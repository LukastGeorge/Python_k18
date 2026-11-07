"""Chạy các tình huống minh họa của hệ thống quản lý trung tâm."""

from quan_ly_trung_tam import GiangVien, HocVien, QuanLyTrungTam


def main():
    print("1. ĐĂNG KÝ KHÓA HỌC THEO TEST CASE CỦA ĐỀ")
    try:
        hv1 = HocVien("HV01", "Nguyen Van A", "a@gmail.com")
        hv1.dang_ky_khoa_hoc("Python Basic", 1500000)
        hv1.dang_ky_khoa_hoc("Python Basic", 1500000)
        print(hv1.hien_thi_thong_tin())
        print("Khóa học:", hv1.danh_sach_khoa)
        print("Tổng học phí:", hv1.tong_hoc_phi)
    except ValueError as error:
        print("Lỗi validation:", error)
        return

    print("\n2. ĐĂNG KÝ KHÓA MỚI VÀ KIỂM TRA HỌC PHÍ SAI")
    hv1.dang_ky_khoa_hoc("IELTS Foundation", 2000000)
    print("Các khóa đã đăng ký:", sorted(hv1.danh_sach_khoa))
    print("Tổng học phí sau khóa mới:", hv1.tong_hoc_phi)
    for hoc_phi in (0, -500000):
        try:
            hv1.dang_ky_khoa_hoc("English Speaking", hoc_phi)
        except ValueError as error:
            print("Lỗi validation:", error)

    print("\n3. QUẢN LÝ BẰNG DICTIONARY VÀ NẠP CHỒNG TOÁN TỬ")
    hv2 = HocVien("HV02", "Tran Thi B", "b@gmail.com")
    trung_tam = QuanLyTrungTam()
    trung_tam.them_hoc_vien(hv1)
    trung_tam.them_hoc_vien(hv2)
    print("Số học viên:", len(trung_tam))
    print("Tìm HV01:", trung_tam.tim_hoc_vien("HV01"))
    print("Tìm mã không tồn tại:", trung_tam.tim_hoc_vien("HV99"))
    hv_cung_ma = HocVien("HV01", "Ten cap nhat", "moi@gmail.com")
    print("Hai học viên cùng mã:", hv1 == hv_cung_ma)
    print("Hai học viên khác mã:", hv1 == hv2)
    try:
        trung_tam.them_hoc_vien(hv_cung_ma)
    except ValueError as error:
        print("Không thêm mã trùng:", error)

    print("\n4. GIẢNG VIÊN, SUPER VÀ ĐA HÌNH")
    gv = GiangVien("GV01", "Le Van C", "c@gmail.com", "IELTS", 300000)
    gv.luong_theo_gio = 350000
    for thanh_vien in (hv1, gv):
        print(thanh_vien.hien_thi_thong_tin())
    try:
        gv.luong_theo_gio = -1
    except ValueError as error:
        print("Lỗi cập nhật lương:", error)
    print("Lương sau cập nhật không hợp lệ:", gv.luong_theo_gio)


if __name__ == "__main__":
    main()
