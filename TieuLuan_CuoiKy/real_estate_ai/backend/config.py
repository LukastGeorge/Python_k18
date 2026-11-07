"""Cấu hình dùng chung; đường dẫn luôn tính từ thư mục dự án."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

ROOT = Path(__file__).resolve().parents[1]
STORAGE_DIR = ROOT / 'storage'
MODEL_PATH = ROOT / 'models' / 'house_model.pkl'
FEATURES = ['dien_tich', 'so_phong_ngu', 'latitude', 'longitude']
load_dotenv(ROOT / '.env', override=False)


def configure_console():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')


def get_engine():
    backend = os.getenv('DB_BACKEND', 'postgresql').lower()
    if backend == 'sqlite':
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        return create_engine(URL.create('sqlite', database=str(STORAGE_DIR / 'real_estate.db')))
    if backend != 'postgresql':
        raise ValueError('DB_BACKEND phải là postgresql hoặc sqlite.')
    password = os.getenv('DB_PASSWORD')
    if not password:
        raise ValueError('Thiếu DB_PASSWORD. Sao chép .env.example thành .env và điền cấu hình.')
    url = URL.create('postgresql+psycopg2', username=os.getenv('DB_USER', 'postgres'),
        password=password, host=os.getenv('DB_HOST', '127.0.0.1'),
        port=int(os.getenv('DB_PORT', '5432')), database=os.getenv('DB_NAME', 'GiaNha'))
    return create_engine(url, pool_pre_ping=True, connect_args={'connect_timeout': 5}, hide_parameters=True)
