from flask import Flask, jsonify, request
import sqlite3
from pathlib import Path

app = Flask(__name__)

# Database will be created in this project's folder
DATABASE = Path(__file__).resolve().parent / "ecommerce.db"


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                price REAL NOT NULL CHECK(price >= 0),
                category TEXT NOT NULL CHECK(length(trim(category)) > 0
                )
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        if count == 0:
            conn.executemany("""
                INSERT INTO products (name, price, category)
                VALUES (?, ?, ?)
            """, [
                ("Laptop", 50000, "Electronics"),
                ("Headphones", 1500, "Electronics"),
                ("Shoes", 2000, "Fashion")
            ])


def product_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "category": row["category"]
    }


def validate_product(data, partial=False):
    if not isinstance(data, dict):
        return False, "Send product data as a JSON object"

    required = ("name", "price", "category")

    if not partial:
        for field in required:
            if field not in data:
                return False, f"{field} is required"

    allowed = set(required)
    unknown = set(data) - allowed

    if unknown:
        return False, f"Unknown fields: {', '.join(sorted(unknown))}"

    if partial and not data:
        return False, "At least one field is required"

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return False, "Name must be a non-empty string"

    if "category" in data:
        if (
            not isinstance(data["category"], str)
            or not data["category"].strip()
        ):
            return False, "Category must be a non-empty string"

    if "price" in data:
        price = data["price"]
        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
            or price != price
            or price == float("inf")
            or price == float("-inf")
        ):
            return False, "Price must be a finite, non-negative number"

    return True, None


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to E-Commerce Backend API",
        "database": "SQLite",
        "endpoints": [
            "GET /products",
            "GET /products/<id>",
            "POST /products",
            "PUT /products/<id>",
            "DELETE /products/<id>",
            "GET /search?name=Laptop",
            "GET /categories"
        ]
    })


@app.route("/products", methods=["GET"])
def get_products():
    category = request.args.get("category")

    with get_db() as conn:
        if category:
            rows = conn.execute("""
                SELECT * FROM products
                WHERE category = ? COLLATE NOCASE
                ORDER BY id
            """, (category,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM products ORDER BY id"
            ).fetchall()

    return jsonify([product_dict(row) for row in rows])


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

    if row is None:
        return jsonify({"error": "Product not found"}), 404

    return jsonify(product_dict(row))


@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True)
    valid, error = validate_product(data)

    if not valid:
        return jsonify({"error": error}), 400

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO products (name, price, category)
            VALUES (?, ?, ?)
        """, (
            data["name"].strip(),
            data["price"],
            data["category"].strip()
        ))

        row = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()

        result = product_dict(row)

    return jsonify(result), 201


@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True)
    valid, error = validate_product(data, partial=True)

    if not valid:
        return jsonify({"error": error}), 400

    updates = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in data.items()
    }

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if existing is None:
            return jsonify({"error": "Product not found"}), 404

        set_clause = ", ".join(
            f"{field} = ?" for field in updates
        )
        values = list(updates.values()) + [product_id]

        conn.execute(
            f"UPDATE products SET {set_clause} WHERE id = ?",
            values
        )

        row = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        result = product_dict(row)

    return jsonify({
        "message": "Product updated successfully",
        "product": result
    })


@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Product not found"}), 404

    return jsonify({"message": "Product deleted successfully"})


@app.route("/search", methods=["GET"])
def search_products():
    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({
            "error": "Please provide a product name"
        }), 400

    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM products
            WHERE name LIKE ? COLLATE NOCASE
            ORDER BY id
        """, (f"%{name}%",)).fetchall()

    return jsonify([product_dict(row) for row in rows])


@app.route("/categories", methods=["GET"])
def get_categories():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT DISTINCT category
            FROM products
            ORDER BY category
        """).fetchall()

    return jsonify([row["category"] for row in rows])


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Route or product not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed"
    }), 405


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": "Internal server error"
    }), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)