"""Chạy pipeline một lần hoặc lặp định kỳ trong terminal hiện tại."""
import argparse
import time
from pathlib import Path
import schedule
from sqlalchemy.exc import SQLAlchemyError
from config import configure_console
from data_pipeline import run_pipeline


def safe_run(csv_path=None, source='csv'):
    try:
        run_pipeline(csv_path, source=source)
        return True
    except (ValueError, OSError, SQLAlchemyError) as error:
        print(f'Lần chạy này thất bại: {error}')
        print('Kiểm tra .env/dữ liệu đầu vào. Lịch đang chạy sẽ thử lại ở lần kế tiếp.')
        return False


def main(argv=None):
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true', help='Chạy một lần rồi thoát.')
    parser.add_argument('--interval', type=float, default=60, help='Số phút giữa các lần chạy; mặc định 60.')
    parser.add_argument('--csv', type=Path, help='Đọc lại CSV này; nếu bỏ trống thì chạy DEMO.')
    parser.add_argument('--source', default='csv')
    args = parser.parse_args(argv)
    if not 0 < args.interval < float('inf'):
        parser.error('--interval phải là số hữu hạn lớn hơn 0.')
    if args.once:
        return 0 if safe_run(args.csv, args.source) else 1
    scheduler = schedule.Scheduler()
    scheduler.every(args.interval).minutes.do(safe_run, args.csv, args.source)
    print(f'Chạy ngay và lặp mỗi {args.interval:g} phút. Giữ terminal mở; Ctrl+C để dừng.')
    try:
        safe_run(args.csv, args.source)
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nĐã dừng lịch chạy.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
