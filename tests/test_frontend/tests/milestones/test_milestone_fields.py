import os
import re
from datetime import datetime

import allure
import pytest
from playwright.sync_api import expect, Page

from tests.test_frontend.conftest import cleanup_board, cleanup_cards_by_pattern
from tests.test_frontend.tests.milestones.conftest import (
    create_milestone_on_board,
    open_milestone,
    add_task_to_milestone,
    wait_for_task_rows,
    archive_milestone,
    cleanup_milestones,
)
from tests.test_frontend.tests.tasks.conftest import (
    add_comment,
    fill_description,
    future_date,
    set_date,
    delete_task_in_table,
)

pytestmark = [pytest.mark.frontend]

# test_01 — создаёт майлстоун, остальные зависят от него.
# При запуске отдельного теста через IDE — майлстоун создаётся и архивируется автоматически.
_DEP_CREATE = 'test_01_create_milestone'
_DEP_TASK_LIST = 'test_06_add_tasks_to_milestone'

_MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
           'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']


def _make_ts():
    now = datetime.now()
    return f'{now.day} {_MONTHS[now.month - 1]}, {now.strftime("%H:%M")}'


_TS = os.environ.get('TEST_TS') or _make_ts()
_MILESTONE_NAME = f'autotest_ms_{_TS}'
_SHORT_DESC = f'Short desc {_TS}'
_DESCRIPTION = f'Milestone description {_TS}'
_TASK_NAME = f'MS task {_TS}'
_TASK_NAME_2 = f'MS task 2 {_TS}'
_COMMENT = f'MS comment {_TS}'
_DATE_START = future_date()
_DATE_DUE = future_date(100)


# ── Auto-debug: setup/cleanup при запуске отдельного теста из IDE ──


def _debug_create(page):
    create_milestone_on_board(page, _MILESTONE_NAME)


_KEEP_MILESTONES = ['Test milestone']


def _debug_teardown(page):
    cleanup_milestones(page, keep_names=_KEEP_MILESTONES)
    cleanup_board(page)


def _setup_tasks(page):
    for name in (_TASK_NAME, _TASK_NAME_2):
        add_task_to_milestone(page, name)


_debug_extra_setup = {
    'test_07_complete_milestone_tasks': _setup_tasks,
    'test_08_delete_milestone_tasks': _setup_tasks,
}


# ── 01. Создание майлстоуна ─────────────────────────────────────────


@pytest.mark.dependency(name=_DEP_CREATE)
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('01. Create milestone on board')
def test_01_create_milestone(page: Page, soft_step):
    """Создаёт майлстоун через вкладку Milestones на борде."""
    # Cleanup артефактов от предыдущих прерванных прогонов
    with allure.step('Cleanup: удаление артефактов предыдущих прогонов'):
        cleanup_cards_by_pattern(page, 'MS task')
        cleanup_milestones(page, keep_names=['Test milestone'])

    with allure.step(f'Создание майлстоуна: {_MILESTONE_NAME}'):
        soft_step('Создание майлстоуна', lambda: create_milestone_on_board(page, _MILESTONE_NAME))


# ── 02. Название ────────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('02. Verify milestone name')
def test_02_verify_milestone_name(page: Page, soft_step, sidebar):
    """Проверяет что название майлстоуна отображается корректно."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step('Проверка названия'):
        soft_step(
            'Название', lambda: expect(sidebar.get_by_role('heading', name=_MILESTONE_NAME)).to_be_visible(timeout=5000)
        )


# ── 03. Короткое описание ──────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('03. Set short description')
def test_03_set_short_description(page: Page, soft_step, sidebar):
    """Заполняет и проверяет короткое описание майлстоуна."""
    open_milestone(page, _MILESTONE_NAME)

    def set_short_desc():
        short_desc = sidebar.get_by_placeholder('Enter short description...')
        short_desc.click()
        short_desc.fill(_SHORT_DESC)
        page.keyboard.press('Tab')
        expect(short_desc).to_have_value(_SHORT_DESC, timeout=5000)

    with allure.step(f'Короткое описание: {_SHORT_DESC}'):
        soft_step('Короткое описание', set_short_desc)


# ── 04. Описание (tiptap) ──────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('04. Set and verify description')
def test_04_set_description(page: Page, soft_step, sidebar):
    """Заполняет и проверяет описание майлстоуна (tiptap-редактор после секции задач)."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f'Описание: {_DESCRIPTION}'):
        soft_step('Заполнение описания', lambda: fill_description(page, _DESCRIPTION))

    with allure.step('Проверка описания'):
        soft_step(
            'Описание сохранено',
            lambda: expect(sidebar.locator('.tiptap').filter(has_text=_DESCRIPTION).first).to_be_visible(timeout=5000),
        )


# ── 05. Даты ────────────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('05. Set and verify dates')
def test_05_set_milestone_dates(page: Page, soft_step, sidebar):
    """Устанавливает и проверяет даты майлстоуна."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f'Даты: {_DATE_START}'):
        soft_step('Установка дат', lambda: set_date(page, date=_DATE_START))

    with allure.step('Проверка дат'):
        # "10.08.2026" → "10 August 2026"
        _d = datetime.strptime(_DATE_START, '%d.%m.%Y')
        _expected = f'{_d.day} {_d.strftime("%B")} {_d.year}'
        soft_step('Даты сохранены', lambda: expect(sidebar.get_by_text(_expected)).to_be_visible(timeout=5000))


# ── 06. Добавление задач + счётчики ────────────────────────────────


@pytest.mark.dependency(name=_DEP_TASK_LIST, depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('06. Add tasks and verify counters')
def test_06_add_tasks_to_milestone(page: Page, soft_step, sidebar):
    """Добавляет две задачи в майлстоун, проверяет счётчик на каждом шаге.

    Обратную связь (МС виден в карточке задачи) проверяет API-тест
    test_tasks_visibility_in_correct_milestones — кросс-навигация на E2E не нужна.
    """
    open_milestone(page, _MILESTONE_NAME)

    # ── Пустое состояние ──

    with allure.step('Проверка: 0 tasks'):
        soft_step('0 tasks', lambda: expect(sidebar.get_by_role('heading', name='0 tasks')).to_be_visible(timeout=5000))

    # ── Задача 1 → "1 task" + "0 completed of 1" ──

    with allure.step(f'Добавление задачи: {_TASK_NAME}'):
        soft_step('Добавление задачи 1', lambda: add_task_to_milestone(page, _TASK_NAME))

    with allure.step('Проверка: 1 task'):
        soft_step(
            '1 task',
            lambda: expect(sidebar.get_by_role('heading', name=re.compile(r'\b1 task\b'))).to_be_visible(timeout=5000),
        )

    with allure.step('Проверка: 0 completed of 1'):
        soft_step(
            '0 completed of 1', lambda: expect(sidebar.get_by_text('0 completed of 1')).to_be_visible(timeout=5000)
        )

    # ── Задача 2 → "2 tasks" + "0 completed of 2" ──

    with allure.step(f'Добавление задачи: {_TASK_NAME_2}'):
        soft_step('Добавление задачи 2', lambda: add_task_to_milestone(page, _TASK_NAME_2))

    with allure.step('Проверка: 2 tasks'):
        soft_step('2 tasks', lambda: expect(sidebar.get_by_role('heading', name='2 tasks')).to_be_visible(timeout=5000))

    with allure.step('Проверка: 0 completed of 2'):
        soft_step(
            '0 completed of 2', lambda: expect(sidebar.get_by_text('0 completed of 2')).to_be_visible(timeout=5000)
        )


# ── 07. Завершение / снятие завершения задач ───────────────────────


@pytest.mark.dependency(depends=[_DEP_TASK_LIST])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('07. Verify task completion counters')
def test_07_complete_milestone_tasks(page: Page, soft_step, sidebar):
    """Завершает и снимает завершение задач, проверяет счётчики и прогресс-круги."""
    open_milestone(page, _MILESTONE_NAME)

    wait_for_task_rows(page, _MILESTONE_NAME)

    progress_bars = sidebar.locator('[data-test-id="CircularProgressbar"]')
    progress_title = progress_bars.first
    progress_counter = progress_bars.nth(1)

    def _get_offset(progress_bar):
        """Возвращает stroke-dashoffset прогресс-пути (0 = 100%, ~289 = 0%)."""
        path = progress_bar.locator('.CircularProgressbar-path')
        style = path.get_attribute('style')
        match = re.search(r'stroke-dashoffset:\s*([\d.]+)px', style)
        return float(match.group(1)) if match else None

    def _offset_in_range(bar, expected_pct):
        offset = _get_offset(bar)
        if offset is None:
            return False
        if expected_pct == 0:
            return offset > 200
        elif expected_pct == 50:
            return 50 < offset < 200
        elif expected_pct == 100:
            return offset < 1
        return False

    def _check_progress(label, expected_pct):
        """Проверяет что оба прогресс-круга заполнены на expected_pct (0, 50, 100).
        Polling с ожиданием до 5 секунд — SVG обновляется с задержкой (бродкаст)."""
        for name, bar in [('у заголовка', progress_title), ('у счётчика', progress_counter)]:
            for _ in range(20):
                if _offset_in_range(bar, expected_pct):
                    break
                page.wait_for_timeout(500)
            else:
                offset = _get_offset(bar)
                raise AssertionError(f'Прогресс-круг {name}: ожидался {expected_pct}%, offset={offset}')

    def toggle_complete(task_name):
        task_row = sidebar.get_by_role('button').filter(has_text=re.compile(r'[A-Z]+-\d+')).filter(has_text=task_name)
        task_row.locator('label[role="checkbox"]').click()

    # ── Прогресс-круги видны, 0% ──

    with allure.step('Проверка: оба прогресс-круга видны, 0%'):
        soft_step('Прогресс-круг у заголовка', lambda: expect(progress_title).to_be_visible(timeout=5000))
        soft_step('Прогресс-круг у счётчика', lambda: expect(progress_counter).to_be_visible(timeout=5000))
        soft_step('Прогресс 0%', lambda: _check_progress('0 completed', 0))

    # ── Complete задачи 1 → "1 completed of 2", ~50% ──

    with allure.step(f'Завершение задачи: {_TASK_NAME}'):
        soft_step('Завершение задачи 1', lambda: toggle_complete(_TASK_NAME))

    with allure.step('Проверка: 1 completed of 2, ~50%'):
        expect(sidebar.get_by_text('1 completed of 2')).to_be_visible(timeout=10000)
        soft_step('Прогресс ~50%', lambda: _check_progress('1 of 2', 50))

    # ── Complete задачи 2 → "All 2 completed", 100% ──

    with allure.step(f'Завершение задачи: {_TASK_NAME_2}'):
        soft_step('Завершение задачи 2', lambda: toggle_complete(_TASK_NAME_2))

    with allure.step('Проверка: All 2 completed, 100%'):
        expect(sidebar.get_by_text('All 2 completed')).to_be_visible(timeout=10000)
        soft_step('Прогресс 100%', lambda: _check_progress('All completed', 100))

    # ── Uncomplete задачи 1 → "1 completed of 2", ~50% ──

    with allure.step(f'Снятие завершения: {_TASK_NAME}'):
        soft_step('Снятие завершения задачи 1', lambda: toggle_complete(_TASK_NAME))

    with allure.step('Проверка: 1 completed of 2 (после снятия), ~50%'):
        expect(sidebar.get_by_text('1 completed of 2')).to_be_visible(timeout=10000)
        soft_step('Прогресс ~50%', lambda: _check_progress('1 of 2 after uncomplete', 50))

    # ── Uncomplete задачи 2 → "0 completed of 2", 0% ──

    with allure.step(f'Снятие завершения: {_TASK_NAME_2}'):
        soft_step('Снятие завершения задачи 2', lambda: toggle_complete(_TASK_NAME_2))

    with allure.step('Проверка: 0 completed of 2, 0%'):
        expect(sidebar.get_by_text('0 completed of 2')).to_be_visible(timeout=10000)
        soft_step('Прогресс 0%', lambda: _check_progress('0 of 2 after uncomplete', 0))


# ── 08. Удаление задач + счётчики ──────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_TASK_LIST])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('08. Delete tasks and verify counters')
def test_08_delete_milestone_tasks(page: Page, soft_step, sidebar):
    """Удаляет задачи из таблицы майлстоуна, проверяет уменьшение счётчика."""
    open_milestone(page, _MILESTONE_NAME)

    wait_for_task_rows(page, _MILESTONE_NAME)

    def delete_task(task_name):
        delete_task_in_table(page, sidebar, task_name)

    # ── Удаление задачи 1 → "1 task" ──

    with allure.step(f'Удаление задачи: {_TASK_NAME}'):
        soft_step('Удаление задачи 1', lambda: delete_task(_TASK_NAME))

    with allure.step('Проверка: 1 task'):
        soft_step(
            '1 task',
            lambda: expect(sidebar.get_by_role('heading', name=re.compile(r'\b1 task\b'))).to_be_visible(timeout=5000),
        )

    # ── Удаление задачи 2 → "0 tasks" ──

    with allure.step(f'Удаление задачи: {_TASK_NAME_2}'):
        soft_step('Удаление задачи 2', lambda: delete_task(_TASK_NAME_2))

    with allure.step('Проверка: 0 tasks'):
        soft_step('0 tasks', lambda: expect(sidebar.get_by_role('heading', name='0 tasks')).to_be_visible(timeout=5000))


# ── 09. Комментарии ─────────────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('09. Add comment and verify')
def test_09_add_milestone_comment(page: Page, soft_step, sidebar):
    """Добавляет комментарий к майлстоуну и проверяет."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step(f'Комментарий: {_COMMENT}'):
        sidebar.get_by_role('button', name=re.compile(r'Comments \d+')).click()
        soft_step('Добавление комментария', lambda: add_comment(page, _COMMENT))

    with allure.step('Проверка комментария'):
        soft_step('Комментарий сохранён', lambda: expect(sidebar.get_by_text(_COMMENT)).to_be_visible(timeout=5000))


# ── 10. Вкладка Activities ─────────────────────────────────────────


@pytest.mark.dependency(depends=[_DEP_CREATE])
@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('10. Verify Activities tab')
def test_10_verify_activities_tab(page: Page, soft_step, sidebar):
    """Проверяет что вкладка Activities отображается."""
    open_milestone(page, _MILESTONE_NAME)

    with allure.step('Вкладка Activities видна'):
        soft_step(
            'Вкладка Activities',
            lambda: expect(sidebar.get_by_role('button', name='Activities')).to_be_visible(timeout=5000),
        )



# ── 99. Cleanup ─────────────────────────────────────────────────────


@allure.parent_suite('Frontend')
@allure.suite('Milestones')
@allure.sub_suite('Fields')
@allure.title('99. Cleanup: archive milestone')
def test_99_cleanup_milestone(page: Page):
    """Архивирует тестовый майлстоун и подчищает все остальные кроме 'Test milestone'."""
    archive_milestone(page, _MILESTONE_NAME)
    cleanup_milestones(page, keep_names=['Test milestone'])
