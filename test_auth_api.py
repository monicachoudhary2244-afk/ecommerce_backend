import json
import urllib.request
import urllib.error
import uuid

BASE_URL = "http://127.0.0.1:5001"


def send_request(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        BASE_URL + path,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return response.status, result
    except urllib.error.HTTPError as error:
        result = json.loads(error.read().decode("utf-8"))
        return error.code, result


# Unique email lets you run this test more than once
email = f"test_{uuid.uuid4().hex[:10]}@example.com"
password = "TestPass123!"

# 1. Register a user
status, result = send_request("POST", "/register", {
    "name": "Test User",
    "email": email,
    "password": password
})
assert status == 201, f"Registration failed: {result}"
print("PASS: Registration")

# 2. Reject duplicate email
status, result = send_request("POST", "/register", {
    "name": "Test User",
    "email": email,
    "password": password
})
assert status == 409, f"Duplicate email check failed: {result}"
print("PASS: Duplicate email rejected")

# 3. Reject wrong password
status, result = send_request("POST", "/login", {
    "email": email,
    "password": "WrongPassword123!"
})
assert status == 401, f"Wrong password check failed: {result}"
print("PASS: Wrong password rejected")

# 4. Login with correct password
status, result = send_request("POST", "/login", {
    "email": email,
    "password": password
})
assert status == 200, f"Login failed: {result}"
token = result["access_token"]
print("PASS: Login")

# 5. Access protected profile
status, result = send_request("GET", "/me", token=token)
assert status == 200, f"Profile request failed: {result}"
assert result["user"]["email"] == email
print("PASS: Protected profile")

# 6. Reject profile request without token
status, result = send_request("GET", "/me")
assert status == 401, f"Missing token check failed: {result}"
print("PASS: Missing token rejected")

# 7. Logout
status, result = send_request("POST", "/logout", token=token)
assert status == 200, f"Logout failed: {result}"
print("PASS: Logout")

# 8. Token should no longer work after logout
status, result = send_request("GET", "/me", token=token)
assert status == 401, f"Logged-out token still works: {result}"
print("PASS: Logged-out token rejected")

print("\nAll authentication tests passed!")