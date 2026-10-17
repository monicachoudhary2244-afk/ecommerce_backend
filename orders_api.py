from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import sqlite3

app = FastAPI(title="E-commerce Orders API")

DATABASE = "ecommerce.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Placed'
            )
        """)


create_table()


class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    total_amount: float = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Orders API is running"}


@app.post("/orders", status_code=201)
def create_order(order: OrderCreate):
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO orders (customer_id, total_amount)
                VALUES (?, ?)
                """,
                (order.customer_id, order.total_amount)
            )

            order_id = cursor.lastrowid

            return {
                "message": "Order created successfully",
                "order_id": order_id,
                "customer_id": order.customer_id,
                "total_amount": order.total_amount,
                "status": "Placed"
            }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while creating order"
        )


@app.get("/orders")
def get_orders():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM orders ORDER BY id DESC"
            ).fetchall()

            return [dict(row) for row in rows]

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching orders"
        )


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        return dict(row)


@app.patch("/orders/{order_id}/cancel")
def cancel_order(order_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM orders WHERE id = ?",
            (order_id,)
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if row["status"] == "Cancelled":
            raise HTTPException(
                status_code=400,
                detail="Order is already cancelled"
            )

        conn.execute(
            "UPDATE orders SET status = 'Cancelled' WHERE id = ?",
            (order_id,)
        )

        return {
            "message": "Order cancelled successfully",
            "order_id": order_id,
            "status": "Cancelled"
        }