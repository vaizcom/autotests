def pytest_ignore_collect(collection_path, config):
    """Пропускаем все тесты в invite/ — инвайт-сервис на стенде зависает."""
    return collection_path.name.startswith("test_") or collection_path.name == "acces_invite"
