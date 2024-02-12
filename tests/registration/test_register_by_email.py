import random
import string
import settings
from playwright.sync_api import Page, expect, Playwright, BrowserContext

length = 8
str_characters = "!#$%^&*" + string.ascii_lowercase + string.digits
generated_string = ''.join(random.choice(str_characters) for _ in range(length))

# OR
# generated_string = ''.join(random.choices(str_characters, k=length))
# print(generated_string)


def test_success_register(page: Page, playwright: Playwright):
    page.goto(settings.BASE_URL + 'auth/sign-up')
    page.get_by_placeholder('name@example.com').fill(generated_string+'by.email@gmail.com')
    playwright.selectors.set_test_id_attribute('id')
    page.get_by_test_id('password').fill(generated_string)
    page.get_by_text('Sign up with Email').click()
    expect(page.get_by_text('Get started')).to_be_attached()

