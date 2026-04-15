import allure

# Обязательные поля для IHistory
HISTORY_REQUIRED_SCHEMA = {
    "_id": str,
    "creatorId": str,
    "createdAt": str,
    "key": str,
    "type": int,
    "data": dict,
}

# Опциональные поля (ID связанных сущностей)
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


def assert_history_payload(history: dict, expected_kind: str = None, expected_kind_id: str = None):
    """
    Валидирует структуру и типы данных объекта истории, а также проверяет бизнес-правила (checkSelf).

    Args:
        history (dict): Словарь с данными события истории.
        expected_kind (str, optional): Ожидаемый тип сущности (Space, Project, Board, Task, Document, Member, Milestone).
        expected_kind_id (str, optional): Ожидаемый ID этой сущности.
    """
    with allure.step("Проверка набора полей события истории"):
        actual_keys = set(history.keys())
        required_keys = set(HISTORY_REQUIRED_SCHEMA.keys())
        all_allowed_keys = required_keys.union(set(HISTORY_OPTIONAL_FIELDS.keys()))

        missing = required_keys - actual_keys
        extra = actual_keys - all_allowed_keys

        assert not missing, f"Отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra, f"Найдены лишние/неизвестные поля: {sorted(extra)}"

    with allure.step("Проверка типов данных полей истории"):
        # Проверка обязательных полей
        for field, expected_type in HISTORY_REQUIRED_SCHEMA.items():
            value = history[field]
            assert isinstance(value, expected_type), (
                f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

        # Проверка опциональных полей (если они присутствуют и не None)
        for field, expected_type in HISTORY_OPTIONAL_FIELDS.items():
            if field in history:
                value = history.get(field)
                assert isinstance(value, expected_type) or value is None, (
                    f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type} или None"
                )

    # Аналог функции checkSelf из TypeScript
    if expected_kind and expected_kind_id:
        with allure.step(f"Бизнес-проверки контекста (checkSelf) для kind={expected_kind}"):
            if expected_kind == "Task":
                assert history.get(
                    "taskId") == expected_kind_id, f"Ожидался taskId={expected_kind_id}, получен {history.get('taskId')}"

            elif expected_kind == "Milestone":
                assert history.get(
                    "milestoneId") == expected_kind_id, f"Ожидался milestoneId={expected_kind_id}, получен {history.get('milestoneId')}"

            elif expected_kind == "Project":
                assert history.get(
                    "projectId") == expected_kind_id, f"Ожидался projectId={expected_kind_id}, получен {history.get('projectId')}"
                assert history.get("boardId") is None, "Для Project поле boardId должно отсутствовать (или быть None)"
                assert history.get(
                    "documentId") is None, "Для Project поле documentId должно отсутствовать (или быть None)"

            elif expected_kind == "Document":
                assert history.get(
                    "documentId") == expected_kind_id, f"Ожидался documentId={expected_kind_id}, получен {history.get('documentId')}"

            elif expected_kind == "Member":
                assert history.get(
                    "memberId") == expected_kind_id, f"Ожидался memberId={expected_kind_id}, получен {history.get('memberId')}"

            elif expected_kind == "Space":
                assert history.get(
                    "spaceId") == expected_kind_id, f"Ожидался spaceId={expected_kind_id}, получен {history.get('spaceId')}"
                assert history.get("projectId") is None, "Для Space поле projectId должно отсутствовать (или быть None)"
                assert history.get(
                    "documentId") is None, "Для Space поле documentId должно отсутствовать (или быть None)"

            elif expected_kind == "Board":
                assert history.get(
                    "boardId") == expected_kind_id, f"Ожидался boardId={expected_kind_id}, получен {history.get('boardId')}"