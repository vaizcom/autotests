import requests
from tests.config.settings import USERS, API_URL

_token_cache = {}


def get_token(role: str = 'guest') -> str:
    if role in _token_cache:
        return _token_cache[role]

    credentials = USERS.get(role)
    if not credentials:
        raise ValueError(f'Unknown role: {role}')

    login_url = f"{API_URL.rstrip('/')}/Login"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(login_url, headers=headers, json=credentials)

    assert response.status_code == 202, f'Login failed ({response.status_code}): {response.text}'

    token = response.json()['payload']['token']
    _token_cache[role] = token
    return token


def reset_token_cache(role: str = None):
    """Очистка кэша токенов — для одной роли или всех."""
    if role:
        _token_cache.pop(role, None)
    else:
        _token_cache.clear()
