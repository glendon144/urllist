import socket

import app as url_app


def _client(tmp_path, monkeypatch):
    db = tmp_path / "test_urls.db"
    monkeypatch.setenv("URL_LIST_DB", str(db))
    url_app.app.config["DATABASE"] = str(db)
    url_app.init_db(str(db))
    return url_app.app.test_client(), db


def test_add_url_shows_clickable_link(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    resp = client.post("/add", data={"url": "https://example.com"})
    assert resp.status_code == 302
    page = client.get("/")
    assert page.status_code == 200
    assert b'<a href="https://example.com">https://example.com</a>' in page.data
    assert b"Add URL" in page.data


def test_add_url_persists_in_sqlite(tmp_path, monkeypatch):
    import sqlite3

    client, db = _client(tmp_path, monkeypatch)
    client.post("/add", data={"url": "example.org"})
    conn = sqlite3.connect(str(db))
    rows = conn.execute("SELECT url FROM urls").fetchall()
    conn.close()
    assert rows == [("https://example.org",)]
    # A fresh client (new run) still sees the saved URL.
    fresh = url_app.app.test_client()
    assert b"https://example.org" in fresh.get("/").data


def test_add_url_rejects_empty(tmp_path, monkeypatch):
    client, _ = _client(tmp_path, monkeypatch)
    resp = client.post("/add", data={"url": ""})
    assert resp.status_code == 400


def test_find_available_port_returns_free_port():
    port = url_app.find_available_port(5027)
    assert port >= 5027
    assert url_app.is_port_available(port)


def test_find_available_port_skips_busy_port():
    busy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    busy.bind(("127.0.0.1", 0))
    busy_port = busy.getsockname()[1]
    try:
        assert not url_app.is_port_available(busy_port)
        found = url_app.find_available_port(busy_port)
        assert found > busy_port
        assert url_app.is_port_available(found)
    finally:
        busy.close()
