import os

from pymongo import MongoClient

import pytest
import requests
import urllib3


def pytest_configure(config):
    """Разделяет allure-results для backend и frontend тестов (только локально)."""
    if os.getenv("CI"):
        return
    if not getattr(config.option, "allure_report_dir", None):
        return

    args = " ".join(str(a) for a in (config.option.file_or_dir or []))
    markexpr = getattr(config.option, "markexpr", "") or ""

    if "test_frontend" in args or "frontend" in markexpr:
        config.option.allure_report_dir = "allure-results-frontend"
    elif "test_backend" in args or "backend" in markexpr:
        config.option.allure_report_dir = "allure-results-backend"


@pytest.fixture(scope="session")
def mongo_client():
    """Создает подключение к MongoDB на время всего прогона тестов."""
    mongo_uri = os.getenv("MONGO_URI")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)

    yield client

    client.close()


@pytest.fixture(scope="session")
def db(mongo_client):
    """Возвращает конкретную базу данных для работы."""
    db_name = os.getenv("MONGO_DB_NAME")
    return mongo_client[db_name]


@pytest.fixture(scope="session", autouse=True)
def global_ssl_settings():
    """
    Глобальная настройка SSL для всех тестов.
    Если стенд 'local', отключает верификацию сертификатов для всех запросов requests.
    """
    stand_name = os.getenv("TEST_STAND_NAME", "local")

    if stand_name == "local":
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        original_request = requests.Session.request

        def patched_request(self, method, url, *args, **kwargs):
            if 'verify' not in kwargs:
                kwargs['verify'] = False
            return original_request(self, method, url, *args, **kwargs)

        requests.Session.request = patched_request
