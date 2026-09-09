"""
Транспортный слой — HTTP-клиент для internal API.

Не знает про бизнес-логику: получает path, json, headers из endpoint-функций,
подставляет токен и отправляет запрос. Связка: client.post(**endpoint_function(...))
"""

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class APIClient:
    """HTTP-клиент для internal API (RPC-стиль, только POST).

    - Подставляет JWT-токен в заголовки (Bearer + Cookie)
    - Retry: 2 попытки при 429/502/503/504
    - Таймаут: 5 сек на подключение, 30 сек на ответ
    """

    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=2, status_forcelist=[429, 502, 503, 504], allowed_methods=["POST"], connect=2, read=0, respect_retry_after_header=False)
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.token = None
        if token:
            self.set_auth_header(token)

    def set_auth_header(self, token: str):
        """Устанавливает токен в заголовки сессии.
        Bearer — стандарт API, Cookie — совместимость с фронтом.
        """
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}', 'Cookie': f'_t={token}'})

    def post(self, path: str, json: dict = None, headers: dict = None, timeout=(5, 30), **kwargs):
        """Отправляет POST-запрос. path и json приходят из endpoint-функций."""
        url = f'{self.base_url}{path}'
        return self.session.post(url, json=json, headers=headers, timeout=timeout, **kwargs)
