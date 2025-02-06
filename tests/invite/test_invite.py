import time

import pytest
from playwright.sync_api import expect

from core import settings


#  playwright codegen https://app.vaiz.dev/
# Пользователь логинется по инвайту
# 3.1 приглашающий высылает приглашение из Space→team→members→invite новому пользователя vaiz
#    3.1.1 на заданный email приходит письмо с сылкой-приглашением
#    3.1.2 пользователь нажимает на кнопку или ссылку в письме
#    3.1.3  войти в vaiz


# to do invaite more than one uzer
# only in chrome, cose mode window isn't correct view


@pytest.fixture()
def browser_context_args():
    return {
        'http_credentials': {
            'username': 'mastretsova+2@ibitcy.com',
            'password': '123456',
        }
    }


def test_invite_new_user(context, page, generated_string):
    page.goto(settings.BASE_URL + 'auth/sign-in')
    page.get_by_label('Email').click()
    page.get_by_label('Email').fill('mastretsova+2@ibitcy.com')
    page.get_by_label('Password').click()
    page.get_by_label('Password').fill('123456')
    page.get_by_role('button', name='Continue with Email').click()
    time.sleep(5)

    expect(page.get_by_role('link', name='Home')).to_be_attached()
    page.get_by_role('complementary').get_by_text('Team').click()
    page.get_by_role('link', name='Members').click()
    page.get_by_role('button', name='Invite').click()
    page.get_by_role('button', name='Create Invitation').click()
    page.get_by_placeholder('Enter email…').click()
    page.get_by_placeholder('Enter email…').fill('test.vaiz.by.email+' + generated_string + '@gmail.com')
    page.keyboard.press('Enter')
    page.get_by_role('button', name='Add members').click()
    page.get_by_role('button', name='Manage member').click()

    page1 = context.new_page()
    page1.goto('https://www.google.com/gmail/')
    page1.get_by_label('Телефон или адрес эл. почты').or_(page1.get_by_label('Email or phone')).click()
    page1.get_by_label('Телефон или адрес эл. почты').or_(page1.get_by_label('Email or phone')).fill(
        'test.vaiz.by.email@gmail.com'
    )
    page1.get_by_label('Email or phone').press('Enter')
    page1.get_by_label('Enter your password').click()
    page1.get_by_label('Enter your password').fill('fJ529_/!o7T~wwn!*e|')
    page1.get_by_label('Enter your password').press('Enter')
    page1.get_by_role('link', name='Join to a new Space - Join to').click()
    with page1.expect_popup() as page2:
        page1.get_by_role('link', name='Accept invite').last.click()
    page2 = page2.value
    page2.get_by_role('button', name='Enter space').click()

    expect(page.get_by_text('Active?')).to_be_attached()
