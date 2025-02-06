import random
import string
from datetime import time
import time
import allure
import pytest
from requests import request

from core import settings
from core.settings import API_URL


@pytest.fixture
def generated_string():
    length = 4
    str_characters = '!#$%^&*' + string.ascii_lowercase + string.digits
    generated_string = ''.join(random.choice(str_characters) for _ in range(length))
    return generated_string


# ["session", "package", "module", "class", "function"]
@pytest.fixture(scope='session')
def browser_token():
    payload = {"email": "mastretsova+2@ibitcy.com", "password": "123456"}
    headers = {
        'currentSpaceId': '667433ff21f760c6446bc0e2',
        'Content-Type': 'application/json'
    }
    response = request('POST', API_URL + "/Login", headers=headers, json=payload)
    payload = response.json()['payload']
    return payload['token']


@pytest.fixture(scope='session')
def browser_context_args(browser_context_args, browser_token):
    return {
        **browser_context_args,
        'storage_state': {
            'cookies': [
                {
                    'name': '_t',
                    'value': browser_token,
                    'url': 'https://app.vaiz.dev',
                },
            ]
        },
    }

@pytest.fixture(scope='function')
def open_task_drawer(browser_context_args, page):
    with allure.step('Launching the app'):
        page.goto(settings.BASE_URL)
    with allure.step('Open Board'):
        page.get_by_role('navigation').get_by_text('Project 1').click()
        page.get_by_role('link', name='autotest_dont_tuch').click()
    with allure.step('Add task'):
        page.get_by_role('button', name='Add task', exact=True).first.click()
        task = 'autotest ' + str(time.asctime())
        page.get_by_placeholder('Enter title...').fill(task)
        page.get_by_role('button', name='Add task', exact=True).first.click()
    with allure.step('Open task_drawer'):
        task_drawer = page.get_by_role('button', name=task).click()
    return task_drawer

# @pytest.fixture()
# def browser_context_args():
#     return {
#         'http_credentials': {
#             'username': 'test.vaiz.by.email@gmail.com',
#             'password': 'fJ529_/!o7T~wwn!*e|',
#         }
#     }


# @pytest.fixture(scope="session")
# def browser_context_args(browser_context_args):
#     return {
#         **browser_context_args,
#         "storage_state": {
#             "cookies": [
#                 {
#                     "name": "_t",
#                     "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
#                     eyJpZCI6IjY2NDM5YmU1YTU0ZTkzNjA5ZTk3NGEyNSIsIm
#                     lhdCI6MTcxNTcwNjg1MywiZXhwIjozMzI1MTcwNjg1M30.
#                     6MnZuzdiBGHnN0JksJUva3CiMjt2bCNf7HU0L0JsMa4",
#                     "url": "https://app.vaiz.dev/",
#                 },
#             ]
#         },
#     }




#
# @pytest.fixture(scope="session")
# def browser_context_args(browser_context_args, playwright):
#     iphone_11 = playwright.devices['iPhone 11 Pro']
#     return {
#         **browser_context_args,
#         **iphone_11,
#     }