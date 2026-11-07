from backend import launch_ui


def test_reuses_only_matching_source_and_model(monkeypatch):
    monkeypatch.setattr(launch_ui,'server_info',lambda port:{'runtime_revision':'new','metadata':{'model_version':'model'}})
    monkeypatch.setattr(launch_ui,'available',lambda port:False)
    assert launch_ui.choose_port(8000,'new','model') == (8000,True)


def test_old_running_code_does_not_block_updated_project(monkeypatch):
    monkeypatch.setattr(launch_ui,'server_info',lambda port: {'runtime_revision':'old','metadata':{'model_version':'model'}} if port==8000 else None)
    monkeypatch.setattr(launch_ui,'available',lambda port:port==8001)
    assert launch_ui.choose_port(8000,'new','model') == (8001,False)


def test_other_service_is_not_reused_or_terminated(monkeypatch):
    monkeypatch.setattr(launch_ui,'server_info',lambda port:None)
    monkeypatch.setattr(launch_ui,'available',lambda port:port==8002)
    assert launch_ui.choose_port(8000,'new','model') == (8002,False)
