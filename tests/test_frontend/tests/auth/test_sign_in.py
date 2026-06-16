import re
import time

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Sidebar
from tests.test_frontend.tests.auth.conftest import (
    sign_in_and_go_to_space,
    home_screenshot_with_masks,
    submit_email_and_get_temp_token,
    get_otp,
)

pytestmark = [pytest.mark.frontend]

OTP_SIGN_IN_EMAIL = 'TST_signin_otp@mailinator.com'


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign in via email (password)')
def test_sign_in_with_email_password(page: Page, assert_snapshot):
    with allure.step('Вход и переход в autotest space'):
        sign_in_and_go_to_space(page)

    with allure.step('Сравнение скриншота'):
        # Сворачиваем раскрытые секции сайдбара → фиксируем известное состояние
        # ADD_DOC один test-id на обе секции (Space Docs / Personal Docs) → .first/.last
        collapsible = [
            (Sidebar.PROJECTS, page.get_by_test_id(Sidebar.ADD_PROJECT)),
            (Sidebar.SPACE_DOCS, page.get_by_test_id(Sidebar.ADD_DOC).first),
            (Sidebar.PERSONAL_DOCS, page.get_by_test_id(Sidebar.ADD_DOC).last),
        ]
        for section_id, child in collapsible:
            if child.is_visible(timeout=1000):
                page.get_by_test_id(section_id).click()
                page.wait_for_timeout(500)

        page.mouse.move(640, 400)
        page.wait_for_timeout(200)

        screenshot = home_screenshot_with_masks(page)
        assert_snapshot(screenshot, name='sign_in_success.png', threshold=5.0)


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign in via email (OTP)')
def test_sign_in_with_email_otp(page: Page, db, assert_snapshot):
    since_ts = time.time()

    with allure.step('Открытие страницы входа'):
        page.goto(f'{settings.BASE_URL}/auth/sign-in')
        page.get_by_test_id(Auth.EMAIL_INPUT).wait_for(state='visible', timeout=15000)

    with allure.step(f'Ввод email: {OTP_SIGN_IN_EMAIL}'):
        page.get_by_test_id(Auth.EMAIL_INPUT).fill(OTP_SIGN_IN_EMAIL)

    with allure.step('Отправка email и перехват tempToken'):
        payload = submit_email_and_get_temp_token(page)
        assert payload.get('needOTP') is True, (
            f'Ожидался needOTP=true (аккаунт без пароля), получено: {payload}. '
            f'Возможно на аккаунт {OTP_SIGN_IN_EMAIL} установлен пароль.'
        )
        temp_token = payload['tempToken']

    with allure.step('Получение OTP'):
        inbox_name = OTP_SIGN_IN_EMAIL.split('@')[0]
        otp_code = get_otp(inbox_name, since_ts=since_ts, db=db, temp_token=temp_token)

    with allure.step(f'Ввод OTP: {otp_code}'):
        page.get_by_test_id(Auth.OTP_INPUT).wait_for(state='visible', timeout=10000)
        page.get_by_test_id(Auth.OTP_INPUT).fill(otp_code)
        page.get_by_test_id(Auth.OTP_SUBMIT).click()

    with allure.step('Ожидание перехода с auth-страницы'):
        expect(page).not_to_have_url(re.compile(r'.*/auth/'), timeout=30000)

    with allure.step('Проверка: пользователь на Home'):
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step('Сравнение скриншота'):
        screenshot = home_screenshot_with_masks(page)
        assert_snapshot(screenshot, name='sign_in_otp_home.png', threshold=5.0)
