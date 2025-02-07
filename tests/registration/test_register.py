import allure
import pytest
from core import settings
from playwright.sync_api import Page, expect, Playwright


@pytest.fixture()
def browser_context_args(generated_string):
    return {'http_credentials': {'username': 'mastretsovaone+' + generated_string + '@gmail.com', 'password': '123456'}}


def test_register_with_email(page: Page, generated_string, browser_context_args):
    with allure.step('Launching the app'):
        page.goto(settings.BASE_URL + 'auth/sign-up')
    with allure.step('Entering user credentials'):
        page.get_by_label('Email').fill('mastretsova+2+' + generated_string + '@ibitcy.com')
        page.get_by_label('Password').fill('123456')
        page.get_by_label('What is your name?').fill(generated_string)
    with allure.step("Entering the button 'Continue'"):
        page.get_by_role('button', name='Continue with Email').click()
    expect(page.get_by_role('heading', name='Set up your Workspace')).to_be_visible()

    with allure.step('Fill in Space Name, Project name'):
        page.get_by_placeholder('My Space').fill('My Space ' + generated_string)
        page.get_by_placeholder('My project').fill('My Project ' + generated_string)
    with allure.step('Click the button Continue'):
        page.get_by_role('button', name='Continue').click()
    expect(page.get_by_role('heading', name='What features are you interested in?')).to_be_visible()
    with allure.step('Select items on the page What features are you interested in?'):
        page.get_by_text('Tasks').click()
        page.get_by_text('Boards', exact=True).click()
        page.get_by_text('Docs and wiki').click()
        page.get_by_text('Calendar').click()
        page.get_by_text('Time tracking').click()
        page.get_by_text('Dashboards').click()
        page.get_by_text('Scrum').click()
        page.get_by_text('Scrum').click()
        page.get_by_text('Dashboards').click()
        page.get_by_text('Time tracking').click()

    # expect(page.get_by_text("Time tracking".is))

    with allure.step('Click the button Start using Vaiz'):
        page.get_by_role('button', name='Start using Vaiz').click()

    expect(page.get_by_role('link', name='Home')).to_be_attached()
    expect(page.get_by_role('heading', name='Hello, ' + generated_string + '!')).to_be_visible()
    page.context.clear_cookies()
    return generated_string


@pytest.mark.skip
def test_success_register(page: Page, generated_string):
    page.goto(settings.BASE_URL + '/auth/sign-up')
    page.get_by_label('Email').fill('mastretsovaone+' + generated_string + '@gmail.com')
    page.get_by_label('Password').fill('123456')
    page.get_by_role('button', name='Continue with Email').click()
    expect(page.get_by_role('link', name='Home')).to_be_attached()
    expect(page.get_by_role('heading', name='Hello, ' + generated_string + '!')).to_be_visible()
    page.context.clear_cookies()


@pytest.mark.skip
def test_sign_up_with_slack(page: Page, playwright: Playwright, generated_string):
    page.goto('https://accounts.google.com')
    playwright.selectors.set_test_id_attribute('id')
    page.get_by_test_id('identifierId').fill(generated_string + 'by.email@gmail.com')
    page.keyboard.press('Enter')
    playwright.selectors.set_test_id_attribute('aria-label')
    page.get_by_test_id('Enter your password').fill(generated_string)
    page.keyboard.press('Enter')
    expect(page.get_by_test_id('Enter your password')).not_to_be_attached()
    expect(page.get_by_text('Welcome, vaiz_slack')).to_be_attached(timeout=5000)
    vaiz = page.context.new_page()
    vaiz.goto(settings.BASE_URL + 'auth/sign-up')
    vaiz.get_by_text('Sign up with Slack').click()
    playwright.selectors.set_test_id_attribute('id')
    vaiz.get_by_test_id('domain').fill('vaizslack')
    vaiz.keyboard.press('Enter')
    vaiz.get_by_text('Sign In With Google').click()
    playwright.selectors.set_test_id_attribute('role')
    expect(vaiz.get_by_text('test.vaiz.by.slack@gmail.com')).to_be_attached(timeout=5000)
    # В Google специальная защита - приходится ждать (delay):
    vaiz.get_by_text('test.vaiz.by.slack@gmail.com').click(delay=1000, timeout=5000)
    vaiz.get_by_text('Continue').click()
    vaiz.get_by_text('Accept All Cookies').click()
    vaiz.get_by_text('Accept and Continue').click()
    expect(vaiz.get_by_text('Dashboard')).to_be_attached()
