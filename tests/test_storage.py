from core.storage import Storage


def test_storage_events(tmp_path):
    db_path = tmp_path / "test.db"
    storage = Storage(str(db_path))
    storage.record_event("INFO", "TEST", "message", {"a": 1})
    events = storage.fetch_recent_events(1)
    assert events
    assert events[0]["event_type"] == "TEST"
    storage.close()
