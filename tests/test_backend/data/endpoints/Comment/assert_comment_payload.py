
import allure

# Обязательные поля согласно IComment
COMMENT_REQUIRED_SCHEMA = {
    "_id": str,
    "documentId": str,
    "content": str,
    "authorId": str,
    "createdAt": str,
    "files": list,
    "reactions": list,
    "hasRemovedFiles": bool
}

# Опциональные поля
COMMENT_OPTIONAL_FIELDS = {
    "replyTo": str,
    "editedAt": str,
    "updatedAt": str,
    "deletedAt": str,
    "restrictGallery": bool
}

def assert_comment_payload(comment: dict, expected_document_id: str, expected_content: str):
    """
    Валидирует структуру и типы данных объекта IComment.
    """
    with allure.step("Проверка набора полей комментария (IComment)"):
        actual_keys = set(comment.keys())
        required_keys = set(COMMENT_REQUIRED_SCHEMA.keys())
        all_allowed_keys = required_keys.union(set(COMMENT_OPTIONAL_FIELDS.keys()))

        missing = required_keys - actual_keys
        extra = actual_keys - all_allowed_keys

        assert not missing, f"В комментарии отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra, f"В комментарии найдены неизвестные поля: {sorted(extra)}"

    with allure.step("Проверка типов данных полей комментария"):
        for field, expected_type in COMMENT_REQUIRED_SCHEMA.items():
            value = comment[field]
            assert isinstance(value, expected_type), (
                f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

        for field, expected_type in COMMENT_OPTIONAL_FIELDS.items():
            if field in comment:
                value = comment.get(field)
                assert isinstance(value, expected_type) or value is None, (
                    f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type} или None"
                )

    with allure.step("Бизнес-проверки созданного комментария"):
        assert comment["documentId"] == expected_document_id, \
            f"ID документа не совпадает! Ожидалось: {expected_document_id}, получено: {comment['documentId']}"
        assert comment["content"] == expected_content, \
            f"Текст комментария не совпадает! Ожидалось: {expected_content}, получено: {comment['content']}"