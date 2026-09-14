import allure

def assert_space_payload(space: dict, expected_space_id: str = None):
    """
    Проверяет структуру и типы данных объекта space.
    Учитывает как обязательные, так и опциональные (например, invited) поля.
    """
    # Обязательные поля
    expected_schema = {
        "_id": str,
        "name": str,
        "avatar": str,
        "avatarMode": int,
        "color": dict,
        "createdAt": str,
        "creator": str,
        "isForeign": bool,
        "updatedAt": str,
    }

    # Опциональные поля и их ожидаемые типы
    optional_schema = {
        "invited": bool,
        "inviteCode": str,
        "plan": str,
    }

    with allure.step(f"Проверка схемы пространства c _id={space.get('_id', 'N/A')}"):
        actual_keys = set(space.keys())
        expected_keys = set(expected_schema.keys())
        all_possible_keys = expected_keys.union(set(optional_schema.keys()))

        missing = expected_keys - actual_keys
        extra = actual_keys - all_possible_keys

        assert not missing, f"Space с _id={space.get('_id', 'N/A')} - Отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra, f"Space с _id={space.get('_id', 'N/A')} - Найдены неизвестные лишние поля: {sorted(extra)}"

        # Проверка типов обязательных полей
        for field, expected_type in expected_schema.items():
            value = space[field]
            assert isinstance(value, expected_type), (
                f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

        # Проверка типов присутствующих опциональных полей
        for field, expected_type in optional_schema.items():
            if field in space:
                value = space[field]
                assert isinstance(value, expected_type), (
                    f"Опциональное поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
                )

        # Дополнительная проверка структуры color
        if "color" in space:
            color_data = space["color"]
            assert "color" in color_data and isinstance(color_data["color"], str), "Ошибка: некорректен ключ 'color.color'"
            assert "isDark" in color_data and isinstance(color_data["isDark"], bool), "Ошибка: некорректен ключ 'color.isDark'"

        # Проверка соответствия ID, если передан
        if expected_space_id:
            assert space["_id"] == expected_space_id, f"Ожидался _id пространства {expected_space_id}, но получен {space['_id']}"
