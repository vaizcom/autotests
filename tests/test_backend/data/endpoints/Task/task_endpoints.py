from typing import Optional, Dict, Any, List

# Константа для дефолтного имени задачи
DEFAULT_TASK_NAME = "Untitled task"


def create_task_endpoint(
    space_id: str,
    board: str,
    name: Optional[str] = None,
    types: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    due_start: Optional[str] = None,
    due_end: Optional[str] = None,
    priority: Optional[int] = None,
    completed: Optional[bool] = None,  # булево поле
    group: Optional[str] = None,
    milestones: Optional[List[str]] = None,
    parent_task: Optional[str] = None,
    files: Optional[List[Dict[str, Any]]] = None,
    description: Optional[str] = None,
    index: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "board": board,                     # обязательное поле
        "name": name or DEFAULT_TASK_NAME,  # дефолтное значение
    }

    # Опциональные поля
    if types: payload["types"] = types
    if assignees: payload["assignees"] = assignees
    if due_start: payload["dueStart"] = due_start
    if due_end: payload["dueEnd"] = due_end
    if priority is not None: payload["priority"] = priority
    if completed is not None: payload["completed"] = completed  # булево поле
    if group: payload["group"] = group
    if milestones: payload["milestones"] = milestones
    if parent_task: payload["parentTask"] = parent_task
    if files: payload["files"] = files
    if description: payload["description"] = description
    if index is not None: payload["index"] = index

    return {
        "path": "/CreateTask",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }


def delete_task_endpoint(task_id: str, space_id: str):
    return {
        "path": "/DeleteTask",
        "json": {"taskId": task_id},
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id}
    }


def get_tasks_endpoint(space_id: str, **optional_params):
    payload = {k: v for k, v in optional_params.items() if v is not None}
    return {
        "path": "/GetTasks",
        "json": payload if payload else {},
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id}
    }

def get_task_endpoint(slug_id: str, space_id: str):
    return {
        "path": "/GetTask",
        "json": {"slug": slug_id},
        "headers": {"Content-Type": "application/json", "Current-Space-Id": space_id}
    }