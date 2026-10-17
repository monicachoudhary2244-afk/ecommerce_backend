import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:5000"


def send_request(method, path, data=None):
    url = BASE_URL + path
    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return response.status, result

    except urllib.error.HTTPError as error:
        result = json.loads(error.read().decode("utf-8"))
        return error.code, result


# 1. Add a temporary test product
status, product = send_request("POST", "/products", {
    "name": "Temporary Test Product",
    "price": 100,
    "category": "Testing"
})

assert status == 201, f"POST failed: {product}"
product_id = product["id"]
print("PASS: POST - Product added")

# 2. Read the test product
status, result = send_request(
    "GET", f"/products/{product_id}"
)

assert status == 200, f"GET failed: {result}"
assert result["name"] == "Temporary Test Product"
print("PASS: GET - Product found")

# 3. Update the test product
status, result = send_request(
    "PUT", f"/products/{product_id}", {
        "price": 200
    }
)

assert status == 200, f"PUT failed: {result}"
assert result["product"]["price"] == 200
print("PASS: PUT - Product updated")

# 4. Delete only the test product
status, result = send_request(
    "DELETE", f"/products/{product_id}"
)

assert status == 200, f"DELETE failed: {result}"
print("PASS: DELETE - Test product deleted")

# 5. Confirm the product is deleted
status, result = send_request(
    "GET", f"/products/{product_id}"
)

assert status == 404, f"Unexpected result: {result}"
print("PASS: Deleted product returns 404")

print("\nAll database API tests passed!")