def register_endpoint(email, password, full_name, terms_accepted=True):
    return {
        "path": "/register",
        "json": {
            "email": email,
            "fullName": full_name,
            "password": password,
            "termsAccepted": terms_accepted
        },
        "headers": {"Content-Type": "application/json"}
    }