from core.response_utils import short_resp


def assert_multiaction_response(resp) -> dict:
    """
    Проверяет общий контракт ответа multiaction-эндпоинтов:
    - HTTP 200
    - payload содержит success, failed, skipped — всегда массивы строк
    Возвращает payload для дальнейших проверок.
    """
    assert resp.status_code == 200, f"Ожидали 200, получили {resp.status_code}: {short_resp(resp)}"

    payload = resp.json().get("payload", {})

    for field in ("success", "failed", "skipped"):
        value = payload.get(field)
        assert isinstance(value, list), (
            f"payload.{field} должен быть массивом, получили {type(value).__name__}: {value}"
        )

    # Проверяем, что массивы не пересекаются
    success = set(payload["success"])
    failed = set(payload["failed"])
    skipped = set(payload["skipped"])
    assert not (success & failed), f"Пересечение success и failed: {success & failed}"
    assert not (success & skipped), f"Пересечение success и skipped: {success & skipped}"
    assert not (failed & skipped), f"Пересечение failed и skipped: {failed & skipped}"

    return payload
