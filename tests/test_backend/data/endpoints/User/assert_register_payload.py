import allure

# Схема для объекта цвета
COLOR_SCHEMA = {
    "color": str,
    "isDark": bool
}

# Схемы для конкретных секций внутри limits
LIMITS_SECTION_SCHEMAS = {
    "storage": {
        "available": int,
        "used": int
    },
    "seats": {
        "available": int,
        "used": int
    },
    "automation": {
        "available": int,
        "used": int,
        "resetDate": str,
        "resetInterval": str
    },
    "documentHistory": {
        "available": int
    }
}

# Схема для объекта тарифа (Plan)
PLAN_SCHEMA = {
    "space": str,
    "predefinedPlan": str,
    "limits": dict,
    "features": list,
    "isEarlyBird": bool,
    "earlyBirdExpiresAt": (str, type(None)),
    "planChangedAt": str,
    "_id": str,
    "createdAt": str,
    "updatedAt": str
}

# Схема для объекта пространства (Space)
SPACE_SCHEMA = {
    "name": str,
    "avatarMode": int,
    "color": dict,
    "_id": str,
    "avatar": str,
    "creator": str,
    "plan": dict,
    "createdAt": str,
    "updatedAt": str,
    "isForeign": bool
}


def assert_register_payload(response: dict):
    """
    Валидирует структуру и типы данных ответа при регистрации.

    Args:
        response (dict): Полный ответ от сервера (включая type и payload).
    """

    with allure.step("Проверка типа сообщения и наличия payload"):
        assert response.get("type") == "Register", f"Ожидался тип 'Register', получен '{response.get('type')}'"
        assert "payload" in response, "В ответе отсутствует поле 'payload'"
        assert isinstance(response["payload"], dict), "Поле 'payload' должно быть словарем"

    payload = response["payload"]

    with allure.step("Проверка базовых полей payload"):
        assert isinstance(payload.get("token"), str), "Поле 'token' должно быть строкой"
        assert isinstance(payload.get("space"), dict), "Поле 'space' должно быть словарем"

    space = payload["space"]

    with allure.step("Проверка структуры и типов полей пространства (Space)"):
        expected_schema = SPACE_SCHEMA
        actual_keys = set(space.keys())
        expected_keys = set(expected_schema.keys())

        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys

        assert not missing, f"В объекте 'space' отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra, f"В объекте 'space' найдены лишние поля: {sorted(extra)}"

        for field, expected_type in expected_schema.items():
            value = space[field]
            assert isinstance(value, expected_type), (
                f"Поле space['{field}'] имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

    with allure.step("Проверка вложенного объекта Color"):
        color_obj = space["color"]
        for field, expected_type in COLOR_SCHEMA.items():
            assert field in color_obj, f"В объекте 'color' отсутствует поле '{field}'"
            assert isinstance(color_obj[field], expected_type), (
                f"Поле color['{field}'] имеет неверный тип"
            )

    with allure.step("Проверка структуры и типов полей тарифа (Plan)"):
        plan = space["plan"]
        expected_plan_keys = set(PLAN_SCHEMA.keys())
        actual_plan_keys = set(plan.keys())

        missing_plan = expected_plan_keys - actual_plan_keys
        # В плане могут быть дополнительные поля, но проверяем, что нет пропущенных обязательных
        assert not missing_plan, f"В объекте 'plan' отсутствуют обязательные поля: {sorted(missing_plan)}"

        for field, expected_type in PLAN_SCHEMA.items():
            value = plan[field]
            assert isinstance(value, expected_type), (
                f"Поле plan['{field}'] имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

    with allure.step("Детальная проверка структуры лимитов (Limits)"):
        limits = plan["limits"]

        # Проверяем наличие всех ожидаемых секций (storage, seats, etc.)
        expected_sections = set(LIMITS_SECTION_SCHEMAS.keys())
        actual_sections = set(limits.keys())

        missing_sections = expected_sections - actual_sections
        assert not missing_sections, f"В объекте 'limits' отсутствуют обязательные секции: {missing_sections}"

        # Проходим по каждой секции и проверяем её внутренние поля
        for section_name, section_schema in LIMITS_SECTION_SCHEMAS.items():
            current_section = limits[section_name]
            assert isinstance(current_section, dict), f"Секция limits['{section_name}'] должна быть словарем"

            for field, expected_type in section_schema.items():
                assert field in current_section, f"В лимитах '{section_name}' отсутствует поле '{field}'"
                value = current_section[field]
                assert isinstance(value, expected_type), (
                    f"Поле limits['{section_name}']['{field}'] имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
                )

    with allure.step("Бизнес-проверка связей ID"):
        # ID пространства внутри плана должно совпадать с ID самого пространства
        assert plan["space"] == space["_id"], "ID пространства в объекте Plan не совпадает с ID Space"
        # Creator должен быть валидной строкой (не пустой)
        assert space["creator"], "Поле creator не должно быть пустым"