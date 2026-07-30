import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class APIClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=2, status_forcelist=[429, 502, 503, 504], allowed_methods=["POST"], connect=0, read=0, respect_retry_after_header=False)
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.token = token
        if token:
            self.set_auth_header(token)

    def set_auth_header(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}', 'Cookie': f'_t={token}'})

    def post(self, path: str, json: dict = None, headers: dict = None, timeout=(5, 30), **kwargs):
        url = f'{self.base_url}{path}'
        final_headers = self.session.headers.copy()
        if headers:
            final_headers.update(headers)
        return self.session.post(url, json=json, headers=final_headers, timeout=timeout, **kwargs)
