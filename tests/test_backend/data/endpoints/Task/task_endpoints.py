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

def multiple_edit_tasks_endpoint(
    space_id: str,
    tasks: List[Dict[str, Any]],
    # Значения по умолчанию (None)
    taskId: Optional[str] = None,
    assignees: Optional[List[str]] = None,
    completed: Optional[bool] = None,
    dueStart: Optional[str] = None,
    dueEnd: Optional[str] = None,
    priority: Optional[str] = None,
    types: Optional[List[str]] = None,
    milestone: Optional[str] = None,
    archivedAt: Optional[str] = None,  # ISO-строка или None
) -> dict:
    """
    Эндпоинт массового редактирования задач (MultipleEditTasksInputDto).
    """
    if tasks is None:
        # Сборка одного изменения из именованных параметров.
        if not taskId:
            raise ValueError("taskId обязателен при использовании именованных параметров (без tasks=...)")

        single_change: Dict[str, Any] = {"taskId": taskId}
        # Добавляем только те поля, что заданы (не None), чтобы соответствовать Partial<>
        if assignees is not None:
            single_change["assignees"] = assignees
        if completed is not None:
            single_change["completed"] = completed
        if dueStart is not None:
            single_change["dueStart"] = dueStart
        if dueEnd is not None:
            single_change["dueEnd"] = dueEnd
        if priority is not None:
            single_change["priority"] = priority
        if types is not None:
            single_change["types"] = types
        if milestone is not None:
            single_change["milestone"] = milestone
        # archivedAt допускает None как валидное значение (сброс), поэтому ключ отправляем всегда, если аргумент передан
        if archivedAt is not None:
            single_change["archivedAt"] = archivedAt

        tasks_payload = [single_change]
    else:
        tasks_payload = tasks

    return {
        "path": "/MultipleEditTasks",
        "headers": {
            "Current-Space-Id": space_id,
            "Content-Type": "application/json",
        },
        "json": {
            "tasks": tasks,
        },
    }


def edit_task_endpoint(
    space_id: str,
    task_id: str,
    assignees: Optional[List[str]] = None,
    completed: Optional[bool] = None,
    name: Optional[str] = None,
    dueStart: Optional[str] = None,
    dueEnd: Optional[str] = None,
    priority: Optional[int] = None,
    types: Optional[List[str]] = None,
    coverImage: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Эндпоинт для редактирования одной задачи.
    """
    payload: Dict[str, Any] = {
        "taskId": task_id,                     # обязательное поле
    }

    if assignees is not None:
        payload["assignees"] = assignees
    if completed is not None:
        payload["completed"] = completed
    if name is not None:
        payload["name"] = name
    if dueStart is not None:
        payload["dueStart"] = dueStart
    if dueEnd is not None:
        payload["dueEnd"] = dueEnd
    if priority is not None:
        payload["priority"] = priority
    if types is not None:
        payload["types"] = types
    if coverImage is not None:
        payload["coverImage"] = coverImage

    return {
        "path": "/EditTask",
        "json": payload,
        "headers": {
            "Content-Type": "application/json","Current-Space-Id": space_id,
        },
    }


def edit_task_custom_field_endpoint(space_id, task_id, field_id, value):
    """
    Формирует запрос для EditTaskCustomField.
    DTO: EditTaskCustomFieldInputDto { taskId, customFieldId, value }
    """
    payload = {
        "taskId": task_id,
        "customFieldId": field_id,
        "value": value
    }
    return {
        "path": "/EditTaskCustomField",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }