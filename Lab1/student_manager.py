INPUT_FILE = "students_input.txt"
OUTPUT_FILE = "report_output.txt"

def read_students_from_file(filepath):

    students = []
    errors = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[LỖI] Không tìm thấy file dữ liệu: '{filepath}'")
        return students, errors
    except IOError as e:
        print(f"[LỖI] Không thể đọc file '{filepath}': {e}")
        return students, errors

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue  # bỏ qua dòng trống

        parts = [p.strip() for p in line.split(",")]

        if len(parts) != 5:
            errors.append(f"Dòng {idx}: sai định dạng (cần 5 trường) -> '{line}'")
            continue

        ma_sv, ho_ten, cc_raw, gk_raw, ck_raw = parts

        try:
            diem_cc = float(cc_raw)
            diem_gk = float(gk_raw)
            diem_ck = float(ck_raw)

            # Kiểm tra khoảng điểm hợp lệ (0 - 10)
            if not all(0 <= d <= 10 for d in (diem_cc, diem_gk, diem_ck)):
                errors.append(f"Dòng {idx}: điểm nằm ngoài khoảng [0, 10] -> '{line}'")
                continue

        except ValueError:
            errors.append(f"Dòng {idx}: lỗi ép kiểu số điểm -> '{line}'")
            continue

        students.append({
            "ma_sv": ma_sv,
            "ho_ten": ho_ten,
            "diem_cc": diem_cc,
            "diem_gk": diem_gk,
            "diem_ck": diem_ck,
        })

    return students, errors

def calc_diem_tong_ket(diem_cc, diem_gk, diem_ck):
    """Điểm tổng kết hệ 10 = CC*0.1 + GK*0.3 + CK*0.6"""
    return diem_cc * 0.1 + diem_gk * 0.3 + diem_ck * 0.6


def xep_loai_hoc_luc(diem_tong_ket):
    """Xếp loại học lực bằng hàm rẽ nhánh (if - elif - else)."""
    if diem_tong_ket >= 9.0:
        return "A"
    elif diem_tong_ket >= 7.5:
        return "B"
    elif diem_tong_ket >= 6.0:
        return "C"
    elif diem_tong_ket >= 5.0:
        return "D"
    else:
        return "F"


def process_students(students):
    """Bổ sung điểm tổng kết và xếp loại cho từng sinh viên trong danh sách."""
    for sv in students:
        tong_ket = calc_diem_tong_ket(sv["diem_cc"], sv["diem_gk"], sv["diem_ck"])
        sv["diem_tong_ket"] = round(tong_ket, 2)
        sv["xep_loai"] = xep_loai_hoc_luc(tong_ket)
    return students



def sort_by_diem_tong_ket_desc(students):
    """Sắp xếp sinh viên theo điểm tổng kết giảm dần (dùng sorted + lambda)."""
    return sorted(students, key=lambda sv: sv["diem_tong_ket"], reverse=True)


def loc_sinh_vien_gioi_xuat_sac(students):
    """List comprehension: lọc sinh viên đạt loại Xuất sắc/Giỏi (hạng A, B)."""
    return [sv for sv in students if sv["xep_loai"] in ("A", "B")]


def thong_ke_lop(students):
    """
    Tính điểm trung bình chung của lớp và tỷ lệ sinh viên đạt yêu cầu
    (điểm tổng kết >= 5.0).
    """
    if not students:
        return 0.0, 0.0, 0

    tong_diem = sum(sv["diem_tong_ket"] for sv in students)
    diem_tb_lop = tong_diem / len(students)

    # Dict/List comprehension để lọc SV đạt yêu cầu
    sv_dat = [sv for sv in students if sv["diem_tong_ket"] >= 5.0]
    ty_le_dat = len(sv_dat) / len(students) * 100

    return diem_tb_lop, ty_le_dat, len(sv_dat)


def dem_so_luong_theo_loai(students):
    """Dict comprehension: đếm số lượng sinh viên theo từng xếp loại."""
    return {
        loai: len([sv for sv in students if sv["xep_loai"] == loai])
        for loai in ("A", "B", "C", "D", "F")
    }


def build_report(students, errors):
    """Xây dựng chuỗi báo cáo có căn chỉnh định dạng đẹp mắt."""
    lines = []
    sep = "=" * 88

    lines.append(sep)
    lines.append("BÁO CÁO QUẢN LÝ & PHÂN TÍCH ĐIỂM SINH VIÊN".center(88))
    lines.append(sep)

    if errors:
        lines.append("\n[CẢNH BÁO] Các dòng dữ liệu bị bỏ qua do lỗi:")
        for e in errors:
            lines.append(f"   - {e}")

    if not students:
        lines.append("\nKhông có dữ liệu sinh viên hợp lệ để thống kê.")
        return "\n".join(lines)

    students = process_students(students)
    sorted_students = sort_by_diem_tong_ket_desc(students)

    # ---- Bảng danh sách sinh viên (theo thứ hạng điểm tổng kết) ----
    header = f"{'Hạng':<5}{'Mã SV':<10}{'Họ Tên':<22}{'CC':>6}{'GK':>6}{'CK':>6}{'Tổng Kết':>10}{'Xếp Loại':>10}"
    lines.append("\n" + "-" * 88)
    lines.append("DANH SÁCH SINH VIÊN (Sắp xếp theo Điểm Tổng Kết giảm dần)")
    lines.append("-" * 88)
    lines.append(header)
    lines.append("-" * 88)

    for rank, sv in enumerate(sorted_students, start=1):
        lines.append(
            f"{rank:<5}{sv['ma_sv']:<10}{sv['ho_ten']:<22}"
            f"{sv['diem_cc']:>6.1f}{sv['diem_gk']:>6.1f}{sv['diem_ck']:>6.1f}"
            f"{sv['diem_tong_ket']:>10.2f}{sv['xep_loai']:>10}"
        )
    lines.append("-" * 88)

    # ---- Thủ khoa ----
    thu_khoa = sorted_students[0]
    lines.append(
        f"\n>> THỦ KHOA CỦA LỚP: {thu_khoa['ho_ten']} ({thu_khoa['ma_sv']}) "
        f"- Điểm tổng kết: {thu_khoa['diem_tong_ket']:.2f} - Xếp loại: {thu_khoa['xep_loai']}"
    )

    # ---- Danh sách Giỏi/Xuất sắc ----
    gioi_xuat_sac = loc_sinh_vien_gioi_xuat_sac(sorted_students)
    lines.append(f"\n>> DANH SÁCH SINH VIÊN XUẤT SẮC/GIỎI (Hạng A, B) - Tổng số: {len(gioi_xuat_sac)}")
    lines.append("-" * 88)
    if gioi_xuat_sac:
        lines.append(f"{'Mã SV':<10}{'Họ Tên':<22}{'Tổng Kết':>10}{'Xếp Loại':>10}")
        lines.append("-" * 52)
        for sv in gioi_xuat_sac:
            lines.append(
                f"{sv['ma_sv']:<10}{sv['ho_ten']:<22}"
                f"{sv['diem_tong_ket']:>10.2f}{sv['xep_loai']:>10}"
            )
    else:
        lines.append("Không có sinh viên nào đạt loại Xuất sắc/Giỏi.")

    # ---- Thống kê chung của lớp ----
    diem_tb_lop, ty_le_dat, so_luong_dat = thong_ke_lop(sorted_students)
    so_luong_theo_loai = dem_so_luong_theo_loai(sorted_students)

    lines.append("\n" + "=" * 88)
    lines.append("THỐNG KÊ CHUNG CỦA LỚP".center(88))
    lines.append("=" * 88)
    lines.append(f"{'Tổng số sinh viên (hợp lệ)':<45}: {len(sorted_students)}")
    lines.append(f"{'Điểm trung bình chung của lớp':<45}: {diem_tb_lop:.2f}")
    lines.append(f"{'Số SV đạt yêu cầu (>= 5.0)':<45}: {so_luong_dat}")
    lines.append(f"{'Tỷ lệ SV đạt yêu cầu':<45}: {ty_le_dat:.2f}%")

    lines.append("\n" + "-" * 40)
    lines.append("Phân bố xếp loại học lực:")
    lines.append("-" * 40)
    for loai in ("A", "B", "C", "D", "F"):
        so_luong = so_luong_theo_loai[loai]
        ty_le = (so_luong / len(sorted_students) * 100) if sorted_students else 0
        lines.append(f"  Loại {loai:<3}: {so_luong:>3} SV   ({ty_le:>5.1f}%)")

    lines.append(sep)
    return "\n".join(lines)


def nhap_diem_hop_le(ten_diem):
    """
    Yêu cầu người dùng nhập một điểm số, lặp lại đến khi hợp lệ (0-10).
    Có xử lý ngoại lệ khi ép kiểu float thất bại.
    """
    while True:
        gia_tri = input(f"    Nhập {ten_diem} (0-10): ").strip()
        try:
            diem = float(gia_tri)
            if 0 <= diem <= 10:
                return diem
            else:
                print("    [LỖI] Điểm phải nằm trong khoảng từ 0 đến 10. Vui lòng nhập lại.")
        except ValueError:
            print(f"    [LỖI] '{gia_tri}' không phải là số hợp lệ. Vui lòng nhập lại.")


def ghi_danh_sach_ra_file(students, filepath):
    """
    Ghi danh sách sinh viên (list[dict]) ra file theo định dạng CSV gốc.
    Dùng chung cho chức năng nhập tay và xóa sinh viên.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            for sv in students:
                f.write(f"{sv['ma_sv']},{sv['ho_ten']},{sv['diem_cc']},{sv['diem_gk']},{sv['diem_ck']}\n")
        return True
    except IOError as e:
        print(f"[LỖI] Không thể ghi file '{filepath}': {e}")
        return False


def tim_sinh_vien_theo_ma(students, ma_sv):
    """Tìm sinh viên theo Mã SV (không phân biệt hoa thường). Trả về dict hoặc None."""
    ma_sv_norm = ma_sv.strip().lower()
    for sv in students:
        if sv["ma_sv"].strip().lower() == ma_sv_norm:
            return sv
    return None


def xoa_sinh_vien():
    """Chức năng xóa sinh viên khỏi file dữ liệu"""
    students, errors = read_students_from_file(INPUT_FILE)

    if not students:
        print(f"\n[THÔNG BÁO] Không có sinh viên nào trong '{INPUT_FILE}' để xóa.")
        return students, errors

    print(f"\nDanh sách sinh viên hiện có trong '{INPUT_FILE}':")
    print("-" * 40)
    for sv in students:
        print(f"  {sv['ma_sv']:<10} - {sv['ho_ten']}")
    print("-" * 40)

    while True:
        ma_sv_xoa = input("\nNhập Mã SV cần xóa (để trống để dừng): ").strip()

        if ma_sv_xoa == "":
            break

        sv_can_xoa = tim_sinh_vien_theo_ma(students, ma_sv_xoa)

        if sv_can_xoa is None:
            print(f"[LỖI] Không tìm thấy sinh viên có Mã SV '{ma_sv_xoa}'. Vui lòng thử lại.")
            continue

        xac_nhan = input(
            f"Bạn có chắc muốn xóa '{sv_can_xoa['ho_ten']}' ({sv_can_xoa['ma_sv']}) không? (y/n): "
        ).strip().lower()

        if xac_nhan == "y":
            students.remove(sv_can_xoa)
            print(f"[OK] Đã xóa sinh viên '{sv_can_xoa['ho_ten']}' ({sv_can_xoa['ma_sv']}).")
        else:
            print("Đã hủy thao tác xóa.")

        tiep_tuc = input("Bạn có muốn xóa thêm sinh viên khác không? (y/n): ").strip().lower()
        if tiep_tuc != "y":
            break

    if ghi_danh_sach_ra_file(students, INPUT_FILE):
        print(f"\n[OK] Đã cập nhật và lưu lại '{INPUT_FILE}' ({len(students)} sinh viên còn lại).")

    return students, errors


def nhap_sinh_vien_tu_ban_phim():
    """Cho phép người dùng nhập danh sách sinh viên trực tiếp từ bàn phím."""
    students = []

    try:
        so_luong = int(input("Nhập số lượng sinh viên cần nhập: ").strip())
    except ValueError:
        print("[LỖI] Số lượng không hợp lệ, mặc định dùng 0 sinh viên.")
        so_luong = 0

    for i in range(1, so_luong + 1):
        print(f"\n--- Nhập thông tin sinh viên thứ {i}/{so_luong} ---")
        ma_sv = input("    Nhập Mã SV: ").strip()
        ho_ten = input("    Nhập Họ tên: ").strip()
        diem_cc = nhap_diem_hop_le("Điểm CC")
        diem_gk = nhap_diem_hop_le("Điểm GK")
        diem_ck = nhap_diem_hop_le("Điểm CK")

        students.append({
            "ma_sv": ma_sv,
            "ho_ten": ho_ten,
            "diem_cc": diem_cc,
            "diem_gk": diem_gk,
            "diem_ck": diem_ck,
        })

    # Hỏi có muốn lưu lại vào file students_input.txt để dùng cho lần sau không
    if students:
        luu = input(f"\nBạn có muốn lưu danh sách này vào '{INPUT_FILE}' không? (y/n): ").strip().lower()
        if luu == "y":
            if ghi_danh_sach_ra_file(students, INPUT_FILE):
                print(f"[OK] Đã lưu vào '{INPUT_FILE}'.")

    return students


def write_report(report_text, filepath):
    """Ghi báo cáo ra file, có xử lý ngoại lệ."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"\n[OK] Đã ghi báo cáo thành công vào file: '{filepath}'")
    except IOError as e:
        print(f"[LỖI] Không thể ghi báo cáo ra file '{filepath}': {e}")


def main():
    print("=" * 50)
    print("   HỆ THỐNG QUẢN LÝ ĐIỂM SINH VIÊN")
    print("=" * 50)
    print("1. Đọc dữ liệu từ file 'students_input.txt'")
    print("2. Nhập dữ liệu trực tiếp từ bàn phím")
    print("3. Xóa sinh viên khỏi file dữ liệu")

    lua_chon = input("Chọn (1/2/3): ").strip()

    errors = []
    if lua_chon == "2":
        students = nhap_sinh_vien_tu_ban_phim()
    elif lua_chon == "3":
        students, errors = xoa_sinh_vien()
    else:
        print(f"\nĐang đọc dữ liệu từ '{INPUT_FILE}' ...\n")
        students, errors = read_students_from_file(INPUT_FILE)

    report_text = build_report(students, errors)

    # Hiển thị ra màn hình
    print(report_text)

    # Ghi ra file
    write_report(report_text, OUTPUT_FILE)


if __name__ == "__main__":
    main()