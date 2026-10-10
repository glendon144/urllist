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
<title>Custom URL Selector</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <h1>Custom URL Selector</h1>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
  <div class="text-controls">
    <button type="button" id="text-smaller" aria-label="Smaller text">A-</button>
    <label for="text-size-slider">Text size</label>
    <input type="range" id="text-size-slider" min="12" max="28" step="1" value="16">
    <button type="button" id="text-larger" aria-label="Larger text">A+</button>
  </div>
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
  <script src="{{ url_for('static', filename='textsize.js') }}"></script>
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
