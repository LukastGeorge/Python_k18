"""Primary API for the notebook dataset; legacy records remain isolated."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from flask import jsonify, request, send_from_directory
from sqlalchemy import MetaData, Table, Column, String, Text, Float, select, func
from .kingcounty import MODEL, ARTIFACTS, load_bundle, estimate_property


def register_routes(app, engine, model_path=MODEL):
    predictions = Table('kingcounty_predictions', MetaData(),
        Column('id', String(40), primary_key=True), Column('created_at', String(40)),
        Column('model_version', String(40)), Column('predicted_vnd', Float),
        Column('input_json', Text), Column('result_json', Text))

    @app.get('/api/kingcounty/info')
    def info():
        bundle = load_bundle(model_path)
        examples_path = Path(model_path).parent / 'examples.json'
        examples = json.loads(examples_path.read_text(encoding='utf-8')) if examples_path.exists() else []
        return jsonify(metadata=bundle['metadata'], examples=examples)

    @app.post('/api/kingcounty/predict')
    def predict():
        payload = request.get_json()
        result = estimate_property(payload, model_path)
        predictions.metadata.create_all(engine)
        identifier = str(uuid4())
        with engine.begin() as con:
            con.execute(predictions.insert().values(id=identifier,
                created_at=datetime.now(timezone.utc).isoformat(), model_version=result['model_version'],
                predicted_vnd=result['predicted_vnd'], input_json=json.dumps(payload, ensure_ascii=False),
                result_json=json.dumps(result, ensure_ascii=False)))
        return jsonify(id=identifier, result=result)

    @app.get('/api/kingcounty/history')
    def history():
        predictions.metadata.create_all(engine)
        with engine.connect() as con:
            rows = con.execute(select(predictions.c.id, predictions.c.created_at, predictions.c.predicted_vnd,
                                      predictions.c.model_version).order_by(predictions.c.created_at.desc()).limit(10)).mappings().all()
        return jsonify(items=[dict(row) for row in rows])

    @app.get('/evidence/<name>')
    def evidence(name):
        allowed = {'area_price.png', 'bedrooms_bathrooms.png', 'quality_environment.png',
                   'location.png', 'amenities.png', 'model_comparison.png', 'test_errors.png',
                   'importance.png', 'example_explanation.png', 'price_per_m2.png', 'calibration.png'}
        if name not in allowed:
            return jsonify(error='Biểu đồ không tồn tại.'), 404
        return send_from_directory(ARTIFACTS / 'charts', name)
