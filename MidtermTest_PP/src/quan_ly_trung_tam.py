"""Hệ thống quản lý học viên, giảng viên và đăng ký khóa học."""

import math


def _kiem_tra_so(gia_tri, ten_truong):
    """Chỉ nhận số int/float hữu hạn, loại bool dù bool kế thừa int."""
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
        raise TypeError(f"{ten_truong} phải là số!")
    if isinstance(gia_tri, float) and not math.isfinite(gia_tri):
        raise ValueError(f"{ten_truong} phải là số hữu hạn!")


class Nguoi:
    """Lớp cơ sở lưu thông tin chung của thành viên trung tâm."""

    def __init__(self, ma_id, ho_ten, email):
        self.ma_id = ma_id
        self.ho_ten = ho_ten
        self.email = email

    def hien_thi_thong_tin(self):
        """Trả về chuỗi để nơi gọi chủ động in hoặc xử lý tiếp."""
        return f"Mã: {self.ma_id} | Họ tên: {self.ho_ten} | Email: {self.email}"

    def __str__(self):
        return f"[{self.ma_id}] {self.ho_ten}"


class HocVien(Nguoi):
    """Học viên có tập khóa học riêng và học phí được đóng gói."""

    def __init__(self, ma_id, ho_ten, email):
        super().__init__(ma_id, ho_ten, email)
        self.danh_sach_khoa = set()
        self.__tong_hoc_phi = 0

    @property
    def tong_hoc_phi(self):
        """Getter cho phép đọc hv.tong_hoc_phi theo mẫu test của đề."""
        return self.__tong_hoc_phi

    @tong_hoc_phi.setter
    def tong_hoc_phi(self, gia_tri):
        """Setter chỉ cho phép cập nhật tổng học phí không âm, hữu hạn."""
        _kiem_tra_so(gia_tri, "Tổng học phí")
        if gia_tri < 0:
            raise ValueError("Tổng học phí không được âm!")
        self.__tong_hoc_phi = gia_tri

    def dang_ky_khoa_hoc(self, ten_khoa, hoc_phi):
        """Đăng ký mới trả True; trùng tên trả False và không thu tiền lại."""
        _kiem_tra_so(hoc_phi, "Học phí")
        if hoc_phi <= 0:
            raise ValueError("Học phí phải lớn hơn 0!")
        if not isinstance(ten_khoa, str):
            raise TypeError("Tên khóa học phải là chuỗi!")
        ten_khoa = ten_khoa.strip()
        if not ten_khoa:
            raise ValueError("Tên khóa học không được rỗng!")

        if ten_khoa in self.danh_sach_khoa:
            return False

        # Kiểm tra tổng mới qua setter trước khi thay đổi danh sách khóa.
        self.tong_hoc_phi = self.tong_hoc_phi + hoc_phi
        self.danh_sach_khoa.add(ten_khoa)
        return True

    def hien_thi_thong_tin(self):
        return (
            f"{super().hien_thi_thong_tin()}"
            f" | Số khóa: {len(self.danh_sach_khoa)}"
            f" | Tổng học phí: {self.tong_hoc_phi} VNĐ"
        )

    def __eq__(self, other):
        """Hai đối tượng HocVien bằng nhau khi có cùng mã định danh."""
        if not isinstance(other, HocVien):
            return NotImplemented
        return self.ma_id == other.ma_id


class GiangVien(Nguoi):
    """Giảng viên bổ sung chuyên môn và lương giờ được kiểm tra qua property."""

    def __init__(self, ma_id, ho_ten, email, chuyen_mon, luong_theo_gio):
        super().__init__(ma_id, ho_ten, email)
        self.chuyen_mon = chuyen_mon
        self.luong_theo_gio = luong_theo_gio

    @property
    def luong_theo_gio(self):
        return self.__luong_theo_gio

    @luong_theo_gio.setter
    def luong_theo_gio(self, gia_tri):
        _kiem_tra_so(gia_tri, "Lương theo giờ")
        if gia_tri < 0:
            raise ValueError("Lương theo giờ không được âm!")
        self.__luong_theo_gio = gia_tri

    def hien_thi_thong_tin(self):
        """Tái sử dụng thông tin chung, rồi bổ sung dữ liệu giảng viên."""
        thong_tin_chung = super().hien_thi_thong_tin()
        return (
            f"{thong_tin_chung} | Chuyên môn: {self.chuyen_mon}"
            f" | Lương theo giờ: {self.luong_theo_gio} VNĐ"
        )


class QuanLyTrungTam:
    """Quản lý học viên theo mã bằng dictionary để tra cứu nhanh."""

    def __init__(self):
        self.ds_hoc_vien = {}

    def them_hoc_vien(self, hoc_vien):
        """Không ghi đè thông tin học viên đã có cùng mã trong hệ thống."""
        if not isinstance(hoc_vien, HocVien):
            raise TypeError("Đối tượng thêm vào phải là HocVien!")
        if hoc_vien.ma_id in self.ds_hoc_vien:
            raise ValueError(f"Mã học viên đã tồn tại: {hoc_vien.ma_id}")
        self.ds_hoc_vien[hoc_vien.ma_id] = hoc_vien

    def tim_hoc_vien(self, ma_id):
        """Trả về HocVien tìm được hoặc None nếu không tồn tại."""
        return self.ds_hoc_vien.get(ma_id)

    def __len__(self):
        return len(self.ds_hoc_vien)
