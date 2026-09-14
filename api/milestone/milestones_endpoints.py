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
            "Content-Type": "application/json",
            'Current-Space-Id': space_id,
        },
        "json": payload,
    }

def get_milestone_endpoint(ms_id: str, space_id: str):
    return {
        "path": "/GetMilestone",
        "json": {"_id": ms_id},
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id}
    }


def create_milestone_endpoint(
        space_id: str,
        board: str,
        name: str,
        project: str = None,
        due_start: str = None,
        due_end: str = None,
        description: str = None
):
    """
    Эндпоинт для создания майлстоуна (CreateMilestoneInputDto).
    """
    payload = {
        "board": board,
        "name": name,
    }

    if project is not None:
        payload["project"] = project
    if due_start is not None:
        payload["dueStart"] = due_start
    if due_end is not None:
        payload["dueEnd"] = due_end
    if description is not None:
        payload["description"] = description

    return {
        "path": "/CreateMilestone",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }

def archive_milestone_endpoint(space_id: str, milestone_id: str):
    """
    Эндпоинт для архивации майлстоуна (ArchiveMilestone).
    """
    return {
        "path": "/ArchiveMilestone",
        "json": {"milestoneId": milestone_id},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }