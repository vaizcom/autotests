import allure

def assert_task_payload(task: dict, board_id: str, project_id: str):
    """
    Валидирует структуру и типы данных задачи, а также проверяет бизнес-правила.

    Args:
        task (dict): Словарь с данными задачи для валидации.
        board_id (str): Ожидаемый идентификатор доски для бизнес-проверки.
        project_id (str): Ожидаемый идентификатор проекта для бизнес-проверки.
    """
    with allure.step("Проверка полного совпадения набора полей задачи"):
        expected_schema = {
            # строки
            "_id": str,
            "name": str,
            "group": str,
            "board": str,
            "project": str,
            "hrid": str,
            "creator": str,
            "createdAt": str,
            "updatedAt": str,
            "document": str,
            # "editor": str, # Убрано из обязательной схемы, т.к. проверяется отдельно

            # допускают None или строку
            "parentTask": (str, type(None)),
            "archiver": (str, type(None)),
            "dueStart": (str, type(None)),
            "dueEnd": (str, type(None)),
            "archivedAt": (str, type(None)),
            "completedAt": (str, type(None)),
            "deleter": (str, type(None)),
            "deletedAt": (str, type(None)),
            "milestone": (str, type(None)),  #  Will be deprecated in next versions
            # булево
            "completed": bool,
            # числа
            "priority": int,
            # массивы
            "types": list,
            "assignees": list,
            "subtasks": list,
            "milestones": list,
            "rightConnectors": list,
            "leftConnectors": list,
            "customFields": list,
            # словари
            "followers": dict,
        }
        actual_keys = set(task.keys())
        expected_keys = set(expected_schema.keys())
        missing = expected_keys - actual_keys
        extra = actual_keys - expected_keys
        assert not missing, f"Отсутствуют обязательные поля: {sorted(missing)}"
        assert not extra - {"editor"}, f"Найдены лишние поля: {sorted(extra - {'editor'})}"
        # "editor" допустим как дополнительное поле
        if "editor" in actual_keys:
            assert isinstance(task["editor"], str), "Поле 'editor' (если присутствует) должно быть строкой"

    with allure.step("Проверка типов данных всех полей задачи"):
        for field, expected_type in expected_schema.items():
            value = task[field]
            assert isinstance(value, expected_type), (
                f"Поле '{field}' имеет неверный тип: {type(value).__name__}, ожидается {expected_type}"
            )

    with allure.step("Дополнительные проверки содержимого коллекций"):
        # Массивы строк
        list_of_strings_fields = [
            "assignees", "subtasks", "milestones",
            "rightConnectors", "leftConnectors", "types", "customFields"
        ]
        for f in list_of_strings_fields:
            assert isinstance(task[f], list), f"Поле '{f}' должно быть массивом"
            assert all(isinstance(x, str) for x in task[f]), f"Элементы поля '{f}' должны быть строками"
        # followers: ключи и значения строки
        assert all(isinstance(k, str) for k in task["followers"].keys()), "Ключи 'followers' должны быть строками"
        assert all(isinstance(v, str) for v in task["followers"].values()), "Значения 'followers' должны быть строками"

    with allure.step("Бизнес-проверки стабильных значений"):
        assert task["board"] == board_id, "Ошибка: неверное значение поля 'board'"
        assert task["project"] == project_id, "Ошибка: неверное значение поля 'project'"