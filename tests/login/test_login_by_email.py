from playwright.sync_api import expect, Page, Playwright, BrowserContext

from core import settings


def test_success_login(page: Page, playwright: Playwright):
    page.goto(settings.BASE_URL)
    page.get_by_placeholder('name@example.com').fill('test.vaiz.by.email@gmail.com')
    playwright.selectors.set_test_id_attribute('id')
    page.get_by_test_id('password').fill('fJ529_/!o7T~wwn!*e|')
    page.get_by_text('Sign in with Email').click()
    expect(page.get_by_text('Dashboard')).to_be_attached()


def test_success_login_slack_by_email(page: Page, playwright: Playwright):
    page.goto(settings.BASE_URL)
    page.get_by_placeholder('name@example.com').fill('test.vaiz.by.slack@gmail.com')
    playwright.selectors.set_test_id_attribute('id')
    page.get_by_test_id('password').fill('fJ529_/!o7T~wwn!*e|')
    page.get_by_text('Sign in with Email').click()
    expect(page.get_by_text('Dashboard')).to_be_attached()


# vaizslack
def test_sign_in_with_slack(page: Page, playwright: Playwright, context: BrowserContext):
    page.goto('https://accounts.google.com')
    playwright.selectors.set_test_id_attribute('id')
    page.get_by_test_id('identifierId').fill('test.vaiz.by.slack@gmail.com')
    page.keyboard.press('Enter')
    playwright.selectors.set_test_id_attribute('aria-label')
    page.get_by_test_id('Enter your password').fill('fJ529_/!o7T~wwn!*e|')
    page.keyboard.press('Enter')
    expect(page.get_by_test_id('Enter your password')).not_to_be_attached()
    expect(page.get_by_text('Welcome, vaiz_slack')).to_be_attached(timeout=5000)
    vaiz = context.new_page()
    vaiz.goto(settings.BASE_URL)
    vaiz.get_by_text('Sign in with Slack').click()
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
