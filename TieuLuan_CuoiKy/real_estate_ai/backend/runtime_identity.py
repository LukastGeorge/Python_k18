"""Identify the source loaded by a running local UI, separately from its model."""
import hashlib
from .config import ROOT


def runtime_revision():
    names = ['backend/web_app.py','backend/vietnam.py','backend/kaggle_vietnam.py',
             'backend/vietnam_api.py','backend/runtime_identity.py',
             'frontend/templates/vietnam.html','frontend/static/vietnam.js','frontend/static/vietnam.css']
    digest = hashlib.sha256()
    for name in names:
        digest.update(name.encode('utf-8'))
        digest.update((ROOT/name).read_bytes())
    return digest.hexdigest()[:20]
