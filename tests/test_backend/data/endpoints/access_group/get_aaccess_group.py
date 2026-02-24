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