from fastapi.testclient import TestClient
from cart_api import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Shopping Cart API is running"
    }


def test_add_item_to_cart():
    response = client.post(
        "/cart/1/items",
        json={
            "product_id": 101,
            "name": "T-Shirt",
            "price": 499,
            "quantity": 2
        }
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Item added to cart"


def test_get_cart():
    client.delete("/cart/2")

    client.post(
        "/cart/2/items",
        json={
            "product_id": 102,
            "name": "Shoes",
            "price": 1000,
            "quantity": 2
        }
    )

    response = client.get("/cart/2")

    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 2
    assert data["total_price"] == 2000


def test_update_quantity():
    client.delete("/cart/3")

    client.post(
        "/cart/3/items",
        json={
            "product_id": 103,
            "name": "Bag",
            "price": 500,
            "quantity": 1
        }
    )

    response = client.put(
        "/cart/3/items/103",
        json={"quantity": 3}
    )

    assert response.status_code == 200
    assert response.json()["cart"][0]["quantity"] == 3


def test_remove_item():
    client.delete("/cart/4")

    client.post(
        "/cart/4/items",
        json={
            "product_id": 104,
            "name": "Book",
            "price": 200,
            "quantity": 1
        }
    )

    response = client.delete("/cart/4/items/104")

    assert response.status_code == 200
    assert response.json()["cart"] == []


def test_clear_cart():
    client.delete("/cart/5")

    client.post(
        "/cart/5/items",
        json={
            "product_id": 105,
            "name": "Pen",
            "price": 20,
            "quantity": 2
        }
    )

    response = client.delete("/cart/5")

    assert response.status_code == 200
    assert response.json()["message"] == "Cart cleared successfully"