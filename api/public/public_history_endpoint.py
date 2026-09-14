from typing import Optional, List, Dict, Any


def public_history_endpoint(
    space_id: str,
    kind: str,
    kind_id: str,
    limit: Optional[int] = None,
    next_cursor: Optional[int] = None,
    date_range_start: Optional[str] = None,
    date_range_end: Optional[str] = None,
    event_keys: Optional[List[str]] = None,
    group_ids: Optional[List[str]] = None,
    board_ids: Optional[List[str]] = None,
    member_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    GET /public/v1/history

    Публичный API истории. Использует query params (не JSON body).
    Пагинация курсорная: nextCursor (отсутствует — первая страница).
    Rate limit: 1 rps.

    dateRangeStart/dateRangeEnd — фильтр по createdAt событий, полуоткрытый интервал [start, end).
    Формат ISO 8601: "2026-08-14T09:03:00.000Z". Поддерживает точность до миллисекунд.
    Не путать с dueStart/dueEnd задач — там бэкенд нормализует время (00:00:00 / 23:59:59).
    """
    params: Dict[str, Any] = {
        "spaceId": space_id,
        "kind": kind,
        "kindId": kind_id,
    }

    if limit is not None:
        params["limit"] = limit
    if next_cursor is not None:
        params["nextCursor"] = next_cursor
    if date_range_start is not None:
        params["dateRangeStart"] = date_range_start
    if date_range_end is not None:
        params["dateRangeEnd"] = date_range_end
    if event_keys is not None:
        params["eventKeys"] = event_keys
    if group_ids is not None:
        params["groupIds"] = group_ids
    if board_ids is not None:
        params["boardIds"] = board_ids
    if member_ids is not None:
        params["memberIds"] = member_ids

    return {
        "path": "/public/v1/history",
        "params": params,
    }
