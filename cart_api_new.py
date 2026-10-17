from fastapi import FastAPI, HTTPException
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json

app = FastAPI(title="E-Commerce Checkout API")

# Existing Cart API and Orders API addresses
CART_API = "http://127.0.0.1:8000"
ORDERS_API = "http://127.0.0.1:8001"


def call_api(url, method="GET", data=None):
    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    request = Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = response.read().decode("utf-8")
            return json.loads(result) if result else {}

    except HTTPError as error:
        details = error.read().decode("utf-8")
        raise HTTPException(
            status_code=502,
            detail=f"Connected API returned an error: {details}"
        )

    except (URLError, TimeoutError, OSError):
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Cart API or Orders API. Check that both are running."
        )

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail="An API returned an invalid response."
        )


@app.get("/")
def home():
    return {"message": "Checkout API is running"}


@app.post("/checkout/{user_id}")
def checkout(user_id: int):
    if user_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="User ID must be greater than zero"
        )

    # Step 1: Get the user's cart
    cart = call_api(f"{CART_API}/cart/{user_id}")

    items = cart.get("items", [])
    total = cart.get("total_price", 0)

    if not items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty"
        )

    if total <= 0:
        raise HTTPException(
            status_code=400,
            detail="Cart total must be greater than zero"
        )

    # Step 2: Create an order using the cart total
    order = call_api(
        f"{ORDERS_API}/orders",
        method="POST",
        data={
            "customer_id": user_id,
            "total_amount": total
        }
    )

    # Step 3: Clear the cart only after order creation succeeds
    call_api(
        f"{CART_API}/cart/{user_id}",
        method="DELETE"
    )

    return {
        "message": "Order placed successfully",
        "order": order,
        "cart_cleared": True
    }