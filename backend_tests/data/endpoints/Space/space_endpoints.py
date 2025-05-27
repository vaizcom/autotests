def create_space_endpoint(name: str):
    return {
        "path": "/CreateSpace",
        "json": {
            "name": name
        },
        "headers": {
            "Content-Type": "application/json"
        }
    }

def edit_space_endpoint(name: str, space_id: str = None):
    headers = {"Content-Type": "application/json"}
    if space_id:
        headers["Current-Space-Id"] = space_id

    return {
        "path": "/EditSpace",
        "json": {"name": name},
        "headers": headers,
    }

def get_space_endpoint(space_id: str):
    return {
        "path": "/GetSpace",
        "json": {"spaceId": space_id},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def get_spaces_endpoint():
    return {
        "path": "/GetSpaces",
        "json": {},
        "headers": {
            "Content-Type": "application/json"
        }
    }

def remove_space_endpoint(space_id: str) -> dict:
    """
    Endpoint definition for /RemoveSpace
    Input: { spaceId: string }
    Output: { success: boolean }
    """
    return {
        "path": "/RemoveSpace",
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        },
        "json": {
            "spaceId": space_id
        }
    }
