"""Vietnam routes and prediction history, isolated from earlier project tables."""
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from flask import jsonify, request, send_from_directory
from sqlalchemy import MetaData, Table, Column, String, Float, Text, select

from .vietnam import MODEL, ARTIFACTS, load_bundle, estimate_property
from .runtime_identity import runtime_revision


def register_routes(app, engine, model_path=MODEL):
    loaded_revision = runtime_revision()
    predictions = Table('vietnam_predictions', MetaData(),
        Column('id', String(40), primary_key=True), Column('created_at', String(40)),
        Column('model_version', String(40)), Column('province_name', String(100)),
        Column('district_name', String(100)), Column('predicted_vnd', Float),
        Column('input_json', Text), Column('result_json', Text))

    @app.get('/api/vietnam/info')
    def vietnam_info():
        bundle = load_bundle(model_path)
        examples = json.loads((Path(model_path).parent / 'examples.json').read_text(encoding='utf-8'))
        return jsonify(metadata=bundle['metadata'], examples=examples, runtime_revision=loaded_revision)

    @app.post('/api/vietnam/predict')
    def vietnam_predict():
        payload = request.get_json()
        result = estimate_property(payload, model_path)
        predictions.metadata.create_all(engine)
        identifier = str(uuid4())
        with engine.begin() as con:
            con.execute(predictions.insert().values(id=identifier,
                created_at=datetime.now(timezone.utc).isoformat(), model_version=result['model_version'],
                province_name=payload['province_name'], district_name=payload['district_name'],
                predicted_vnd=result['predicted_vnd'], input_json=json.dumps(payload, ensure_ascii=False),
                result_json=json.dumps(result, ensure_ascii=False, allow_nan=False)))
        return jsonify(id=identifier, result=result)

    @app.get('/api/vietnam/history')
    def vietnam_history():
        predictions.metadata.create_all(engine)
        with engine.connect() as con:
            rows = con.execute(select(predictions.c.id, predictions.c.created_at,
                predictions.c.province_name, predictions.c.district_name, predictions.c.predicted_vnd,
                predictions.c.model_version).where(predictions.c.model_version == load_bundle(model_path)['metadata']['model_version'])
                .order_by(predictions.c.created_at.desc(), predictions.c.id).limit(10)).mappings().all()
        return jsonify(items=[dict(row) for row in rows])

    @app.get('/vietnam-evidence/<name>')
    def vietnam_evidence(name):
        allowed = {'area_price.png', 'rooms.png', 'districts.png', 'model_comparison.png',
                   'importance.png', 'test_errors.png', 'example_explanation.png', 'missingness.png'}
        if name not in allowed:
            return jsonify(error='Biểu đồ không tồn tại.'), 404
        return send_from_directory(ARTIFACTS / 'charts', name)
