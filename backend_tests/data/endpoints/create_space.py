def create_space_endpoint(name="Test space"):
    return {
        "path": "/CreateSpace",
        "json": {"name": name},
        "headers": {
            "Content-Type": "application/json"
        }
    }
