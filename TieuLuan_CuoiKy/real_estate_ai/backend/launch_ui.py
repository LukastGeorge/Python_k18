"""Run the project using its pinned environment, reusing only a compatible UI."""
import argparse
import json
import os
import socket
from threading import Timer
from urllib.request import urlopen
import webbrowser

from .config import configure_console
from .runtime_identity import runtime_revision


def server_info(port):
    try:
        with urlopen(f'http://127.0.0.1:{port}/api/vietnam/info',timeout=1.5) as response:
            return json.load(response)
    except (OSError,ValueError):
        return None


def available(port):
    with socket.socket() as connection:
        try:
            connection.bind(('127.0.0.1',port))
            return True
        except OSError:
            return False


def choose_port(preferred, revision, model_version):
    for port in range(preferred,min(preferred+10,65535)+1):
        info = server_info(port)
        if info and info.get('runtime_revision') == revision and info.get('metadata',{}).get('model_version') == model_version:
            return port,True
        if available(port):
            return port,False
    raise RuntimeError('Chưa có cổng trống. Đóng phiên chạy cũ hoặc chọn --port khác.')


def main(argv=None):
    configure_console()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args(argv)
    if not 1<=args.port<=65535:
        parser.error('Cổng phải từ 1 đến 65535.')
    os.environ['DB_BACKEND']='sqlite'
    try:
        print('Đang kiểm tra môi trường, mô hình Kaggle 2024 và SQLite…',flush=True)
        from .vietnam import load_bundle,FEATURES
        from .config import get_engine
        bundle=load_bundle()
        meta=bundle['metadata']
        if meta['source'].get('revision')!='kaggle-version-8' or meta['features']!=FEATURES:
            raise RuntimeError('Model chưa khớp nguồn Kaggle 2024. Chạy scripts/huan_luyen.cmd để cập nhật.')
        engine=get_engine()
        with engine.connect() as connection:
            connection.exec_driver_sql('SELECT 1')
        engine.dispose()
        port,reuse=choose_port(args.port,runtime_revision(),meta['model_version'])
        url=f'http://127.0.0.1:{port}'
        print(('Dùng phiên đang chạy: ' if reuse else 'Mở ứng dụng tại: ')+url,flush=True)
        if port!=args.port:
            print(f'Cổng {args.port} đang có phiên khác. Dùng cổng {port}; dữ liệu cũ được giữ.',flush=True)
        if args.check_only:
            print('Kiểm tra khởi động thành công.',flush=True)
            return 0
        if reuse:
            if not args.no_browser:
                webbrowser.open(url)
            return 0
        from .web_app import create_app
        app=create_app()
        if not args.no_browser:
            timer=Timer(1.5,webbrowser.open,args=(url,));timer.daemon=True;timer.start()
        print('Giữ cửa sổ này mở khi sử dụng. Ctrl+C để dừng.',flush=True)
        try:
            app.run(host='127.0.0.1',port=port,debug=False,use_reloader=False)
        finally:
            app.extensions['database'].dispose()
        return 0
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print('Không khởi động được: '+str(error),flush=True)
        print('Nếu thiếu thư viện, chạy TieuLuan_CuoiKy\\scripts\\cai_dat.cmd rồi mở lại chay_ui.cmd.',flush=True)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
