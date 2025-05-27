import time
import allure
import pytest
from playwright.sync_api import expect, Page
from frontend_tests.core import settings


@pytest.fixture()
def browser_context_args():
    return {
        'http_credentials': {
            'username': 'mastretsova+2@ibitcy.com',
            'password': '123456',
        }
    }

@pytest.mark.skip
def test_sign_in_with_email(page: Page, browser_context_args):
    # Создаем новый контекст браузера с учетными данными для базовой аутентификации
    with allure.step('Launching the app'):
        page.goto(settings.BASE_URL)
    with allure.step('Entering user credentials'):
        page.get_by_label('Email').fill('mastretsovaone@gmail.com')
        page.get_by_label('Password').fill('123456')
    with allure.step("Entering the button 'Continue'"):
        page.get_by_role('button', name='Continue with Email').click()
    expect(page.get_by_role('link', name='Home')).to_be_attached()
    expect(page.get_by_role('heading', name='Hello')).to_be_visible()


@pytest.mark.skip
def test_sign_in_with_slack(page: Page):
    page.goto(settings.BASE_URL + '/auth/sign-in', wait_until='domcontentloaded')
    page.get_by_role('button', name='Sign in with Slack').click()
    page.get_by_role('link', name='Find your workspaces').click()

    page.get_by_role('button', name='Accept All Cookies').click()

    page.get_by_role('button', name='Continue With Google').click()
    page.get_by_label('Email or phone').click()
    page.get_by_label('Email or phone').fill('test.vaiz.by.email@gmail.com')
    page.get_by_role('button', name='Next').click(timeout=600 * 1000)
    page.get_by_label('Enter your password').click()
    page.get_by_label('Enter your password').fill('fJ529_/!o7T~wwn!*e|')
    page.get_by_role('button', name='Next').click()
    time.sleep(10)
    page.get_by_role('button', name='Allow').or_(page.get_by_role('button', name='Continue')).click()
    time.sleep(1)
    page.get_by_role('link', name='test.vaiz.by.email test.vaiz.').click()
    time.sleep(1)
    page.get_by_role('button', name='Accept and Continue').click()

    expect(page.get_by_role('link', name='Dashboard')).to_be_visible(timeout=6000 * 10000)
    expect(page).to_have_url('https://app.vaiz.dev/65c8e579dac495717996637b')


@pytest.mark.skip
def test_sign_in_with_google(page: Page):
    page.goto(settings.BASE_URL + '/auth/sign-in')
    page.get_by_role('button', name='Sign in with Google').click()
    page.get_by_label('Email or phone').click()
    page.get_by_label('Email or phone').fill('test.vaiz.by.email@gmail.com')
    page.get_by_role('button', name='Next').click()
    page.get_by_label('Enter your password').click()
    page.get_by_label('Enter your password').fill('fJ529_/!o7T~wwn!*e|')
    page.get_by_role('button', name='Next').click()
    expect(page.get_by_text('test.vaiz.by.email@gmail.com')).to_be_attached()
    page.get_by_role('button', name='Continue').click()

    # assert page.url == "https://zimaev.github.io/tabs/dashboard/index.html?"
    # sign_out = page.locator('.nav-link', has_text='Sign out')
    # assert sign_out.is_visible()
    expect(page.get_by_role('link', name='Dashboard')).to_be_attached(timeout=100 * 1000)


@pytest.mark.skip
def test_sign_in_with_github(page: Page, context, browser_context_args):
    # GMail
    # g_account_page = context.new_page()
    # g_account_page.goto("https://accounts.google.com/")
    # g_account_page.get_by_label("Email or phone").click()
    # g_account_page.get_by_label("Email or phone").fill("test.vaiz.by.email@gmail.com")
    #
    # g_account_page.get_by_role("button", name="Next").click()
    # g_account_page.get_by_label("Enter your password").click()
    # g_account_page.get_by_label("Enter your password").fill("fJ529_/!o7T~wwn!*e|")
    # g_account_page.get_by_role("button", name="Next").click()

    # VAIZ page.get_by_role("heading", name="Welcome, test_vaiz").click()
    vaiz_page = context.new_page()
    vaiz_page.goto(settings.BASE_URL + '/auth/sign-in')
    vaiz_page.get_by_role('button', name='Sign in with Github').click()
    vaiz_page.get_by_label('Username or email address').click()
    vaiz_page.get_by_label('Username or email address').fill('test.vaiz.by.email@gmail.com')
    vaiz_page.get_by_label('Password').click()
    vaiz_page.get_by_label('Password').fill('fJ529_/!o7T~wwn!*e|')
    vaiz_page.get_by_role('button', name='Sign in', exact=True).click()

    Ask_later = vaiz_page.get_by_role('link', name='Ask me later').last
    Authorize = vaiz_page.get_by_role('button', name='Authorize vaizcom')

    # vaiz_page.get_by_role("button", name="Authorize vaizcom").or_(vaiz_page.get_by_role("link", name="Ask me later").last).click()

    if Ask_later.is_visible():
        Ask_later.click()
    if Authorize.is_visible():
        Authorize.click()
    expect(vaiz_page.get_by_role('link', name='Dashboard')).to_be_attached(timeout=100 * 1000)
