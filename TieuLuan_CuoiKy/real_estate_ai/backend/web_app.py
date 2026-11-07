"""Giao diện web và JSON API dùng chung database với pipeline."""
import argparse
from datetime import datetime, timezone
from threading import Lock, Timer
import os
import webbrowser

import pandas as pd
from flask import Flask, jsonify, render_template, request
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from .config import ROOT, MODEL_PATH, configure_console, get_engine
from .data_pipeline import clean_data, run_pipeline
from .database import metadata, records, save_records
from .model_inference import RealEstateAI


def serialize_record(row):
    result = dict(row)
    timestamp = result.get('updated_at')
    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        result['updated_at'] = timestamp.isoformat()
    return result


def create_app(*, engine=None, model_path=MODEL_PATH, kingcounty_model_path=None, vietnam_model_path=None):
    app = Flask(__name__, template_folder=str(ROOT / 'frontend' / 'templates'),
                static_folder=str(ROOT / 'frontend' / 'static'), static_url_path='/static')
    trusted_hosts = os.getenv('WEB_TRUSTED_HOSTS', 'localhost,127.0.0.1,[::1]')
    app.config.update(MAX_CONTENT_LENGTH=16_384,
                      TRUSTED_HOSTS=[host.strip() for host in trusted_hosts.split(',') if host.strip()])
    app.json.ensure_ascii = False
    db = engine if engine is not None else get_engine()
    app.extensions['database'] = db
    schema_lock = Lock()
    schema_ready = False

    def ensure_tables():
        nonlocal schema_ready
        with schema_lock:
            if not schema_ready:
                metadata.create_all(db)
                schema_ready = True

    @app.before_request
    def check_json_request():
        if request.path.startswith('/api/') and request.method == 'POST':
            if not request.is_json:
                return jsonify(error='API yêu cầu Content-Type: application/json.'), 415
            origin = request.headers.get('Origin')
            if origin and origin != request.host_url.rstrip('/'):
                return jsonify(error='Chỉ nhận yêu cầu từ cùng địa chỉ giao diện.'), 403

    @app.after_request
    def response_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; frame-ancestors 'none'; form-action 'self'")
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(ValueError)
    def invalid_input(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(SQLAlchemyError)
    def database_error(_error):
        return jsonify(error='Không kết nối hoặc thao tác được với database. '
                       'Nếu dùng PostgreSQL, hãy bật dịch vụ, tạo database GiaNha '
                       'và kiểm tra .env. Có thể chạy lại với --backend sqlite.'), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        return error

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception('Lỗi xử lý yêu cầu web')
        return jsonify(error='Không xử lý được yêu cầu. Xem terminal để kiểm tra lỗi.'), 500

    @app.get('/')
    def index():
        return render_template('vietnam.html')

    @app.get('/kingcounty')
    def kingcounty_reference():
        return render_template('kingcounty.html')

    @app.get('/legacy')
    def legacy():
        return render_template('index.html')

    @app.get('/api/status')
    def status():
        ensure_tables()
        with db.connect() as connection:
            counts = connection.execute(select(
                func.count().label('total'),
                func.coalesce(func.sum(case((records.c.is_demo.is_(True), 1), else_=0)), 0).label('demo'),
                func.coalesce(func.sum(case((records.c.is_demo.is_(False), 1), else_=0)), 0).label('real'),
            ).select_from(records)).mappings().one()
        model = {'method': 'unavailable', 'error': None}
        try:
            model['method'] = RealEstateAI(model_path).method
        except ValueError as error:
            model['error'] = str(error)
        return jsonify(database={'backend': db.dialect.name, 'connected': True},
                       counts=dict(counts), model=model, currency='VND')

    @app.get('/api/records')
    def list_records():
        try:
            page = int(request.args.get('page', '1'))
            page_size = int(request.args.get('page_size', '10'))
        except ValueError:
            raise ValueError('Trang và số dòng phải là số nguyên.') from None
        if page < 1 or not 1 <= page_size <= 100:
            raise ValueError('Trang phải từ 1; số dòng mỗi trang phải từ 1 đến 100.')
        query = request.args.get('q', '').strip()
        mode = request.args.get('mode', 'all')
        if len(query) > 200 or mode not in ('all', 'demo', 'real'):
            raise ValueError('Bộ lọc không hợp lệ hoặc từ khóa dài quá 200 ký tự.')
        conditions = []
        if query:
            conditions.append(or_(records.c.title.icontains(query, autoescape=True),
                                  records.c.id.icontains(query, autoescape=True)))
        if mode != 'all':
            conditions.append(records.c.is_demo.is_(mode == 'demo'))
        ensure_tables()
        with db.connect() as connection:
            total = connection.scalar(select(func.count()).select_from(records).where(*conditions))
            rows = connection.execute(select(records).where(*conditions)
                .order_by(records.c.updated_at.desc(), records.c.source, records.c.id)
                .limit(page_size).offset((page - 1) * page_size)).mappings().all()
        return jsonify(items=[serialize_record(row) for row in rows], total=total,
                       page=page, page_size=page_size, total_pages=max(1, (total + page_size - 1) // page_size))

    @app.post('/api/records')
    def predict_and_save():
        payload = request.get_json()
        if not isinstance(payload, dict):
            raise ValueError('Nội dung yêu cầu phải là một JSON object.')
        allowed = {'mode', 'id', 'title', 'area', 'rooms', 'latitude', 'longitude', 'actual_price'}
        if set(payload) - allowed:
            raise ValueError('Yêu cầu chứa trường không được hỗ trợ.')
        mode = payload.get('mode', 'real')
        if mode not in ('demo', 'real'):
            raise ValueError('Chế độ phải là demo hoặc real.')
        for field in ('id', 'title'):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                raise ValueError('Mã căn nhà và tiêu đề phải là chuỗi không để trống.')
        for field in ('area', 'rooms', 'latitude', 'longitude'):
            value = payload.get(field)
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ValueError('Diện tích, số phòng và tọa độ phải được nhập đầy đủ bằng số.')
        actual_price = payload.get('actual_price')
        if actual_price == '':
            actual_price = None
        if actual_price is not None and (isinstance(actual_price, bool)
                or not isinstance(actual_price, (str, int, float))):
            raise ValueError('Giá giao dịch phải là số VND hoặc để trống.')
        is_demo = mode == 'demo'
        if is_demo and actual_price is not None:
            raise ValueError('Dữ liệu minh họa không được gán giá giao dịch thật.')
        raw = {key: payload[key] for key in ('id', 'title', 'area', 'rooms', 'latitude', 'longitude')}
        raw.update(actual_price=actual_price, price_kind='sale' if actual_price is not None else 'unknown')
        frame = clean_data(pd.DataFrame([raw]), is_demo=is_demo,
                           source='web_demo' if is_demo else 'web')
        model = RealEstateAI(model_path, allow_demo=is_demo)
        frame['predicted_price'] = model.predict_price(frame)
        frame['prediction_method'] = model.method
        frame['updated_at'] = datetime.now(timezone.utc)
        ensure_tables()
        save_records(db, frame)
        row = frame.astype(object).where(pd.notna(frame), None).to_dict('records')[0]
        message = 'Đã dự đoán và lưu căn nhà.'
        if model.method == 'demo_formula':
            message = 'Đã lưu giá minh họa từ công thức demo; đây không phải giá thị trường.'
        elif model.method == 'unavailable':
            message = 'Đã lưu dữ liệu thật. Chưa có mô hình VND nên giá dự đoán để trống.'
        return jsonify(item=serialize_record(row), message=message)

    @app.post('/api/demo')
    def load_demo():
        if request.get_json() != {}:
            raise ValueError('API mẫu nhận JSON object rỗng: {}.')
        ensure_tables()
        run_pipeline(engine=db, model_path=model_path, verbose=False)
        return jsonify(message='Đã cập nhật 2 tin mẫu. Chạy lại không tạo thêm bản ghi trùng.')

    from .kingcounty import MODEL as KINGCOUNTY_MODEL
    from .kingcounty_api import register_routes
    register_routes(app, db, kingcounty_model_path or KINGCOUNTY_MODEL)
    from .vietnam import MODEL as VIETNAM_MODEL
    from .vietnam_api import register_routes as register_vietnam
    register_vietnam(app, db, vietnam_model_path or VIETNAM_MODEL)
    return app


def main(argv=None):
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=['sqlite', 'postgresql'], help='Ghi đè DB_BACKEND cho lần chạy này.')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--open-browser', action='store_true')
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('Cổng phải từ 1 đến 65535.')
    if args.backend:
        os.environ['DB_BACKEND'] = args.backend
    app = create_app()
    url = f'http://127.0.0.1:{args.port}'
    print(f'Giao diện: {url} | Database: {app.extensions["database"].dialect.name}')
    print('Giữ terminal mở; Ctrl+C để dừng.')
    if args.open_browser:
        timer = Timer(1, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    try:
        app.run(host='127.0.0.1', port=args.port, debug=False, use_reloader=False)
    finally:
        app.extensions['database'].dispose()


if __name__ == '__main__':
    main()
