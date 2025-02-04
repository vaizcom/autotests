from requests import request
from core.settings import API_URL


def test_login():
    payload = {'email': 'mastretsova+2@ibitcy.com', 'password': '123456'}
    headers = {'currentSpaceId': '667433ff21f760c6446bc0e2', 'Content-Type': 'application/json'}
    response = request('POST', API_URL + '/Login', headers=headers, json=payload)

    assert response.status_code == 202
    payload = response.json()['payload']
    assert payload['token']
    print(str(payload['token']))
    return payload['token']
