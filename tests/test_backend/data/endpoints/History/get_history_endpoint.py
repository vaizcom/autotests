from typing import Optional, Dict, Any, List

def get_history_endpoint(
    space_id: str,
    kind: str,
    kind_id: str,
    limit: Optional[int] = None,
    next_cursor: Optional[int] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    event_keys: Optional[List[str]] = None,
    groups_ids: Optional[List[str]] = None,
    board_ids: Optional[List[str]] = None,
    member_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Эндпоинт для получения истории (GetHistoryInputDto).
    Пагинация курсорная: nextCursor (0 — первая страница).

    APP-5670: убраны createdBy, excludeKeys, tasksIds;
              keys переименован в eventKeys;
              добавлены limit и memberIds.
    """
    payload: Dict[str, Any] = {
        "kind": kind,
        "kindId": kind_id,
    }

    if limit is not None:
        payload["limit"] = limit
    if next_cursor is not None:
        payload["nextCursor"] = next_cursor
    if date_range_start is not None:
        payload["dateRangeStart"] = date_range_start
    if date_range_end is not None:
        payload["dateRangeEnd"] = date_range_end
    if event_keys is not None:
        payload["eventKeys"] = event_keys
    if groups_ids is not None:
        payload["groupsIds"] = groups_ids
    if board_ids is not None:
        payload["boardIds"] = board_ids
    if member_ids is not None:
        payload["memberIds"] = member_ids

    return {
        "path": "/GetHistory",
        "json": payload,
        "headers": {
            "Content-Type": "application/json",
            "Current-Space-Id": space_id,
        },
    }