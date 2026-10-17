import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:5000"


def test_api(method, path, data=None):
    body = None

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method
    )

    try:
        with urllib.request.urlopen(req) as response:
            print(f"\n{method} {path}")
            print("Status:", response.status)
            print(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        print(f"\n{method} {path}")
        print("Status:", error.code)
        print(error.read().decode("utf-8"))

    except urllib.error.URLError:
        print("Server is not running. Start app.py first.")


if __name__ == "__main__":
    print("1. GET - All Products")
    test_api("GET", "/products")

    print("\n2. GET - Single Product")
    test_api("GET", "/products/1")

    print("\n3. GET - Search")
    test_api("GET", "/search?name=Laptop")

    print("\n4. GET - Categories")
    test_api("GET", "/categories")

    print("\n5. POST - Add Product")
    test_api("POST", "/products", {
        "name": "Mouse",
        "price": 500,
        "category": "Electronics"
    })

    print("\n6. PUT - Update Product")
    test_api("PUT", "/products/1", {
        "price": 45000
    })

    print("\n7. DELETE - Delete Product")
    test_api("DELETE", "/products/2")