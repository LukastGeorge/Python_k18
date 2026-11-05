"""Lưu tin theo khóa (source, id); hỗ trợ PostgreSQL và SQLite."""
import pandas as pd
from sqlalchemy import (MetaData, Table, Column, String, Float, Integer, Boolean,
                        DateTime, CheckConstraint, select, inspect)
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

metadata = MetaData()
# Dùng bảng mới vì bảng cũ có thể chứa tin lặp và không có nhãn giá thực.
records = Table('real_estate_records', metadata,
    Column('source', String(160), primary_key=True),
    Column('id', String(160), primary_key=True),
    Column('title', String(1000), nullable=False),
    Column('dien_tich', Float, nullable=False),
    Column('so_phong_ngu', Integer, nullable=False),
    Column('latitude', Float, nullable=False),
    Column('longitude', Float, nullable=False),
    Column('actual_price', Float, nullable=True),
    Column('price_kind', String(20), nullable=False),
    Column('predicted_price', Float, nullable=True),
    Column('prediction_method', String(40), nullable=False),
    Column('is_demo', Boolean, nullable=False),
    Column('updated_at', DateTime(timezone=True), nullable=False),
    CheckConstraint('dien_tich > 0'), CheckConstraint('so_phong_ngu >= 0'),
    CheckConstraint('actual_price IS NULL OR actual_price > 0'),
    CheckConstraint('predicted_price IS NULL OR predicted_price > 0'),
)


def save_records(engine, frame):
    if frame.empty:
        return 0
    metadata.create_all(engine)
    insert = {'postgresql': postgres_insert, 'sqlite': sqlite_insert}.get(engine.dialect.name)
    if insert is None:
        raise ValueError('Chỉ hỗ trợ PostgreSQL và SQLite.')
    # NaN phải thành SQL NULL; không lưu NaN như một giá hợp lệ.
    values = frame.astype(object).where(pd.notna(frame), None).to_dict('records')
    with engine.begin() as connection:
        for start in range(0, len(values), 1000):
            statement = insert(records).values(values[start:start + 1000])
            updates = {c.name: getattr(statement.excluded, c.name) for c in records.c if not c.primary_key}
            statement = statement.on_conflict_do_update(index_elements=['source', 'id'], set_=updates)
            connection.execute(statement)
    return len(values)


def load_training_data(engine):
    columns = ['source', 'id', 'dien_tich', 'so_phong_ngu', 'latitude', 'longitude', 'actual_price']
    if not inspect(engine).has_table(records.name):
        return pd.DataFrame(columns=columns)
    query = select(*(records.c[c] for c in columns)).where(
        records.c.is_demo.is_(False), records.c.actual_price.is_not(None), records.c.price_kind == 'sale'
    ).order_by(records.c.source, records.c.id)
    with engine.connect() as connection:
        return pd.read_sql(query, connection)
