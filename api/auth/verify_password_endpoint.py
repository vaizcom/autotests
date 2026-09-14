def verify_password_endpoint(temp_token, password):
    return {
        "path": "/VerifyPassword",
        "json": {"tempToken": temp_token, "password": password},
        "headers": {"Content-Type": "application/json"}
    }
