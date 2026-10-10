"""Small Flask app to keep a clickable list of URLs backed by SQLite."""
import os
import socket
import sqlite3
from urllib.parse import urlparse

from flask import Flask, g, redirect, render_template_string, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, "urls.db")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5027

app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("URL_LIST_DB", DEFAULT_DB)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>URL List</title>
<style>
  body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         max-width: 640px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }
  h1 { font-size: 1.5rem; }
  form { display: flex; gap: 0.5rem; margin: 1rem 0 2rem; }
  input[type=url], input[type=text] { flex: 1; padding: 0.5rem; font-size: 1rem; }
  button { padding: 0.5rem 1rem; font-size: 1rem; cursor: pointer; }
  ul { list-style: none; padding: 0; }
  li { padding: 0.4rem 0; border-bottom: 1px solid #e0e0e0;
       overflow-wrap: anywhere; }
  .error { color: #a00; }
  .empty { color: #555; }
</style>
</head>
<body>
  <h1>URL List</h1>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
  <form action="{{ url_for('add_url') }}" method="post">
    <input type="text" name="url" placeholder="https://example.com" required>
    <button type="submit">Add URL</button>
  </form>
  {% if urls %}
  <ul>
    {% for u in urls %}
    <li><a href="{{ u }}">{{ u }}</a></li>
    {% endfor %}
  </ul>
  {% else %}
  <p class="empty">No URLs yet. Add one above.</p>
  {% endif %}
</body>
</html>
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS urls ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "url TEXT UNIQUE NOT NULL)"
        )
        g.db.commit()
    return g.db


@app.teardown_appcontext
def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path=None):
    path = db_path or app.config["DATABASE"]
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS urls ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "url TEXT UNIQUE NOT NULL)"
    )
    conn.commit()
    conn.close()


def normalize_url(raw):
    raw = (raw or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    parsed = urlparse(raw)
    if not parsed.netloc:
        return ""
    return raw


def get_urls():
    db = get_db()
    rows = db.execute("SELECT url FROM urls ORDER BY id").fetchall()
    return [r[0] for r in rows]


@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGE, urls=get_urls(), error=None)


@app.route("/add", methods=["POST"])
def add_url():
    url = normalize_url(request.form.get("url", ""))
    if not url:
        return (
            render_template_string(
                PAGE, urls=get_urls(), error="Please enter a valid URL."
            ),
            400,
        )
    db = get_db()
    try:
        db.execute("INSERT INTO urls (url) VALUES (?)", (url,))
        db.commit()
    except sqlite3.IntegrityError:
        pass  # already saved; treat as success
    return redirect(url_for("index"))


def is_port_available(port, host=DEFAULT_HOST):
    """True if host:port can be bound right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(start=DEFAULT_PORT, host=DEFAULT_HOST, limit=100):
    """Return start if free, else increment until a free port is found."""
    port = start
    for _ in range(limit):
        if is_port_available(port, host):
            return port
        port += 1
    raise OSError(f"No free port found from {start} to {port - 1}")


if __name__ == "__main__":
    init_db()
    port = find_available_port(DEFAULT_PORT, DEFAULT_HOST)
    if port != DEFAULT_PORT:
        print(f"Port {DEFAULT_PORT} busy, using {port} instead.")
    app.run(host=DEFAULT_HOST, port=port)
