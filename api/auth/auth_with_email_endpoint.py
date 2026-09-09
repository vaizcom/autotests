def auth_with_email_endpoint(email):
    return {
        "path": "/AuthWithEmail",
        "json": {"email": email},
        "headers": {"Content-Type": "application/json"}
    }
