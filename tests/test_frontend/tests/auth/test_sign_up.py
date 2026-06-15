import base64
import json
import re
import time
import urllib.parse

import allure
import pytest
import requests
from bson import ObjectId
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Sidebar
from tests.test_frontend.core.settings import FRONTEND_STAND
from tests.test_frontend.tests.auth.conftest import home_screenshot_with_masks

pytestmark = [pytest.mark.frontend]

MAILINATOR_API = 'https://api.mailinator.com/api/v2/domains/public/inboxes'


def _submit_email_and_get_temp_token(page) -> str:
    """Кликает Submit на email-шаге, перехватывает ответ AuthWithEmail и возвращает tempToken."""
    captured = {}

    def _capture(response):
        try:
            body = response.json()
            if isinstance(body, dict) and body.get('type') == 'AuthWithEmail':
                captured['data'] = body
        except Exception:
            pass

    page.on('response', _capture)
    page.get_by_test_id(Auth.EMAIL_SUBMIT).click()
    page.get_by_test_id(Auth.OTP_INPUT).wait_for(state='visible', timeout=15000)
    page.remove_listener('response', _capture)

    assert captured, 'Ответ AuthWithEmail не перехвачен'
    payload = captured['data']['payload']
    assert payload.get('needOTP') is True, f'Ожидался needOTP=true для нового email, получено: {payload}'
    return payload['tempToken']


def _get_otp_from_mailinator(inbox_name: str, timeout: int = 30, poll_interval: int = 3) -> str:
    """Поллит Mailinator API и возвращает OTP из темы письма от Vaiz."""
    encoded = urllib.parse.quote(inbox_name)
    url = f'{MAILINATOR_API}/{encoded}'
    deadline = time.time() + timeout

    while time.time() < deadline:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            msgs = [m for m in resp.json().get('msgs', [])
                    if 'vaiz' in m.get('fromfull', '').lower()]
            if msgs:
                subject = msgs[-1]['subject']
                otp = subject.split('|')[1].strip()
                assert re.match(r'^\d{6}', otp), f'OTP не найден в теме письма: {subject}'
                return otp[:6]
        time.sleep(poll_interval)

    raise AssertionError(f'Письмо от Vaiz не пришло в ящик {inbox_name} за {timeout} сек')


def _get_otp_from_mongo(db, temp_token: str) -> str:
    """Декодирует tempToken JWT, достаёт id и находит OTP в confirmtokens."""
    payload_part = temp_token.split('.')[1]
    payload_json = base64.urlsafe_b64decode(payload_part + '==')
    token_data = json.loads(payload_json)
    confirm_id = token_data['id']

    doc = db.confirmtokens.find_one({'_id': ObjectId(confirm_id)})
    assert doc, f'Запись confirmtokens с _id={confirm_id} не найдена'

    otp_code = doc.get('payload', {}).get('otpCode')
    assert otp_code, f'otpCode отсутствует в confirmtokens. Документ: {doc}'

    return otp_code


def _get_otp(inbox_name: str, db=None, temp_token: str = None) -> str:
    """Получает OTP: Mailinator на всех стендах, MongoDB-fallback на dev."""
    if FRONTEND_STAND == 'prod':
        return _get_otp_from_mailinator(inbox_name)

    # Dev: пробуем Mailinator, при неудаче — MongoDB
    try:
        return _get_otp_from_mailinator(inbox_name)
    except Exception:
        assert db and temp_token, 'Mailinator недоступен, а MongoDB-параметры не переданы'
        return _get_otp_from_mongo(db, temp_token)


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
        temp_token = _submit_email_and_get_temp_token(page)

    with allure.step('Получение OTP'):
        inbox_name = new_email.split('@')[0]
        otp_code = _get_otp(inbox_name, db=db, temp_token=temp_token)

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
