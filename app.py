from flask import Flask, jsonify, request

app = Flask(__name__)

# Product data
products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 50000,
        "category": "Electronics"
    },
    {
        "id": 2,
        "name": "Headphones",
        "price": 1500,
        "category": "Electronics"
    },
    {
        "id": 3,
        "name": "Shoes",
        "price": 2000,
        "category": "Fashion"
    }
]


# Home route
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to E-Commerce Backend API",
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


# Get all products and filter by category
@app.route("/products", methods=["GET"])
def get_products():
    category = request.args.get("category")

    if category:
        result = [
            p for p in products
            if p["category"].lower() == category.lower()
        ]
        return jsonify(result)

    return jsonify(products)


# Get a single product by ID
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    for product in products:
        if product["id"] == product_id:
            return jsonify(product)

    return jsonify({"error": "Product not found"}), 404


# Add a new product
@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send product data as JSON"}), 400

    name = data.get("name")
    price = data.get("price")
    category = data.get("category")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Valid name is required"}), 400

    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or price < 0
    ):
        return jsonify({"error": "Valid non-negative price is required"}), 400

    if not isinstance(category, str) or not category.strip():
        return jsonify({"error": "Valid category is required"}), 400

    new_product = {
        "id": max((p["id"] for p in products), default=0) + 1,
        "name": name.strip(),
        "price": price,
        "category": category.strip()
    }

    products.append(new_product)

    return jsonify(new_product), 201


# Update an existing product
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send updated data as JSON"}), 400

    for product in products:
        if product["id"] == product_id:
            if "name" in data:
                if not isinstance(data["name"], str) or not data["name"].strip():
                    return jsonify({"error": "Valid name is required"}), 400
                product["name"] = data["name"].strip()

            if "price" in data:
                price = data["price"]
                if (
                    isinstance(price, bool)
                    or not isinstance(price, (int, float))
                    or price < 0
                ):
                    return jsonify({"error": "Valid non-negative price is required"}), 400
                product["price"] = price

            if "category" in data:
                if not isinstance(data["category"], str) or not data["category"].strip():
                    return jsonify({"error": "Valid category is required"}), 400
                product["category"] = data["category"].strip()

            return jsonify({
                "message": "Product updated successfully",
                "product": product
            })

    return jsonify({"error": "Product not found"}), 404


# Delete a product
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return jsonify({"message": "Product deleted successfully"})

    return jsonify({"error": "Product not found"}), 404


# Search products by name
@app.route("/search", methods=["GET"])
def search_products():
    name = request.args.get("name", "").strip()

    if not name:
        return jsonify({"error": "Please provide a product name"}), 400

    result = [
        p for p in products
        if name.lower() in p["name"].lower()
    ]

    return jsonify(result)


# Get all available categories
@app.route("/categories", methods=["GET"])
def get_categories():
    categories = sorted(set(p["category"] for p in products))
    return jsonify(categories)


# Handle invalid routes
@app.errorhandler(404)
def page_not_found(error):
    return jsonify({"error": "Route or product not found"}), 404


# Start the server
if __name__ == "__main__":
    app.run(debug=True)