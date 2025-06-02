def get_boards_endpoint(space_id: str):
    return {
        'path': '/GetBoards',
        'json': {},
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def get_board_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/GetBoard',
        'json': {
        "name": name,
        "project": project_id
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def create_board_endpoint(
    name: str,
    temp_project: str,
    space_id: str,
    groups: list = None,
    typesList: list = None,
    customFields: list = None,
    description: str = None
):
    payload = {
        "name": name,
        "project": temp_project,
        "groups": groups,
        "typesList": typesList,
        "customFields": customFields,
    }
    if description is not None:
        payload["description"] = description

    return {
        'path': '/CreateBoard',
        'json': payload,
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def edit_board_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/EditBoard',
        'json': {
        "name": name,
        "project": project_id
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def import_board_file_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/ImportBoardFile',
        'json': {
        "project": project_id,
        "file": "mock_file_data"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def import_board_text_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/ImportBoardText',
        'json': {
        "project": project_id,
        "text": "imported text content"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def create_board_type_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/CreateBoardType',
        'json': {
        "label": "Bug",
        "color": "red",
        "icon": "Bug",
        "description": ""
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def edit_board_type_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/EditBoardType',
        'json': {
        "id": "type_id",
        "label": "Bug Updated",
        "color": "green",
        "icon": "BugCheck",
        "description": "Updated description"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def remove_board_type_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/RemoveBoardType',
        'json': {
        "id": "type_id"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def create_board_group_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/CreateBoardGroup',
        'json': {
        "name": "New Group",
        "description": "Group description"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def edit_board_group_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/EditBoardGroup',
        'json': {
        "id": "group_id",
        "name": "Edited Group",
        "description": "Edited description"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def remove_board_group_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/RemoveBoardGroup',
        'json': {
        "id": "group_id"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def reorder_board_groups_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/ReorderBoardGroups',
        'json': {
        "order": ["group_id1", "group_id2"]
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def create_board_custom_field_endpoint(board_id: str, name: str, type: str, space_id: str):
    return {
        "path": "/CreateBoardCustomField",
        "json": {
            "boardId": board_id,
            "name": name,
            "type": type
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }


def edit_board_custom_field_endpoint(board_id: str, field_id: str,
                                     name: str = None,
                                     description: str = None,
                                     hidden: bool = None,
                                     options: list = None,
                                     space_id: str = None):
    payload = {
        "boardId": board_id,
        "fieldId": field_id
    }

    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if hidden is not None:
        payload["hidden"] = hidden
    if options is not None:
        payload["options"] = options

    return {
        "path": "/EditBoardCustomField",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }


def remove_board_custom_field_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/RemoveBoardCustomField',
        'json': {
        "id": "field_id"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def broadcast_board_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/BroadcastBoard',
        'json': {
        "boardId": "board_id"
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }
