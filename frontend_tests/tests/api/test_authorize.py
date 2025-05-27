from requests import request


url = 'https://api.vaiz.dev/register'


def test_registration(generated_string):
    payload = {'email': 'mastretsova+' + generated_string + '@ibitcy.com', 'password': '123456'}
    headers = {'Content-Type': 'application/json'}

    response = request('POST', url, headers=headers, json=payload)
    assert response.status_code == 200
    assert response.json()['type'] == 'Register'
