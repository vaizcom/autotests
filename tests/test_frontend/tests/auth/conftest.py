import base64
import json
import re
import time
import urllib.parse

import pytest
import requests
from bson import ObjectId
from playwright.sync_api import expect, Page

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Header, Sidebar, SpaceSelector
from tests.test_frontend.core.settings import FRONTEND_STAND

MAILINATOR_API = 'https://api.mailinator.com/api/v2/domains/public/inboxes'


@pytest.fixture()
def browser_context_args(browser_context_args):
    """Убираем storage_state — auth-тесты управляют сессией самостоятельно."""
    return {k: v for k, v in browser_context_args.items() if k != 'storage_state'}


def sign_in_and_go_to_space(page: Page):
    """Логинится и переходит в autotest space. Используется как setup в logout."""
    page.goto(f'{settings.BASE_URL}/auth/sign-in')
    page.get_by_test_id(Auth.EMAIL_INPUT).fill(settings.FRONTEND_EMAIL)
    page.get_by_test_id(Auth.EMAIL_SUBMIT).click()
    page.get_by_test_id(Auth.PASSWORD_INPUT).wait_for(state='visible', timeout=10000)
    page.get_by_test_id(Auth.PASSWORD_INPUT).fill(settings.FRONTEND_PASSWORD)
    page.get_by_test_id(Auth.PASSWORD_SUBMIT).click()
    expect(page.get_by_test_id(Sidebar.HOME)).to_be_visible(timeout=15000)

    page.get_by_test_id(Header.SPACE_SELECTOR).click()
    page.get_by_test_id(SpaceSelector.space(settings.AUTOTEST_SPACE_ID)).click()
    page.get_by_test_id(Sidebar.HOME).wait_for(state='visible', timeout=10000)


def home_screenshot_with_masks(page: Page) -> bytes:
    """Стабилизирует Home и возвращает скриншот с масками динамических элементов."""
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

    return page.screenshot(mask=dynamic_masks)


def submit_email_and_get_temp_token(page) -> str:
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
    return captured['data']['payload']


def get_otp_from_mailinator(inbox_name: str, since_ts: int = 0,
                            timeout: int = 30, poll_interval: int = 3) -> str:
    """Поллит Mailinator API и возвращает OTP код из темы письма от Vaiz.

    Args:
        inbox_name: имя ящика (часть до @mailinator.com)
        since_ts: Unix-timestamp в секундах — игнорировать письма старше этого времени.
                  Для переиспользуемых ящиков (sign-in OTP) передавать time.time() до отправки формы.

    Ручная проверка в Postman:
    1. POST https://api.vaiz.dev/v4/AuthWithEmail
       Body: {"email": "TST_test1@mailinator.com"}
       → скопировать payload.tempToken

    2. GET https://api.mailinator.com/api/v2/domains/public/inboxes/TST_test1
       → в msgs найти письмо от vaiz, взять 6 цифр из subject после "|"
       (OTP в теме содержит невидимый символ — вводить вручную, не копировать)

    3. POST https://api.vaiz.dev/v4/VerifyOtp
       Body: {"tempToken": "<из шага 1>", "otp": "<из шага 2>"}
       → payload.authToken
    """
    encoded = urllib.parse.quote(inbox_name)
    url = f'{MAILINATOR_API}/{encoded}'
    deadline = time.time() + timeout
    since_ms = int(since_ts * 1000)
    last_status = None

    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=10)
        except requests.exceptions.ConnectionError:
            raise AssertionError(
                f'Mailinator API недоступен (ConnectionError). '
                f'Проверить: 1) интернет 2) https://www.mailinator.com открывается в браузере'
            )
        except requests.exceptions.Timeout:
            raise AssertionError(
                f'Mailinator API не отвечает (Timeout). '
                f'Проверить: https://www.mailinator.com открывается в браузере'
            )

        last_status = resp.status_code
        if resp.status_code == 200:
            msgs = [m for m in resp.json().get('msgs', [])
                    if 'vaiz' in m.get('fromfull', '').lower()
                    and m.get('time', 0) >= since_ms]
            if msgs:
                subject = msgs[-1]['subject']
                parts = subject.split('|')
                assert len(parts) >= 2, (
                    f'Формат темы письма изменился, нет разделителя "|": {subject}'
                )
                otp = parts[1].strip()
                assert re.match(r'^\d{6}', otp), (
                    f'OTP не найден в теме письма (ожидались 6 цифр после "|"): {subject}'
                )
                return otp[:6]
        time.sleep(poll_interval)

    hints = []
    if last_status and last_status != 200:
        hints.append(f'API вернул статус {last_status} — возможно сменилась версия API или endpoint')
    hints.append('Проверить: 1) https://www.mailinator.com доступен 2) Vaiz отправляет письма на @mailinator.com')
    raise AssertionError(
        f'Письмо от Vaiz не пришло в ящик {inbox_name} за {timeout} сек. '
        + ' '.join(hints)
    )


def get_otp_from_mongo(db, temp_token: str) -> str:
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


def get_otp(inbox_name: str, since_ts: int = 0, db=None, temp_token: str = None) -> str:
    """Получает OTP: Mailinator на всех стендах, MongoDB-fallback на dev."""
    if FRONTEND_STAND == 'prod':
        return get_otp_from_mailinator(inbox_name, since_ts=since_ts)

    # Dev: пробуем Mailinator, при неудаче — MongoDB
    try:
        return get_otp_from_mailinator(inbox_name, since_ts=since_ts)
    except Exception:
        assert db and temp_token, 'Mailinator недоступен, а MongoDB-параметры не переданы'
        return get_otp_from_mongo(db, temp_token)
