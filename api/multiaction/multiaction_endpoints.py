from typing import Optional, List, Dict, Any


def multiple_edit_tasks_endpoint(
    space_id: str,
    tasks_ids: List[str],
    completed: Optional[bool] = None,
    priority: Optional[int] = None,
    types: Optional[List] = None,
    due_start: Optional[str] = None,
    due_end: Optional[str] = None,
    assignees: Optional[List] = None,
) -> Dict[str, Any]:
    """
    Массовое редактирование задач (MultipleEditTasksInputDto).
    Одно действие применяется ко всем задачам из tasksIds.
    """
    payload: Dict[str, Any] = {"tasksIds": tasks_ids}

    if completed is not None:
        payload["completed"] = completed
    if priority is not None:
        payload["priority"] = priority
    if types is not None:
        payload["types"] = types
    if due_start is not None:
        payload["dueStart"] = due_start
    if due_end is not None:
        payload["dueEnd"] = due_end
    if assignees is not None:
        payload["assignees"] = assignees

    return {
        "path": "/MultipleEditTasks",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def multiple_edit_tasks_custom_field_endpoint(
    space_id: str,
    tasks_ids: List[str],
    custom_field_id: str,
    value: Any,
) -> Dict[str, Any]:
    """
    Массовое редактирование кастомного поля (MultipleEditTasksCustomFieldInputDto).
    """
    return {
        "path": "/MultipleEditTasksCustomField",
        "json": {
            "tasksIds": tasks_ids,
            "customFieldId": custom_field_id,
            "value": value,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def multiple_archive_tasks_endpoint(
    space_id: str,
    tasks_ids: List[str],
) -> Dict[str, Any]:
    """
    Массовая архивация задач (MultipleArchiveTasksInputDto).
    """
    return {
        "path": "/MultipleArchiveTasks",
        "json": {"tasksIds": tasks_ids},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def multiple_unarchive_tasks_endpoint(
    space_id: str,
    tasks_ids: List[str],
) -> Dict[str, Any]:
    """
    Массовая разархивация задач (MultipleUnarchiveTasksInputDto).
    """
    return {
        "path": "/MultipleUnarchiveTasks",
        "json": {"tasksIds": tasks_ids},
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def multiple_move_tasks_endpoint(
    space_id: str,
    tasks_ids: List[str],
    board_id: str,
    to_group_id: str,
) -> Dict[str, Any]:
    """
    Массовое перемещение задач (MultipleMoveTasksInputDto).
    Все задачи перемещаются в начало указанной группы.
    """
    return {
        "path": "/MultipleMoveTasks",
        "json": {
            "tasksIds": tasks_ids,
            "boardId": board_id,
            "toGroupId": to_group_id,
        },
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }
