import requests
from config.settings import USERS, API_URL

_token_cache = {}


def get_token(role: str = 'guest') -> str:
    if role in _token_cache:
        return _token_cache[role]

    credentials = USERS.get(role)
    if not credentials:
        raise ValueError(f'Unknown role: {role}')

    base_url = API_URL.rstrip('/')
    headers = {'Content-Type': 'application/json'}

    # Шаг 1: AuthWithEmail
    resp = requests.post(
        f"{base_url}/AuthWithEmail",
        headers=headers,
        json={"email": credentials['email']}
    )
    assert resp.status_code == 200, f'AuthWithEmail failed ({resp.status_code}): {resp.text}'

    payload = resp.json().get("payload", {})
    temp_token = payload.get("tempToken")
    assert temp_token, f'tempToken отсутствует в ответе AuthWithEmail для {role}'

    # Шаг 2: VerifyPassword
    resp = requests.post(
        f"{base_url}/VerifyPassword",
        headers=headers,
        json={"tempToken": temp_token, "password": credentials['password']}
    )
    assert resp.status_code == 200, f'VerifyPassword failed ({resp.status_code}): {resp.text}'

    token = resp.json().get("payload", {}).get("authToken")
    assert token, f'authToken отсутствует в ответе VerifyPassword для {role}'

    _token_cache[role] = token
    return token


def reset_token_cache(role: str = None):
    """Очистка кэша токенов — для одной роли или всех."""
    if role:
        _token_cache.pop(role, None)
    else:
        _token_cache.clear()
