import requests
from backend_tests.config.settings import USERS

_token_cache = {}

def get_token(role: str = "guest", api_url: str = "") -> str:
    if not api_url:
        raise ValueError("API URL must be provided")

    if role in _token_cache:
        return _token_cache[role]

    credentials = USERS.get(role)
    if not credentials:
        raise ValueError(f"Unknown role: {role}")

    login_url = f"{api_url.rstrip('/')}/Login"
    headers = {"Content-Type": "application/json"}

    #  ВАЖНО: отладка
    print(f"[LOGIN] LOGIN_URL: {login_url}")
    print(f"[LOGIN] CREDENTIALS: {credentials}")

    response = requests.post(login_url, headers=headers, json=credentials)

    # Посмотрим ответ, если что-то пошло не так
    if response.status_code != 202:
        print(f"[LOGIN] STATUS: {response.status_code}")
        print(f"[LOGIN] RESPONSE TEXT: {response.text}")

    assert response.status_code == 202, f"Login failed ({response.status_code}): {response.text}"

    token = response.json()["payload"]["token"]
    _token_cache[role] = token
    return token



def reset_token_cache(role: str = None):
    """Очистка кэша токенов — для одной роли или всех."""
    if role:
        _token_cache.pop(role, None)
    else:
        _token_cache.clear()


