from typing import Optional, Dict, Any, List

def get_history_endpoint(
    space_id: str,
    kind: str,
    kind_id: str,
    created_by: Optional[List[str]] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    limit: Optional[int] = None,
    last_loaded_date: Optional[int] = None,
    keys: Optional[List[str]] = None,
    exclude_keys: Optional[List[str]] = None,
    tasks_ids: Optional[List[str]] = None,
    groups_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Эндпоинт для получения истории (GetHistoryInputDto).
    """
    payload: Dict[str, Any] = {
        "kind": kind,
        "kindId": kind_id,
    }

    # Опциональные поля добавляются в payload только если они были переданы
    if created_by is not None:
        payload["createdBy"] = created_by
    if date_range_start is not None:
        payload["dateRangeStart"] = date_range_start
    if date_range_end is not None:
        payload["dateRangeEnd"] = date_range_end
    if limit is not None:
        payload["limit"] = limit
    if last_loaded_date is not None:
        payload["lastLoadedDate"] = last_loaded_date
    if keys is not None:
        payload["keys"] = keys
    if exclude_keys is not None:
        payload["excludeKeys"] = exclude_keys
    if tasks_ids is not None:
        payload["tasksIds"] = tasks_ids
    if groups_ids is not None:
        payload["groupsIds"] = groups_ids

    return {
        "path": "/GetHistory",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }