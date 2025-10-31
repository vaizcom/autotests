def get_milestones_endpoint(
    space_id: str,
    board_id: str = None,
    project_id: str = None,
    with_archived: bool = None,
    skip: int = None,
    limit: int = None,
):
    """
    Формирует данные для эндпоинта получения milestones.
    :return: Словарь с параметрами для запроса.
    """
    payload = {}

    if board_id:
        payload["boardId"] = board_id

    if project_id:
        payload["projectId"] = project_id

    if with_archived is not None:
        payload["withArchived"] = with_archived

    if skip is not None:
        payload["skip"] = skip

    if limit is not None:
        payload["limit"] = limit

    return {
        "path": "/GetMilestones",
        "headers": {
            'Current-Space-Id': space_id,
        },
        "json": payload,
    }

def get_milestone_endpoint(ms_id: str, space_id: str):
    return {
        "path": "/GetMilestone",
        "json": {"_id": ms_id},
        "headers": {"Current-Space-Id": space_id}
    }
