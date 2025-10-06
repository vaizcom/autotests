import requests


def create_token(owner_token, main_space, token_name):
    """
    Выполняет POST-запрос на создание персонального access-токена.
    Возвращает response.
    """
    return requests.post(
        "https://vaiz-api-uat.vaiz.dev/v4/CreatePersonalAccessToken",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Current-Space-Id": main_space,
            "Content-Type": "application/json"
        },
        json={"name": token_name}
    )

def get_tokens(owner_token, main_space):
    """
    Выполняет POST-запрос на получение списка персональных access-токенов.
    Тело запроса пустое. Возвращает response.
    """
    return requests.post(
        "https://vaiz-api-uat.vaiz.dev/v4/GetPersonalAccessTokens",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Current-Space-Id": main_space,
            "Content-Type": "application/json"
        },
        json={}
    )

def delete_personal_access_token(owner_token, main_space, token_id):
    """
    Выполняет POST-запрос на удаление персонального access-токена.
    Возвращает response.
    """
    return requests.post(
        "https://vaiz-api-uat.vaiz.dev/v4/DeletePersonalAccessToken",
        headers={
            "Authorization": f"Bearer {owner_token}",
            "Current-Space-Id": main_space,
            "Content-Type": "application/json"
        },
        json={"tokenId": token_id}
    )
