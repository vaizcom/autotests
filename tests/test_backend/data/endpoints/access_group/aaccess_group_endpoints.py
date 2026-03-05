def get_access_group_endpoint(space_id: str, group_id: str):
    """
    Получение информации о группе доступа (GetAccessGroupInputDto).
    """
    return {
        "path": "/GetAccessGroup",
        "json": {"groupId": group_id},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }

def get_access_groups_endpoint(space_id: str):
    """
    Получение информации о группах доступа (GetAccessGroupsInputDto).
    """
    return {
        "path": "/GetAccessGroups",
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }


def create_access_group_endpoint(
        space_id: str,
        name: str,
        description: str,
        space_accesses: dict = None,
        project_accesses: dict = None,
        board_accesses: dict = None
):
    """
    Создание группы доступа (CreateAccessGroupInputDto).
    """
    json_payload = {
        "name": name,
        "description": description,
    }

    if space_accesses is not None:
        json_payload["spaceAccesses"] = space_accesses
    if project_accesses is not None:
        json_payload["projectAccesses"] = project_accesses
    if board_accesses is not None:
        json_payload["boardAccesses"] = board_accesses

    return {
        "path": "/CreateAccessGroup",
        "json": json_payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id
        }
    }