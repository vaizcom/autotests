import io
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import allure
import pytest
import pytest_check as check
import requests
from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import expect

from tests.test_frontend.core import settings
from tests.test_frontend.core.locators import Auth, Board, Header, Sidebar, SpaceSelector, TaskCard
from tests.test_frontend.core.settings import BASE_URL, FRONTEND_EMAIL, FRONTEND_PASSWORD, FRONTEND_STAND


def pytest_sessionstart(session):
    """Проверяет доступность стенда перед запуском тестов (3 попытки)."""
    for attempt in range(1, 4):
        try:
            resp = requests.get(BASE_URL, timeout=10, verify=False)
            resp.raise_for_status()
            return
        except Exception as e:
            if attempt < 3:
                time.sleep(5)
            else:
                pytest.exit(f"Стенд {BASE_URL} недоступен после 3 попыток: {e}", returncode=1)


def pytest_configure(config):
    """Локальные дефолты: --headed --slowmo 500 --video on (если не CI)."""
    if os.environ.get("CI"):
        return
    if not config.option.headed:
        config.option.headed = True
    if not config.option.slowmo:
        config.option.slowmo = 500
    if not config.option.video:
        config.option.video = "off"


@pytest.fixture(scope="session")
def browser_type_launch_args(pytestconfig):
    """Launch args для браузера: headed + slowmo локально, headless в CI."""
    launch_options = {}
    if pytestconfig.getoption("--headed"):
        launch_options["headless"] = False
    slowmo = pytestconfig.getoption("--slowmo")
    if slowmo:
        launch_options["slow_mo"] = slowmo
    channel = pytestconfig.getoption("--browser-channel")
    if channel:
        launch_options["channel"] = channel
    return launch_options

# API URL для teardown-операций (удаление Space, Project и т.д.)
API_URL = "https://api.vaiz.dev/v4"


def _run_task_cleanup(page, cleanup_info):
    """Удаляет карточки с таймстемпом теста на борде."""
    ts = cleanup_info.get("ts")
    if not ts:
        return

    with allure.step(f"Cleanup: удаление задач с таймстемпом {ts}"):
        page.goto(settings.AUTOTEST_BOARD_URL, timeout=60000)
        try:
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)
        except Exception:
            page.reload()
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)

        deleted = 0

        for _ in range(10):
            card = page.get_by_role("button").filter(has_text=ts).first
            try:
                expect(card).to_be_visible(timeout=3000)
            except Exception:
                break

            card.hover()
            card.get_by_test_id(TaskCard.MENU).click()

            delete_with_sub = page.get_by_text("Delete with subtasks")
            if delete_with_sub.is_visible(timeout=1000):
                delete_with_sub.click()
            else:
                page.get_by_text("Delete task").click()

            page.get_by_role("button", name="Proceed").click()
            page.wait_for_timeout(2000)
            deleted += 1

        allure.attach(f"Удалено карточек: {deleted}", name="cleanup result",
                      attachment_type=allure.attachment_type.TEXT)


def cleanup_cards_by_pattern(page, pattern: str):
    """Удаляет с борды карточки, содержащие pattern в названии. Best effort."""
    with allure.step(f"Cleanup: удаление карточек по паттерну '{pattern}'"):
        page.goto(settings.AUTOTEST_BOARD_URL, timeout=60000)
        try:
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=30000)
        except Exception:
            page.reload()
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=30000)

        deleted = 0
        for _ in range(10):
            card = page.get_by_role("button").filter(has_text=pattern).first
            try:
                expect(card).to_be_visible(timeout=3000)
            except Exception:
                break

            card.hover()
            card.get_by_test_id(TaskCard.MENU).click()

            delete_with_sub = page.get_by_text("Delete with subtasks")
            if delete_with_sub.is_visible(timeout=1000):
                delete_with_sub.click()
            else:
                page.get_by_text("Delete task").click()

            page.get_by_role("button", name="Proceed").click()
            page.wait_for_timeout(2000)
            deleted += 1

        if deleted:
            allure.attach(f"Удалено карточек: {deleted}", name=f"cleanup '{pattern}'",
                          attachment_type=allure.attachment_type.TEXT)


def cleanup_board(page):
    """Удаляет все карточки на автотестовой борде."""
    with allure.step("Cleanup: удаление всех задач на борде"):
        page.goto(settings.AUTOTEST_BOARD_URL, timeout=60000)
        try:
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)
        except Exception:
            page.reload()
            expect(page.get_by_test_id(Board.CREATE_TASK).first).to_be_visible(timeout=15000)

        cards = page.get_by_role("button").filter(has_text=re.compile(r"[A-Z]+-\d+"))
        deleted = 0

        for _ in range(20):
            try:
                expect(cards.first).to_be_visible(timeout=3000)
            except Exception:
                break

            cards.first.hover()
            cards.first.get_by_test_id(TaskCard.MENU).click()

            delete_with_sub = page.get_by_text("Delete with subtasks")
            if delete_with_sub.is_visible(timeout=1000):
                delete_with_sub.click()
            else:
                page.get_by_text("Delete task").click()

            page.get_by_role("button", name="Proceed").click()
            page.wait_for_timeout(1000)
            deleted += 1

        allure.attach(f"Удалено карточек: {deleted}", name="cleanup result",
                      attachment_type=allure.attachment_type.TEXT)


@pytest.fixture(scope="session")
def api_token():
    """Получает API-токен один раз на сессию для teardown-операций."""
    try:
        resp = requests.post(
            f"{API_URL}/Login",
            json={"email": FRONTEND_EMAIL, "password": FRONTEND_PASSWORD},
            timeout=30,
            verify=False,
        )
        resp.raise_for_status()
        return resp.json()["payload"]["token"]
    except (requests.ConnectionError, requests.Timeout) as e:
        pytest.skip(f"API недоступен — не удалось получить токен: {e}")
    except requests.HTTPError as e:
        pytest.skip(f"API вернул ошибку {resp.status_code} — не удалось получить токен")
    except (KeyError, requests.exceptions.JSONDecodeError):
        pytest.skip(f"API вернул невалидный ответ ({resp.status_code}) — не удалось получить токен")


def pytest_addoption(parser):
    """Регистрирует флаг --update-snapshots для обновления VRT-baseline.

    Использование:
        pytest --update-snapshots       # обновить все baseline
        pytest test.py --update-snapshots  # обновить baseline конкретного теста
    """
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Обновить baseline скриншоты",
    )


def pytest_collection_modifyitems(items):
    """Отключает reruns для тестов с маркером dependency.

    Зависимые тесты меняют состояние — повторный запуск после падения
    приведёт к каскадным ошибкам (например, задача уже сконвертирована).

    Debug-режим (TEST_TS, .debug_ts, или запуск без test_01):
    снимает маркеры dependency — тест запускается без зависимостей.
    """
    debug_mode = bool(os.environ.get("TEST_TS"))

    if not debug_mode:
        has_setup = any("test_01" in i.originalname for i in items)
        if not has_setup:
            debug_mode = True

    for item in items:
        if item.get_closest_marker("dependency"):
            item.add_marker(pytest.mark.flaky(reruns=0))

    if debug_mode:
        for item in items:
            item.own_markers = [m for m in item.own_markers if m.name != "dependency"]


def pytest_collection_finish(session):
    """Выводит в консоль стенд и URL перед запуском frontend-тестов.

    Срабатывает после сбора тестов, перед их запуском.
    Помогает убедиться что тесты запускаются на нужном стенде.
    """
    has_frontend = any(item.get_closest_marker("frontend") for item in session.items)
    if has_frontend:
        print(f"\n🧪 Running on stand: {FRONTEND_STAND}")
        print(f"🌐 UI URL: {BASE_URL}\n")


@pytest.fixture(scope="session", autouse=True)
def _configure_test_id(playwright):
    """Playwright по умолчанию ищет data-testid, переключаем на data-test-id."""
    playwright.selectors.set_test_id_attribute("data-test-id")


@pytest.fixture(scope="session")
def auth_state(playwright, _configure_test_id):
    """Логинится один раз на сессию и сохраняет состояние браузера.

    Открывает отдельный браузер, проходит логин и сохраняет куки и localStorage
    через storage_state(). Результат передаётся в browser_context_args и
    переиспользуется всеми тестами — каждый тест стартует уже залогиненным.

    Scope session означает что логин происходит ровно один раз за весь прогон.
    """
    # Подключаем WARP VPN если он установлен, но не подключён (только локально)
    if not os.environ.get("CI") and shutil.which("warp-cli"):
        try:
            status = subprocess.run(["warp-cli", "status"], capture_output=True, text=True, timeout=5)
            if "Disconnected" in status.stdout:
                subprocess.run(["warp-cli", "connect"], capture_output=True, timeout=10)
                time.sleep(3)
                print("🔗 WARP VPN подключён автоматически")
        except Exception:
            pass

    # Проверка доступности стенда перед логином (3 попытки с интервалом 10 сек)
    reason = ""
    for attempt in range(3):
        try:
            resp = requests.get(BASE_URL, timeout=10, verify=False)
            if resp.status_code < 500:
                break
            reason = f"вернул {resp.status_code}"
        except (requests.ConnectionError, requests.Timeout) as e:
            reason = str(e)
        if attempt < 2:
            print(f"⏳ Стенд недоступен ({reason}), повтор через 10 сек... ({attempt + 1}/3)")
            time.sleep(10)
    else:
        pytest.skip(f"Стенд недоступен после 3 попыток: {reason}")

    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    try:
        page.goto(f"{BASE_URL}/auth/sign-in", timeout=60000)
        # Step 1: Email
        page.get_by_test_id(Auth.EMAIL_INPUT).fill(FRONTEND_EMAIL)
        page.get_by_test_id(Auth.EMAIL_SUBMIT).click()
        # Step 2: Password
        page.get_by_test_id(Auth.PASSWORD_INPUT).wait_for(state="visible", timeout=15000)
        page.get_by_test_id(Auth.PASSWORD_INPUT).fill(FRONTEND_PASSWORD)
        page.get_by_test_id(Auth.PASSWORD_SUBMIT).click()
        # Wait for redirect
        page.get_by_test_id(Sidebar.HOME).wait_for(state="visible", timeout=30000)
        # Navigate to autotest space
        page.get_by_test_id(Header.SPACE_SELECTOR).click()
        page.get_by_test_id(SpaceSelector.space(settings.AUTOTEST_SPACE_ID)).click()
        page.get_by_test_id(Sidebar.HOME).wait_for(state="visible", timeout=15000)
    except Exception as e:
        context.close()
        browser.close()
        pytest.skip(f"Стенд недоступен — логин не прошёл: {str(e).split(chr(10))[0]}")
    state = context.storage_state()
    context.close()
    browser.close()
    return state


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    """Настраивает браузерный контекст для всех тестов.

    Переопределяет стандартные настройки pytest-playwright:
    - storage_state: внедряет сохранённую сессию, тест стартует залогиненным
    - ignore_https_errors: игнорирует SSL-ошибки на dev-стенде
    - viewport: фиксирует размер окна для стабильных VRT-скриншотов
    """
    ctx = {
        **browser_context_args,
        "ignore_https_errors": True,
        "storage_state": auth_state,
        "viewport": {"width": 1280, "height": 720},
    }
    ctx["record_video_dir"] = "test-results/videos"
    return ctx


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Сохраняет результат каждой фазы теста в атрибуты тест-айтема.

    Нужен чтобы фикстура attach_on_failure могла узнать упал ли тест —
    внутри фикстуры эта информация иначе недоступна.
    tryfirst=True гарантирует что хук выполняется до других хуков.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture
def soft_step(request, page):
    """Обёртка для шагов с soft assertion — тест продолжается при ошибке.

    При падении шага:
    - Классифицирует ошибку Playwright в человекочитаемую подсказку
    - Прикладывает скриншот страницы и краткий лог к Allure
    - Собирает ошибки — тест продолжается до конца

    После выполнения всех шагов:
    - Если были ошибки — raise AssertionError (триггерит pytest-rerunfailures)
    - Для тестов-источников зависимости (@pytest.mark.dependency(name=...))
      шаг падает жёстко сразу (re-raise), чтобы pytest-dependency скипал зависимые тесты.

    Использование:
        with allure.step("Приоритет: Medium"):
            soft_step("Приоритет", lambda: page.get_by_text("Medium").click())
    """
    dep_marker = request.node.get_closest_marker("dependency")
    is_dependency = dep_marker is not None and dep_marker.kwargs.get("name") is not None

    failures = []

    def _soft_step(name, fn, timeout=15000):
        page.set_default_timeout(timeout)
        try:
            fn()
        except Exception as e:
            full = str(e)
            short = full.split("\nCall log:")[0].split("\n")[0]

            if "intercepts pointer events" in full:
                hint = "Элемент перекрыт другим элементом — попап, оверлей или изменилась вёрстка"
                for line in full.split("\n"):
                    if "intercepts pointer events" in line:
                        blocker = line.strip().lstrip("- ")
                        detail = f"{short}\nБлокирует: {blocker}"
                        break
                else:
                    detail = short
            elif "strict mode violation" in full:
                hint = "Найдено несколько элементов — уточните локатор"
                detail = short
            elif "Target closed" in full or "browser has been closed" in full:
                hint = "Браузер или страница закрылись — возможно предыдущий шаг сломал сессию"
                detail = short
            elif "disabled" in full and "enabled" in full:
                hint = "Элемент заблокирован (disabled) — проверьте состояние UI"
                detail = short
            elif ("Timeout" in full or "timeout" in full) and "waiting for" in full:
                hint = "Элемент не найден — возможно изменился UI или локатор устарел"
                detail = short
            elif "expected to be" in full:
                hint = "Проверка не прошла — элемент не соответствует ожиданию"
                detail = short
            elif "not visible" in full or "not attached" in full:
                hint = "Элемент не виден на странице — проверьте, что поле отображается"
                detail = short
            else:
                hint = "Непредвиденная ошибка"
                detail = short

            log_text = f"Причина: {hint}\n{detail}"
            print(f"\n{'=' * 60}")
            print(f"SOFT STEP FAILED: {name}")
            print(f"URL: {page.url}")
            print(f"Причина: {hint}")
            print(f"Детали: {detail}")
            print(f"{'=' * 60}\n")
            allure.attach(page.screenshot(), name=f"{name} — скриншот", attachment_type=allure.attachment_type.PNG)
            allure.attach(log_text, name=f"{name} — лог", attachment_type=allure.attachment_type.TEXT)

            if is_dependency:
                raise AssertionError(f"[{name}] {hint}") from e

            failures.append(f"[{name}] {hint}")
        finally:
            page.set_default_timeout(30000)

    yield _soft_step

    if failures:
        msg = f"Soft step failures ({len(failures)}):\n" + "\n".join(f"  - {f}" for f in failures)
        raise AssertionError(msg)


@pytest.fixture(autouse=True)
def attach_on_failure(request, page):
    """Прикладывает артефакты к Allure-отчёту при падении теста.

    Подключается автоматически к каждому тесту (autouse=True).

    После теста:
    - Упал: прикладывает скриншот, URL страницы и failure log
    - Всегда: прикладывает видеозапись теста
    """
    allure.dynamic.parameter("test_name", request.node.originalname)

    yield

    failed = getattr(getattr(request.node, "rep_call", None), "failed", False)

    # Снимаем скриншот и URL до закрытия страницы
    if failed:
        try:
            failure_screenshot = page.screenshot()
            failure_url = page.url
        except Exception:
            failure_screenshot = None
            failure_url = None

    # Cleanup задач до закрытия страницы (если есть данные)
    cleanup_info = getattr(request.node, "_cleanup_task_info", None)
    if cleanup_info:
        _run_task_cleanup(page, cleanup_info)

    # Debug teardown до закрытия страницы (если есть)
    debug_teardown = getattr(request.node, "_debug_teardown_fn", None)
    if debug_teardown:
        try:
            debug_teardown(page)
        except Exception:
            pass

    # Закрываем страницу чтобы видео финализировалось
    video = page.video
    page.close()

    screenshot_path = Path(request.node.fspath).parent / "__snapshots__" / f"{request.node.name}.png"

    if failed:
        if failure_screenshot:
            allure.attach(failure_screenshot, name="screenshot on failure", attachment_type=allure.attachment_type.PNG)
            # Сохраняем скриншот на диск для быстрого просмотра в IDE
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot_path.write_bytes(failure_screenshot)
        if failure_url:
            allure.attach(failure_url, name="page URL", attachment_type=allure.attachment_type.TEXT)
        rep = getattr(request.node, "rep_call", None)
        if rep and rep.longrepr:
            allure.attach(str(rep.longrepr), name="failure log", attachment_type=allure.attachment_type.TEXT)
    else:
        screenshot_path.unlink(missing_ok=True)

    # save_as ждёт полной финализации видео (в отличие от чтения raw-файла)
    if video:
        try:
            video_dir = Path(request.node.fspath).parent / "__snapshots__"
            video_save_path = video_dir / f"{request.node.name}_video.webm"
            video_save_path.parent.mkdir(parents=True, exist_ok=True)
            video.save_as(str(video_save_path))
            allure.attach(video_save_path.read_bytes(), name="video", attachment_type=allure.attachment_type.WEBM)
            video_save_path.unlink(missing_ok=True)
        except Exception:
            pass


@pytest.fixture(autouse=True)
def _auto_debug(request, page):
    """Автоматический setup/cleanup при запуске отдельного теста из IDE.

    Тестовый модуль opt-in через module-level функции:
        _debug_create(page)           — создаёт сущность (задачу, майлстоун)
        _debug_teardown(page)         — teardown после теста (архивация и т.д.)
        _debug_extra_setup = {        — доп. setup для конкретных тестов
            "test_12_...": fn(page),
        }

    Если модуль не определяет _debug_create — фикстура ничего не делает.
    При полном прогоне (test_01 в коллекции) — фикстура ничего не делает.

    Teardown сохраняется в request.node._debug_teardown_fn и выполняется
    в attach_on_failure до page.close() (гарантированно пока страница открыта).
    """
    module = request.module
    create_fn = getattr(module, "_debug_create", None)

    if not create_fn:
        yield
        return

    module_items = [i for i in request.session.items if i.fspath == request.fspath]
    is_full_suite = any("test_01" in i.originalname for i in module_items)
    current = request.node.originalname

    if is_full_suite or current.startswith(("test_01", "test_99")):
        yield
        return

    # Setup
    create_fn(page)

    extra = getattr(module, "_debug_extra_setup", {})
    if current in extra:
        extra[current](page)

    cleanup_fn = getattr(module, "_debug_cleanup", None)
    if cleanup_fn:
        cleanup_fn(request)

    # Регистрируем teardown для выполнения в attach_on_failure
    teardown_fn = getattr(module, "_debug_teardown", None)
    if teardown_fn:
        request.node._debug_teardown_fn = teardown_fn

    yield


@pytest.fixture
def sidebar(page):
    """Локатор правого сайдбара — для скоупинга проверок полей."""
    return page.locator('[class*="RightSidebar-module_Root"]')


@pytest.fixture
def assert_snapshot(request):
    """Фикстура для визуального сравнения скриншотов (VRT).

    Сравнивает переданный скриншот с сохранённым baseline попиксельно.
    Baseline хранится в __snapshots__/<stand>/<name>.png рядом с тест-файлом.
    При падении прикладывает к Allure три картинки: baseline, actual, diff.

    Аргументы:
        screenshot: байты скриншота, полученные через page.screenshot()
        name:       имя файла baseline, например "sign_in_success.png"
        threshold:  допустимый процент отличающихся пикселей (по умолчанию 0.1%)

    Пример использования:
        screenshot = page.screenshot(mask=[...])
        assert_snapshot(screenshot, name="my_page.png", threshold=3.0)

    Обновление baseline:
        pytest --update-snapshots           # все тесты
        pytest test.py --update-snapshots   # конкретный файл
    """
    def _assert(screenshot: bytes, name: str, threshold: float = 1.0):
        snapshot_dir = Path(request.fspath).parent / "__snapshots__" / FRONTEND_STAND
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = snapshot_dir / name
        test_name = request.node.originalname

        if not snapshot_path.exists():
            snapshot_path.write_bytes(screenshot)
            return

        if request.config.getoption("--update-snapshots"):
            snapshot_path.write_bytes(screenshot)
            pytest.skip(f"Baseline обновлён: {snapshot_path.name}.")

        # Удаляем артефакты прошлого падения перед новым сравнением
        (snapshot_dir / name.replace(".png", "_actual.png")).unlink(missing_ok=True)
        (snapshot_dir / name.replace(".png", "_diff.png")).unlink(missing_ok=True)

        baseline = Image.open(snapshot_path).convert("RGB")
        actual = Image.open(io.BytesIO(screenshot)).convert("RGB")

        if baseline.size != actual.size:
            allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
            allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)
            check.fail(
                f"[VRT {name}] Размер изменился: baseline {baseline.size} → actual {actual.size}. "
                f"Для обновления: pytest --update-snapshots / в CI: snapshot_test={test_name}"
            )
            return

        # Пиксель считается отличающимся если хоть один RGB-канал отличается больше чем на 10 единиц.
        # Порог 10 отфильтровывает субпиксельный шум рендеринга.
        diff = ImageChops.difference(baseline, actual)
        diff_pixels = sum(1 for p in diff.getdata() if any(c > 10 for c in p))
        total_pixels = baseline.width * baseline.height
        diff_pct = diff_pixels / total_pixels * 100

        # Генерируем diff-картинку если есть пиксельные различия
        diff_coords = [
            (i % baseline.width, i // baseline.width)
            for i, pixel in enumerate(diff.getdata())
            if any(c > 10 for c in pixel)
        ]

        allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
        allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)

        if diff_pct > threshold:
            if diff_coords:
                diff_highlighted = baseline.copy()
                draw = ImageDraw.Draw(diff_highlighted)
                for x, y in diff_coords:
                    draw.point((x, y), fill=(255, 0, 0))
                buf = io.BytesIO()
                diff_highlighted.save(buf, format="PNG")
                allure.attach(buf.getvalue(), name=f"diff ({diff_pct:.2f}%)", attachment_type=allure.attachment_type.PNG)

                diff_path = snapshot_dir / name.replace(".png", "_diff.png")
                diff_path.write_bytes(buf.getvalue())

            actual_path = snapshot_dir / name.replace(".png", "_actual.png")
            actual_path.write_bytes(screenshot)
            check.fail(
                f"[VRT {name}] Скриншот отличается от baseline на {diff_pct:.2f}% "
                f"(допустимо {threshold}%). "
                f"Для обновления: pytest --update-snapshots / в CI: snapshot_test={test_name}"
            )

    return _assert
