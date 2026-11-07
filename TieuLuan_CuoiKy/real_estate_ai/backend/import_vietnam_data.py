"""Import observed asking prices; never use user predictions as training labels."""
from pathlib import Path
import pandas as pd
from sqlalchemy import MetaData, Table, Column, String, Float, select, func
from .vietnam import ARTIFACTS


def import_catalog(engine, path=ARTIFACTS / 'listings_clean.csv.gz'):
    data = pd.read_csv(Path(path), dtype={'listing_id': str, 'district_name': str, 'ward_name': str})
    table = Table('vietnam_2024_listings', MetaData(),
        Column('listing_id', String(24), primary_key=True), Column('published_at', String(10)),
        Column('province_name', String(100)), Column('district_name', String(100)),
        Column('property_type_name', String(100)), Column('area', Float), Column('asking_price_vnd', Float))
    table.metadata.create_all(engine)
    data = data.rename(columns={'price': 'asking_price_vnd'})[[column.name for column in table.columns]]
    with engine.begin() as con:
        existing = set(con.scalars(select(table.c.listing_id)))
        new = data[~data.listing_id.isin(existing)]
        for start in range(0, len(new), 1000):
            con.execute(table.insert(), new.iloc[start:start + 1000].to_dict('records'))
        return con.scalar(select(func.count()).select_from(table))


if __name__ == '__main__':
    from .config import get_engine
    print('Tin nguồn trong database:', import_catalog(get_engine()))
