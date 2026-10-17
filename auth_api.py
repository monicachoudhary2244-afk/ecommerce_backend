from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path
import sqlite3
import secrets
import hmac
import time

app = Flask(__name__)

DATABASE = Path(__file__).resolve().parent / "ecommerce.db"
TOKEN_LIFETIME = 3600  # 1 hour


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


def hash_token(token):
    import hashlib
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def get_current_user():
    header = request.headers.get("Authorization", "")
    parts = header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]
    token_digest = hash_token(token)

    with get_db() as conn:
        row = conn.execute("""
            SELECT users.id, users.name, users.email
            FROM auth_tokens
            JOIN users ON users.id = auth_tokens.user_id
            WHERE auth_tokens.token_hash = ?
              AND auth_tokens.expires_at > ?
        """, (token_digest, int(time.time()))).fetchone()

    return dict(row) if row else None


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "E-Commerce Authentication API",
        "endpoints": [
            "POST /register",
            "POST /login",
            "GET /me",
            "POST /logout"
        ]
    })


@app.route("/register", methods=["POST"])
def register():
    data = get_json()

    if data is None:
        return jsonify({"error": "Send valid JSON"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not all(isinstance(x, str) for x in (name, email, password)):
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    name = name.strip()
    email = email.strip().lower()

    if not name or len(name) > 100:
        return jsonify({"error": "Name must be 1-100 characters"}), 400

    if (
        not email
        or len(email) > 254
        or email.count("@") != 1
        or email.startswith("@")
        or email.endswith("@")
        or "." not in email.split("@")[1]
    ):
        return jsonify({"error": "Enter a valid email address"}), 400

    if len(password) < 8 or len(password) > 128:
        return jsonify({
            "error": "Password must be 8-128 characters"
        }), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
            """, (name, email, password_hash))

            user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email is already registered"}), 409

    return jsonify({
        "message": "Registration successful",
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }), 201


@app.route("/login", methods=["POST"])
def login():
    data = get_json()

    if data is None:
        return jsonify({"error": "Send valid JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required"}), 400

    with get_db() as conn:
        user = conn.execute("""
            SELECT id, name, email, password_hash
            FROM users WHERE email = ? COLLATE NOCASE
        """, (email.strip(),)).fetchone()

    if user is None or not check_password_hash(
        user["password_hash"], password
    ):
        return jsonify({"error": "Invalid email or password"}), 401

    token = secrets.token_urlsafe(32)
    token_digest = hash_token(token)
    expires_at = int(time.time()) + TOKEN_LIFETIME

    with get_db() as conn:
        conn.execute("""
            INSERT INTO auth_tokens (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
        """, (token_digest, user["id"], expires_at))

    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": TOKEN_LIFETIME,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })


@app.route("/me", methods=["GET"])
def me():
    user = get_current_user()

    if user is None:
        return jsonify({"error": "Valid login token required"}), 401

    return jsonify({"user": user})


@app.route("/logout", methods=["POST"])
def logout():
    header = request.headers.get("Authorization", "")
    parts = header.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return jsonify({"error": "Valid login token required"}), 401

    token_digest = hash_token(parts[1])

    with get_db() as conn:
        cursor = conn.execute("""
            DELETE FROM auth_tokens
            WHERE token_hash = ? AND expires_at > ?
        """, (token_digest, int(time.time())))

    if cursor.rowcount == 0:
        return jsonify({"error": "Invalid or expired token"}), 401

    return jsonify({"message": "Logout successful"})


if __name__ == "__main__":
    init_auth_db()
    app.run(port=5001, debug=True)