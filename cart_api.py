from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="E-Commerce Cart API")

# Temporary in-memory cart storage
carts = {}


class CartItem(BaseModel):
    product_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    quantity: int = Field(gt=0)


class UpdateQuantity(BaseModel):
    quantity: int = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Shopping Cart API is running"}


@app.post("/cart/{user_id}/items")
def add_to_cart(user_id: int, item: CartItem):
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    cart = carts.setdefault(user_id, [])

    for existing_item in cart:
        if existing_item["product_id"] == item.product_id:
            existing_item["quantity"] += item.quantity
            return {"message": "Cart quantity updated", "cart": cart}

    cart.append(item.model_dump())
    return {"message": "Item added to cart", "cart": cart}


@app.get("/cart/{user_id}")
def get_cart(user_id: int):
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    items = carts.get(user_id, [])
    total = sum(item["price"] * item["quantity"] for item in items)

    return {
        "user_id": user_id,
        "items": items,
        "total_items": sum(item["quantity"] for item in items),
        "total_price": round(total, 2)
    }


@app.put("/cart/{user_id}/items/{product_id}")
def update_quantity(
    user_id: int,
    product_id: int,
    data: UpdateQuantity
):
    for item in carts.get(user_id, []):
        if item["product_id"] == product_id:
            item["quantity"] = data.quantity
            return {"message": "Quantity updated", "cart": carts[user_id]}

    raise HTTPException(status_code=404, detail="Product not found in cart")


@app.delete("/cart/{user_id}/items/{product_id}")
def remove_from_cart(user_id: int, product_id: int):
    cart = carts.get(user_id, [])

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": "Item removed from cart", "cart": cart}

    raise HTTPException(status_code=404, detail="Product not found in cart")


@app.delete("/cart/{user_id}")
def clear_cart(user_id: int):
    carts[user_id] = []
    return {"message": "Cart cleared successfully"}
