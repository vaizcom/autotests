import re
import time

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Sidebar
from tests.test_frontend.tests.auth.conftest import (
    home_screenshot_with_masks,
    submit_email_and_get_temp_token,
    get_otp,
)

pytestmark = [pytest.mark.frontend]


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign up with email (OTP)')
def test_sign_up_with_email(page: Page, db, assert_snapshot):
    ts = int(time.time())
    new_email = f'TST_autotest_{ts}@mailinator.com'

    with allure.step('Открытие страницы входа'):
        page.goto(f'{settings.BASE_URL}/auth/sign-in')
        page.get_by_test_id(Auth.EMAIL_INPUT).wait_for(state='visible', timeout=15000)

    with allure.step(f'Ввод нового email: {new_email}'):
        page.get_by_test_id(Auth.EMAIL_INPUT).fill(new_email)

    with allure.step('Отправка email и перехват tempToken'):
        payload = submit_email_and_get_temp_token(page)
        assert payload.get('needOTP') is True, (
            f'Ожидался needOTP=true для нового email, получено: {payload}'
        )
        temp_token = payload['tempToken']

    with allure.step('Получение OTP'):
        inbox_name = new_email.split('@')[0]
        otp_code = get_otp(inbox_name, db=db, temp_token=temp_token)

    with allure.step(f'Ввод OTP: {otp_code}'):
        page.get_by_test_id(Auth.OTP_INPUT).wait_for(state='visible', timeout=10000)
        page.get_by_test_id(Auth.OTP_INPUT).fill(otp_code)
        page.get_by_test_id(Auth.OTP_SUBMIT).click()

    with allure.step('Ожидание перехода с auth-страницы'):
        expect(page).not_to_have_url(re.compile(r'.*/auth/'), timeout=30000)

    # --- Онбординг ---
    next_btn = page.get_by_role('button', name='Next')

    with allure.step('Онбординг: ввод имени'):
        expect(page.get_by_text('What is your name?'),
               'Шаг «What is your name?» не появился — онбординг изменён или убран'
               ).to_be_visible(timeout=15000)
        page.locator('input[name="fullName"]').fill(f'{{TST}}_autotest_{ts}')
        next_btn.click()

    with allure.step('Онбординг: название Workspace (пропуск)'):
        expect(page.get_by_text('Name your Workspace'),
               'Шаг «Name your Workspace» не появился — порядок онбординга изменён'
               ).to_be_visible(timeout=10000)
        next_btn.click()

    with allure.step('Онбординг: приглашение Invite people (пропуск)'):
        expect(page.get_by_text('Invite people to your Workspace'),
               'Шаг «Invite people» не появился — порядок онбординга изменён'
               ).to_be_visible(timeout=10000)
        next_btn.click()

    with allure.step('Онбординг: помощь Book a call (пропуск)'):
        expect(page.get_by_text('Need help getting started?'),
               'Шаг «Need help getting started?» не появился — порядок онбординга изменён'
               ).to_be_visible(timeout=10000)
        next_btn.click()

    with allure.step('Онбординг: завершение'):
        expect(page.get_by_text('The workspace setup is complete!'),
               'Финальный шаг онбординга не появился — флоу изменён'
               ).to_be_visible(timeout=10000)
        page.get_by_role('button', name='Finish').click()

    with allure.step('Проверка: пользователь на Home'):
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step('Сравнение скриншота'):
        screenshot = home_screenshot_with_masks(page)
        assert_snapshot(screenshot, name='sign_up_home.png', threshold=5.0)
