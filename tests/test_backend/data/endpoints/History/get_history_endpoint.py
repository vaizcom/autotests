from typing import Optional, Dict, Any, List

def get_history_endpoint(
    space_id: str,
    kind: str,
    kind_id: str,
    next_cursor: Optional[int] = None,
    created_by: Optional[List[str]] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    keys: Optional[List[str]] = None,
    exclude_keys: Optional[List[str]] = None,
    tasks_ids: Optional[List[str]] = None,
    groups_ids: Optional[List[str]] = None,
    board_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Эндпоинт для получения истории (GetHistoryInputDto).
    Пагинация курсорная: nextCursor (0 — первая страница).
    """
    payload: Dict[str, Any] = {
        "kind": kind,
        "kindId": kind_id,
    }

    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    if created_by is not None:
        payload["createdBy"] = created_by
    if date_range_start is not None:
        payload["dateRangeStart"] = date_range_start
    if date_range_end is not None:
        payload["dateRangeEnd"] = date_range_end
    if keys is not None:
        payload["keys"] = keys
    if exclude_keys is not None:
        payload["excludeKeys"] = exclude_keys
    if tasks_ids is not None:
        payload["tasksIds"] = tasks_ids
    if groups_ids is not None:
        payload["groupsIds"] = groups_ids
    if board_ids is not None:
        payload["boardIds"] = board_ids

    return {
        "path": "/GetHistory",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }