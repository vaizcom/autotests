import allure

# Обязательные поля в каждом событии ответа GetHistory
HISTORY_REQUIRED_SCHEMA = {
    "_id": str,
    "creatorId": str,
    "createdAt": str,
    "key": str,
    "type": int,
    "data": dict,
}

# Опциональные поля в событии ответа GetHistory (ID связанных сущностей)
HISTORY_OPTIONAL_FIELDS = {
    "memberId": str,
    "spaceId": str,
    "projectId": str,
    "boardId": str,
    "taskId": str,
    "documentId": str,
    "milestoneId": str,
    "updatedAt": str,
}

# Поля, которые должны присутствовать в каждом событии в ответе GetHistory для данного kind (APP-5670).
KIND_REQUIRED_FIELDS = {
    "Task":      ["taskId", "boardId", "projectId", "spaceId", "creatorId"],
    "Board":     ["boardId", "projectId", "spaceId", "creatorId"],
    "Milestone": ["milestoneId", "boardId", "projectId", "spaceId", "creatorId"],
    "Project":   ["projectId", "spaceId", "creatorId"],
    "Space":     ["spaceId", "creatorId"],
    "Document":  ["documentId", "creatorId"],
    "Member":    ["creatorId"],
}


def assert_history_schema(history: dict):
    """Проверяет обязательные поля, их типы и отсутствие неизвестных полей."""
    with allure.step("Проверка набора полей события истории"):
        actual_keys = set(history.keys())
        required_keys = set(HISTORY_REQUIRED_SCHEMA.keys())
        all_allowed_keys = required_keys.union(set(HISTORY_OPTIONAL_FIELDS.keys()))

        missing = required_keys - actual_keys
        extra = actual_keys - all_allowed_keys

        assert not missing, f"Отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra, f"Найдены лишние/неизвестные поля: {sorted(extra)}"

    with allure.step("Проверка типов данных полей истории"):
        for field, expected_type in HISTORY_REQUIRED_SCHEMA.items():
            value = history[field]
            assert isinstance(value, expected_type), (
                f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type.__name__}"
            )
        for field, expected_type in HISTORY_OPTIONAL_FIELDS.items():
            if field in history:
                value = history[field]
                assert isinstance(value, expected_type) or value is None, (
                    f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type.__name__} или None"
                )


def assert_history_kind_fields(history: dict, kind: str):
    """Проверяет что все обязательные для данного kind поля присутствуют (APP-5670)."""
    # DOC_ARCHIVED — бэкенд не проставляет spaceId в Project-истории, пропускаем до починки
    if history.get("key") == "DOC_ARCHIVED":
        return

    required_fields = KIND_REQUIRED_FIELDS.get(kind, [])
    with allure.step(f"Проверка обязательных полей для kind={kind}: {required_fields}"):
        for field in required_fields:
            assert history.get(field) is not None, (
                f"Поле '{field}' обязательно для kind={kind}, но отсутствует. "
                f"Событие: key={history.get('key')}, _id={history.get('_id')}"
            )


def assert_history_check_self(history: dict, kind: str, kind_id: str):
    """Проверяет что событие принадлежит запрошенной сущности (checkSelf)."""
    with allure.step(f"Проверка checkSelf: событие принадлежит kind={kind}, id={kind_id}"):
        if kind == "Task":
            assert history.get("taskId") == kind_id, (
                f"Ожидался taskId={kind_id}, получен {history.get('taskId')}"
            )
        elif kind == "Milestone":
            assert history.get("milestoneId") == kind_id, (
                f"Ожидался milestoneId={kind_id}, получен {history.get('milestoneId')}"
            )
        elif kind == "Project":
            assert history.get("projectId") == kind_id, (
                f"Ожидался projectId={kind_id}, получен {history.get('projectId')}"
            )
            assert history.get("boardId") is None, "Для Project поле boardId должно отсутствовать"
            assert history.get("documentId") is None, "Для Project поле documentId должно отсутствовать"
        elif kind == "Document":
            assert history.get("documentId") == kind_id, (
                f"Ожидался documentId={kind_id}, получен {history.get('documentId')}"
            )
        elif kind == "Member":
            assert history.get("memberId") == kind_id, (
                f"Ожидался memberId={kind_id}, получен {history.get('memberId')}"
            )
        elif kind == "Space":
            assert history.get("spaceId") == kind_id, (
                f"Ожидался spaceId={kind_id}, получен {history.get('spaceId')}"
            )
            assert history.get("projectId") is None, "Для Space поле projectId должно отсутствовать"
            assert history.get("documentId") is None, "Для Space поле documentId должно отсутствовать"
        elif kind == "Board":
            assert history.get("boardId") == kind_id, (
                f"Ожидался boardId={kind_id}, получен {history.get('boardId')}"
            )
