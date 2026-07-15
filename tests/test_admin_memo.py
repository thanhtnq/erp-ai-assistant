from fastapi.testclient import TestClient

from api.main import app
from api.auth import verify_api_key
import api.routers.admin_memo as admin_memo


app.dependency_overrides[verify_api_key] = lambda: "test-key"


class FakeCursor:
    def __init__(self):
        self.executed_sql = None
        self.executed_params = None

    def execute(self, sql, params):
        self.executed_sql = sql
        self.executed_params = params

    def fetchone(self):
        return {"idcode": 77}

    def close(self):
        return None


class FakeConn:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self, cursor_factory=None):
        return self.cursor_obj

    def commit(self):
        return None

    def rollback(self):
        return None

    def close(self):
        return None


def test_create_memo_accepts_form_fields(monkeypatch):
    conn = FakeConn()
    monkeypatch.setattr(admin_memo, "_get_pg_conn", lambda: conn)

    client = TestClient(app)
    response = client.post(
        "/admin/memo",
        data={"companyfn": "ABC", "content": "hello from form", "created_by": "admin"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "id": 77}
    assert "INSERT INTO memo_long_table" in conn.cursor_obj.executed_sql
