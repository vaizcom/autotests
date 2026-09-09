

def assert_project_payload(payload: dict):
    """
    Проверяет структуру полезной нагрузки ответа, содержащей данные о проекте,
    включая проверку всех полей и их типов.
    """
    assert 'project' in payload, "Полезная нагрузка ответа не содержит ключа 'project'."
    project_data = payload['project']
    assert isinstance(project_data, dict), "Значение ключа 'project' должно быть словарем."

    # Обязательные поля
    assert '_id' in project_data, "В данных проекта отсутствует ключ '_id'."
    assert isinstance(project_data['_id'], str), "Поле '_id' должно быть строкой."

    assert 'name' in project_data, "В данных проекта отсутствует ключ 'name'."
    assert isinstance(project_data['name'], str), "Поле 'name' должно быть строкой."

    assert 'color' in project_data, "В данных проекта отсутствует ключ 'color'."
    assert isinstance(project_data['color'], str), "Поле 'color' должно быть строкой."

    assert 'slug' in project_data, "В данных проекта отсутствует ключ 'slug'."
    assert isinstance(project_data['slug'], str), "Поле 'slug' должно быть строкой."

    assert 'space' in project_data, "В данных проекта отсутствует ключ 'space'."
    assert isinstance(project_data['space'], str), "Поле 'space' (ID пространства) должно быть строкой."

    # Необязательные поля
    if 'icon' in project_data:
        assert isinstance(project_data['icon'], (str, type(None))), "Поле 'icon' должно быть строкой или None."
    if 'description' in project_data:
        assert isinstance(project_data['description'], (str, type(None))), "Поле 'description' должно быть строкой или None."
    if 'archivedAt' in project_data:
        assert isinstance(project_data['archivedAt'], (str, type(None))), "Поле 'archivedAt' должно быть строкой или None."
    if 'archiver' in project_data:
        assert isinstance(project_data['archiver'], (str, type(None))), "Поле 'archiver' должно быть строкой или None."
    if 'creator' in project_data:
        assert isinstance(project_data['creator'], str), "Поле 'creator' должно быть строкой."
    if 'createdAt' in project_data:
        assert 'createdAt' in project_data, "В данных проекта отсутствует ключ 'createdAt'."
        assert isinstance(project_data['createdAt'], str), "Поле 'createdAt' должно быть строкой."
    if 'updatedAt' in project_data:
        assert 'updatedAt' in project_data, "В данных проекта отсутствует ключ 'updatedAt'."
        assert isinstance(project_data['updatedAt'],
                          (str, type(None))), "Поле 'updatedAt' должно быть строкой или None."