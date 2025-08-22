def get_boards_endpoint(space_id: str):
    return {
        'path': '/GetBoards',
        'json': {},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def get_board_endpoint(board_id: str, space_id: str):
    return {
        'path': '/GetBoard',
        'json': {'boardId': board_id},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def create_board_endpoint(
    name: str, project: str, space_id: str, groups: list = None, typesList: list = None, customFields: list = None
):
    payload = {
        'name': name,
        'project': project,
        'groups': groups,
        'typesList': typesList,
        'customFields': customFields,
    }

    return {
        'path': '/CreateBoard',
        'json': payload,
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def delete_board_endpoint(board_id: str, board_name: str, space_id: str):
    return {
        'path': '/DeleteBoard',
        'json': {'boardId': board_id, 'board_name': board_name},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def edit_board_endpoint(board_id: str, name: str, space_id: str):
    return {
        'path': '/EditBoard',
        'json': {'boardId': board_id, 'name': name},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def import_board_file_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/ImportBoardFile',
        'json': {'project': project_id, 'file': 'mock_file_data'},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def import_board_text_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/ImportBoardText',
        'json': {'project': project_id, 'text': 'imported text content'},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def create_board_type_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/CreateBoardType',
        'json': {'label': 'Bug', 'color': 'red', 'icon': 'Bug', 'description': ''},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def edit_board_type_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/EditBoardType',
        'json': {
            'id': 'type_id',
            'label': 'Bug Updated',
            'color': 'green',
            'icon': 'BugCheck',
            'description': 'Updated description',
        },
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def remove_board_type_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/RemoveBoardType',
        'json': {'id': 'type_id'},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def create_board_group_endpoint(
    board_id: str, space_id: str, name: str, description: str = None, limit: int = None, hidden: bool = False
):
    payload = {'boardId': board_id, 'name': name}

    if description is not None:
        payload['description'] = description

    if limit is not None:
        payload['limit'] = limit

    if hidden:
        payload['hidden'] = hidden

    return {
        'path': '/CreateBoardGroup',
        'json': payload,
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def edit_board_group_endpoint(
    board_id: str,
    board_group_id: str,
    space_id: str,
    name: str = None,
    description: str = None,
    hidden: bool = None,
    limit: int = None,
):
    # Собираем payload с обязательными полями
    payload = {
        'boardId': board_id,
        'boardGroupId': board_group_id,
    }

    # Добавляем только переданные параметры (Partial DTO)
    if name is not None:
        payload['name'] = name
    if description is not None:
        payload['description'] = description
    if hidden is not None:
        payload['hidden'] = hidden
    if limit is not None:
        payload['limit'] = limit

    return {
        'path': '/EditBoardGroup',
        'json': payload,
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def remove_board_group_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/RemoveBoardGroup',
        'json': {'id': 'group_id'},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def reorder_board_groups_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/ReorderBoardGroups',
        'json': {'order': ['group_id1', 'group_id2']},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def create_board_custom_field_endpoint(
    board_id: str,
    space_id: str,
    name: str,
    type: str,
    hidden: bool = False,
    options: list = None,
    description: str = None,
):
    payload = {'boardId': board_id, 'name': name, 'type': type, 'hidden': hidden}

    if options is not None:
        payload['options'] = options

    if description is not None:
        payload['description'] = description

    return {
        'path': '/CreateBoardCustomField',
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
        'json': payload,
    }


def edit_board_custom_field_endpoint(
    board_id: str,
    space_id: str,
    field_id: str,
    name: str = None,
    description: str = None,
    hidden: bool = None,
    options: list = None,
):
    payload = {'boardId': board_id, 'fieldId': field_id}

    if name is not None:
        payload['name'] = name

    if description is not None:
        payload['description'] = description

    if hidden is not None:
        payload['hidden'] = hidden

    if options is not None:
        payload['options'] = options

    return {
        'path': '/EditBoardCustomField',
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
        'json': payload,
    }


def remove_board_custom_field_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/RemoveBoardCustomField',
        'json': {'id': 'field_id'},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }


def broadcast_board_endpoint(name: str, project_id: str, space_id: str):
    return {
        'path': '/BroadcastBoard',
        'json': {'boardId': 'board_id'},
        'headers': {'Content-Type': 'application/json', 'Current-Space-Id': space_id},
    }
