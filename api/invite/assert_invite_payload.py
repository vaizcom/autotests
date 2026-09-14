import allure

INVITE_SCHEMA = {
    "nickName": str,
    "avatar": (str, type(None)),
    "avatarMode": int,
    "color": dict,
    "email": str,
    "phoneNumber": str,
    "fullName": str,
    "_id": str,
    "space": str,
    "status": str,
    "invitedBy": str,
    "joinedDate": str,
    "updatedAt": str
}


def assert_invite_payload(invite: dict, space_id: str, email: str, expected_full_name: str = ""):
    """
    Валидирует структуру и типы данных объекта invite, возвращаемого при приглашении в спейс.
    """
    with allure.step("Проверка полного совпадения набора полей инвайта"):
        expected_schema = INVITE_SCHEMA
        actual_keys = set(invite.keys())
        expected_keys = set(expected_schema.keys())
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys

        assert not missing, f"Отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra, f"Найдены лишние поля: {sorted(extra)}"

    with allure.step("Проверка типов данных всех полей инвайта"):
        for field, expected_type in expected_schema.items():
            value = invite[field]
            assert isinstance(value, expected_type), (
                f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

    with allure.step("Проверка структуры вложенного объекта color"):
        color_obj = invite["color"]
        assert "color" in color_obj, "В объекте color отсутствует ключ 'color'"
        assert "isDark" in color_obj, "В объекте color отсутствует ключ 'isDark'"
        assert isinstance(color_obj["color"], str), "color.color должен быть строкой"
        assert isinstance(color_obj["isDark"], bool), "color.isDark должен быть boolean"

    with allure.step("Бизнес-проверки стабильных значений инвайта"):
        assert invite[
                   "space"] == space_id, f"ID спейса не совпадает. Ожидался: {space_id}, Фактический: {invite['space']}"
        assert invite["email"] == email, f"Email не совпадает. Ожидался: {email}, Фактический: {invite['email']}"
        assert invite["status"] == "Invited", f"Статус должен быть 'Invited', но получен '{invite['status']}'"
        assert invite[
                   "fullName"] == expected_full_name, f"Имя не совпадает. Ожидалось: '{expected_full_name}', Фактическое: '{invite['fullName']}'"