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

def create_board_endpoint(name: str, temp_project: str, space_id: str, groups: list,
                          typesList: list, customFields: list):
    return {
        'path': '/CreateBoard',
        'json': {
        "name": name,
        "project": temp_project,
        "groups": groups,
        "typesList": typesList,
        "customFields": customFields
    },
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

def create_board_custom_field_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/CreateBoardCustomField',
        'json': {
        "label": "Priority",
        "type": "string",
        "required": False
    },
        'headers': {
            'Content-Type': 'application/json',
            "Current-Space-Id": space_id
        }
    }

def edit_board_custom_field_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/EditBoardCustomField',
        'json': {
        "id": "field_id",
        "label": "Updated Priority",
        "type": "string",
        "required": True
    },
        'headers': {
            'Content-Type': 'application/json',
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
