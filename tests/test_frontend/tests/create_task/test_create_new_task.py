import pytest

pytestmark = [pytest.mark.frontend]


@pytest.mark.skip(reason='not working')
def test_1(open_task_drawer, page, browser_context_args):
    comment_block = page.locator("//p[@data-placeholder='Write a comment...']")
    comment_block.click()
    comment_block.fill('some comment')
    # pyautogui.hotkey('ctrl', 's')


@pytest.mark.skip(reason='not working')
def test_create_task(page, browser_context_args, open_task_drawer):
    page.locator('.EditorView-module_TitleWrapper_SDiGQ > .CheckToggle-module_Root_yyxTW > span > .icon-icon').click()

    page.get_by_role('button', name='Location Project 1').is_visible()

    page.get_by_role('button', name='Select milestones').click()
    page.get_by_text('Create milestone').click()
    page.get_by_placeholder('Type name').click()
    page.get_by_placeholder('Type name').fill('11')
    page.get_by_role('menuitem', name='milestone 1').click()

    page.get_by_role('button', name='Types Select type').click()
    page.get_by_role('menuitem', name='Green').click()

    page.get_by_role('button', name='Dates No dates set').click()
    page.get_by_text('10', exact=True).click()
    page.get_by_role('button', name='Apply').click()

    page.get_by_role('button', name='Priority Select priority').click()
    page.get_by_role('menuitem', name='High').click()
    page.get_by_role('button', name='Priority High').click()
    page.get_by_text('Medium').click()
    page.get_by_role('button', name='Priority Medium').click()
    page.get_by_role('menuitem', name='Low').click()
    page.get_by_role('button', name='Priority Low').click()
    page.get_by_role('menuitem', name='Default').click()
    page.get_by_role('button', name='Priority Select priority').click()
    page.get_by_text('Medium').click()

    page.get_by_role('button', name='Assign Not assigned').click()
    page.get_by_text('Astretsova', exact=True).click()

    page.get_by_placeholder('Add blocker').click()
    page.get_by_placeholder('Add blocker').fill('blocker new')
    page.get_by_placeholder('Add blocker').press('ArrowDown')
    page.get_by_placeholder('Add blocker').press('Enter')
    page.get_by_role('button', name='Blockers VZS-1137 Blockers for').is_visible()

    page.get_by_placeholder('Add blocking').fill('Blocking new')
    page.get_by_placeholder('Add blocking').press('ArrowDown')
    page.get_by_placeholder('Add blocking').press('Enter')
    page.get_by_role('button', name='Blocking VZS-1138 Blocking for').is_visible()

    page.get_by_role('textbox', name='Empty').click()
    page.get_by_role('textbox', name='Empty').fill('some text')

    page.get_by_role('button', name='Number').get_by_placeholder('Empty').click()
    page.get_by_role('button', name='Number').get_by_placeholder('Empty').fill('123')
    page.get_by_role('button', name='Number').get_by_placeholder('Empty').click()
    page.get_by_role('button', name='Number').get_by_placeholder('Empty').fill('456')
    page.get_by_role('button', name='Number').get_by_placeholder('Empty').click()
    page.get_by_role('button', name='Number').get_by_placeholder('Empty').fill('12')
    page.get_by_role('button', name='Number').get_by_placeholder('Empty').click()

    page.get_by_role('button', name='Date Not selected').click()
    page.get_by_text('10', exact=True).click()
    page.locator('.FlyBlock-module_Overlay_k4A8s').click()

    page.get_by_role('button', name='Boolean').click()
    page.get_by_role('button', name='Boolean').click()
    page.get_by_role('button', name='Boolean').click()

    page.get_by_role('button', name='Member Not selected').click()
    page.get_by_role('menu').get_by_text('Astretsova', exact=True).click()

    page.get_by_placeholder('Link task').click()
    page.get_by_placeholder('Link task').fill('Related task new')
    page.get_by_placeholder('Link task').press('ArrowDown')
    page.get_by_placeholder('Link task').press('Enter')
    page.get_by_role('button', name='Related Tasks VZS-1139 Related').is_visible()

    page.get_by_role('button', name='Add new field').is_visible()

    page.get_by_role('button', name='Select Not selected').click()
    page.get_by_role('menuitem', name='select1').click()

    page.get_by_role('heading', name='Subtasks').click()
    page.get_by_role('heading', name='Add Subtasks').click()
    page.get_by_placeholder('Enter subtask name').click()
    page.get_by_placeholder('Enter subtask name').fill('Subtaska')
    page.get_by_placeholder('Enter subtask name').press('Enter')

    description_block = page.locator("//div[@class='DocumentEditor UniversalEditor']/div/p")
    description_block.click()
    description_block.fill('some text')

    comment_block = page.locator("//p[@data-placeholder='Write a comment...']")
    comment_block.click()
    comment_block.fill('some comment')
    # pyautogui.hotkey('ctrl', 's')


# TODO: check that fields are filled by what you entered


# TODO Not working Related Task on another board
# page.get_by_placeholder("Link task").click()
# page.get_by_placeholder("Link task").fill("VZS-999")
# page.get_by_placeholder("Link task").press("ArrowDown")
# page.get_by_placeholder("Link task").press("Enter")
# page.get_by_role("button", name="Related Tasks VZS-999 Related").is_visible()

# TODO Not working Related Task on another Project
# page.get_by_placeholder("Link task").click()
# page.get_by_placeholder("Link task").fill("TST-83")
# page.get_by_placeholder("Link task").press("ArrowDown")
# page.get_by_placeholder("Link task").press("Enter")
# page.get_by_role("button", name="Related Tasks TST-83 Related").is_visible()
