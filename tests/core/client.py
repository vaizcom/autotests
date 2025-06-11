import requests


class APIClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = token
        if token:
            self.set_auth_header(token)

    def set_auth_header(self, token: str):
        self.token = token
        self.session.headers.update({'Authorization': f'Bearer {token}', 'Cookie': f'_t={token}'})

    def post(self, path: str, json: dict = None, headers: dict = None):
        url = f'{self.base_url}{path}'
        final_headers = self.session.headers.copy()
        if headers:
            final_headers.update(headers)
        return self.session.post(url, json=json, headers=final_headers)
