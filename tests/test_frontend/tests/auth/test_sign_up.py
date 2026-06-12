import base64
import json
import re
import time

import allure
import pytest
from bson import ObjectId
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Header, Sidebar

pytestmark = [pytest.mark.frontend]


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — тест проверяет регистрацию самостоятельно."""
    return {k: v for k, v in browser_context_args.items() if k != 'storage_state'}


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


@allure.parent_suite('Frontend')
@allure.suite('Auth')
@allure.title('Sign up with email (OTP)')
def test_sign_up_with_email(page: Page, db, assert_snapshot):
    new_email = f'autotest_{int(time.time())}@gmail.com'

    with allure.step('Открытие страницы входа'):
        page.goto(f'{settings.BASE_URL}/auth/sign-in')
        page.get_by_test_id(Auth.EMAIL_INPUT).wait_for(state='visible', timeout=15000)

    with allure.step(f'Ввод нового email: {new_email}'):
        page.get_by_test_id(Auth.EMAIL_INPUT).fill(new_email)

    with allure.step('Отправка email и перехват tempToken'):
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
        resp_json = captured['data']
        temp_token = resp_json['payload']['tempToken']
        assert (
            resp_json['payload'].get('needOTP') is True
        ), f'Ожидался needOTP=true для нового email, получено: {resp_json["payload"]}'

    with allure.step('Получение OTP из MongoDB'):
        otp_code = _get_otp_from_mongo(db, temp_token)

    with allure.step(f'Ввод OTP: {otp_code}'):
        page.get_by_test_id(Auth.OTP_INPUT).wait_for(state='visible', timeout=10000)
        page.get_by_test_id(Auth.OTP_INPUT).fill(otp_code)
        page.get_by_test_id(Auth.OTP_SUBMIT).click()

    with allure.step('Ожидание перехода с auth-страницы'):
        expect(page).not_to_have_url(re.compile(r'.*/auth/'), timeout=30000)

    # --- Онбординг ---
    next_btn = page.get_by_role('button', name='Next')

    with allure.step('Онбординг: ввод имени'):
        page.get_by_text('What is your name?').wait_for(state='visible', timeout=15000)
        page.locator('input[name="fullName"]').fill(new_email.split('@')[0])
        next_btn.click()

    with allure.step('Онбординг: название Workspace'):
        page.get_by_text('Name your Workspace').wait_for(state='visible', timeout=10000)
        next_btn.click()

    with allure.step('Онбординг: приглашение Invite people (пропуск)'):
        page.get_by_text('Invite people to your Workspace').wait_for(state='visible', timeout=10000)
        next_btn.click()

    with allure.step('Онбординг: помощь Book a call(пропуск)'):
        page.get_by_text('Need help getting started?').wait_for(state='visible', timeout=10000)
        next_btn.click()

    with allure.step('Онбординг: завершение'):
        page.get_by_text('The workspace setup is complete!').wait_for(state='visible', timeout=10000)
        page.get_by_role('button', name='Finish').click()

    with allure.step('Проверка: пользователь на Home'):
        expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    with allure.step('Сравнение скриншота'):
        page.get_by_test_id(Sidebar.HOME).click()
        page.get_by_test_id(Sidebar.ARCHIVE).wait_for(state='visible', timeout=10000)
        page.mouse.move(640, 400)

        dynamic_masks = [
            page.locator('[class*="AsideNotificationsMenuItem-module_UnreadDot"]'),
            page.locator('[class*="NotificationsToggleButton-module_UnreadDot"]'),
            page.locator('[class*="MemberAvatar-module_Root"]'),
            page.locator('[class*="HomeScreen-module_Avatar"]'),
            page.locator('[class*="HomeScreen-module_Title"]'),
            page.locator('[class*="HomeScreen-module_TimeBlock"]'),
            page.get_by_test_id(Header.SPACE_SELECTOR),
            page.locator('[class*="HomeScreenCard-module_Root"]'),
            page.locator('[class*="HomeScreenTipCard-module_Tips"]'),
            page.locator('[class*="HomeScreenStuff-module_Root"]'),
            page.locator('[class*="TourBanner-module_Root"]'),
            page.locator('[class*="AffiliateBanner-module_Root"]'),
            page.locator('[class*="AsideMenu-module_Footer"]'),
        ]

        page.add_style_tag(
            content="""
            span[class*="AppVersion"] {
                background-color: #FF00FF !important;
                color: transparent !important;
                display: inline-block !important;
                min-height: 14px !important;
            }
        """
        )

        screenshot = page.screenshot(mask=dynamic_masks)
        assert_snapshot(screenshot, name='sign_up_home.png', threshold=5.0)
