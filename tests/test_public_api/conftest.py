import os
import time

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PUBLIC_API_BASE_URL = "https://api.vaiz.com"
PUBLIC_API_PAT = os.getenv('PUBLIC_API_PAT')


class PublicAPIClient:
    """Клиент для публичного API (GET-запросы, Bearer PAT-токен)."""

    def __init__(self, base_url: str, pat_token: str, with_retry: bool = True):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if with_retry:
            retry = Retry(
                total=2,
                backoff_factor=1,
                status_forcelist=[502, 503, 504],
                allowed_methods=["GET"],
                connect=2,
                read=0,
                respect_retry_after_header=False,
            )
            adapter = HTTPAdapter(max_retries=retry)
        else:
            adapter = HTTPAdapter()
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"Authorization": f"Bearer {pat_token}"})

    def get(self, path: str, params: dict = None, timeout=(5, 30)):
        url = f"{self.base_url}{path}"
        return self.session.get(url, params=params, timeout=timeout)


@pytest.fixture(scope="session")
def public_client():
    """Публичный API клиент с PAT-токеном. Ретраи на 502/503/504, не ретраит 429."""
    assert PUBLIC_API_PAT, "Переменная окружения PUBLIC_API_PAT не задана"
    return PublicAPIClient(base_url=PUBLIC_API_BASE_URL, pat_token=PUBLIC_API_PAT, with_retry=True)


@pytest.fixture(scope="session")
def public_client_no_retry():
    """Публичный API клиент без ретраев — для тестов рейт-лимита."""
    assert PUBLIC_API_PAT, "Переменная окружения PUBLIC_API_PAT не задана"
    return PublicAPIClient(base_url=PUBLIC_API_BASE_URL, pat_token=PUBLIC_API_PAT, with_retry=False)


@pytest.fixture(autouse=True)
def rate_limit():
    """Пауза 1 сек перед каждым тестом публичного API — соблюдение рейт-лимита 1 rps."""
    time.sleep(1)


@pytest.fixture(scope="session")
def public_space_id():
    """Space ID для публичного API. Берётся из PUBLIC_SPACE_ID."""
    space_id = os.getenv("PUBLIC_SPACE_ID")
    assert space_id, "Не задана переменная окружения PUBLIC_SPACE_ID"
    return space_id
