def create_board_endpoint(name: str, project_id: str, space_id: str) -> dict:
    return {
        "path": "/CreateBoard",
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        },
        "json": {
            "name": name,
            "project": project_id,
            "groups": [{"name": "Group 1", "description": "Default group"}],
            "typesList": [{"label": "Default", "color": "blue", "icon": "Dot", "description": ""}],
            "customFields": []
        }
    }

def get_board_endpoint(board_id: str, space_id: str) -> dict:
    return {
        "path": "/GetBoard",
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        },
        "json": {"boardId": board_id}
    }

def edit_board_endpoint(board_id: str, name: str, space_id: str) -> dict:
    return {
        "path": "/EditBoard",
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        },
        "json": {
            "boardId": board_id,
            "name": name
        }
    }
