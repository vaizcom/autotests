from typing import Optional, Dict, Any, List


def create_task_endpoint(
    space_id: str,
    name: Optional[str] = None,
    types: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    due_start: Optional[str] = None,
    due_end: Optional[str] = None,
    priority: Optional[int] = None,
    completed: Optional[bool] = None,
    group: Optional[str] = None,
    board: Optional[str] = None,
    milestones: Optional[List[str]] = None,
    parent_task: Optional[str] = None,
    files: Optional[List[Dict[str, Any]]] = None,
    description: Optional[str] = None,
    index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Формирует данные для вызова эндпоинта создания задачи.

    Поля соответствуют CreateTaskInputDto:
      - name, types, assignees, dueStart, dueEnd, priority, completed,
        group, board, milestones, parentTask, files, description, index
    """
    payload: Dict[str, Any] = {}

    if name is not None:
        payload['name'] = name
    if types is not None:
        payload['types'] = types
    if assignees is not None:
        payload['assignees'] = assignees
    if due_start is not None:
        payload['dueStart'] = due_start
    if due_end is not None:
        payload['dueEnd'] = due_end
    if priority is not None:
        payload['priority'] = priority
    if completed is not None:
        payload['completed'] = completed
    if group is not None:
        payload['group'] = group
    if board is not None:
        payload['board'] = board
    if milestones is not None:
        payload['milestones'] = milestones
    if parent_task is not None:
        payload['parentTask'] = parent_task
    if files is not None:
        payload['files'] = files
    if description is not None:
        payload['description'] = description
    if index is not None:
        payload['index'] = index

    return {
        'path': '/CreateTask',
        'json': payload,
        'headers': {
            'Content-Type': 'application/json',
            'Current-Space-Id': space_id,
        },
    }
