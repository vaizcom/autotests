from pathlib import Path

import allure
import pytest

from tests.test_frontend.core.settings import BASE_URL, FRONTEND_EMAIL, FRONTEND_PASSWORD


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Обновить baseline скриншоты",
    )


@pytest.fixture
def assert_snapshot(request):
    def _assert(screenshot: bytes, name: str, threshold: float = 0.1):
        """
        threshold — допустимый % отличающихся пикселей (0.1 = 0.1%).
        Маскировку динамических зон делай на уровне page.screenshot(mask=[...]).
        """
        from PIL import Image, ImageChops, ImageDraw
        import io

        snapshot_dir = Path(request.fspath).parent / "__snapshots__"
        snapshot_dir.mkdir(exist_ok=True)
        snapshot_path = snapshot_dir / name

        if not snapshot_path.exists() or request.config.getoption("--update-snapshots"):
            snapshot_path.write_bytes(screenshot)
            pytest.skip(f"Baseline сохранён: {snapshot_path.name}. Запусти тест снова.")

        # Удаляем артефакты прошлого падения перед новым сравнением
        (snapshot_dir / name.replace(".png", "_actual.png")).unlink(missing_ok=True)
        (snapshot_dir / name.replace(".png", "_diff.png")).unlink(missing_ok=True)

        baseline = Image.open(snapshot_path).convert("RGB")
        actual = Image.open(io.BytesIO(screenshot)).convert("RGB")

        if baseline.size != actual.size:
            allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
            allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)
            pytest.fail(
                f"Размер изменился: baseline {baseline.size} → actual {actual.size}.\n"
                f"Для обновления запусти: pytest --update-snapshots"
            )

        diff = ImageChops.difference(baseline, actual)
        diff_pixels = sum(1 for p in diff.getdata() if any(c > 10 for c in p))
        total_pixels = baseline.width * baseline.height
        diff_pct = diff_pixels / total_pixels * 100

        if diff_pct > threshold:
            actual_path = snapshot_dir / name.replace(".png", "_actual.png")
            actual_path.write_bytes(screenshot)

            diff_highlighted = baseline.copy()
            draw = ImageDraw.Draw(diff_highlighted)
            diff_coords = [
                (i % baseline.width, i // baseline.width)
                for i, pixel in enumerate(diff.getdata())
                if any(c > 10 for c in pixel)
            ]
            for x, y in diff_coords:
                draw.point((x, y), fill=(255, 0, 0))

            if diff_coords:
                xs = [p[0] for p in diff_coords]
                ys = [p[1] for p in diff_coords]
                padding = 5
                draw.rectangle(
                    [min(xs) - padding, min(ys) - padding,
                     max(xs) + padding, max(ys) + padding],
                    outline=(255, 0, 0), width=2
                )

            diff_path = snapshot_dir / name.replace(".png", "_diff.png")
            diff_highlighted.save(diff_path)

            allure.attach(snapshot_path.read_bytes(), name="baseline", attachment_type=allure.attachment_type.PNG)
            allure.attach(screenshot, name="actual", attachment_type=allure.attachment_type.PNG)
            allure.attach(diff_path.read_bytes(), name="diff", attachment_type=allure.attachment_type.PNG)

            pytest.fail(
                f"Скриншот отличается от baseline на {diff_pct:.2f}% пикселей "
                f"(допустимо {threshold}%).\n"
                f"Baseline:  {snapshot_path}\n"
                f"Actual:    {actual_path}\n"
                f"Diff:      {diff_path}\n"
                f"Для обновления запусти: pytest --update-snapshots"
            )

    return _assert


def pytest_collection_finish(session):
    has_frontend = any(item.get_closest_marker('frontend') for item in session.items)
    if has_frontend:
        from tests.test_frontend.core.settings import FRONTEND_STAND
        print(f"\n🧪 Running on stand: {FRONTEND_STAND}")
        print(f"🌐 UI URL: {BASE_URL}\n")


@pytest.fixture(scope="session")
def auth_state(playwright):
    """Логинится один раз на сессию и сохраняет состояние браузера."""
    browser = playwright.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(f"{BASE_URL}/auth/sign-in")
    page.get_by_role("textbox", name="Email").fill(FRONTEND_EMAIL)
    page.get_by_role("textbox", name="Password").fill(FRONTEND_PASSWORD)
    page.get_by_role("button", name="Continue with Email").click()
    page.wait_for_load_state("networkidle")
    state = context.storage_state()
    context.close()
    browser.close()
    return state


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, auth_state):
    """Все тесты стартуют уже залогиненными."""
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "storage_state": auth_state,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def attach_on_failure(request, page):
    """Прикладывает скриншот, URL и трейс к Allure при падении теста."""
    context = page.context
    context.tracing.start(screenshots=True, snapshots=True)

    yield

    failed = getattr(getattr(request.node, "rep_call", None), "failed", False)
    if failed:
        try:
            allure.attach(
                page.screenshot(),
                name="screenshot on failure",
                attachment_type=allure.attachment_type.PNG,
            )
            allure.attach(
                page.url,
                name="page URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            trace_path = Path(request.node.fspath).parent / "__snapshots__" / f"{request.node.name}.zip"
            context.tracing.stop(path=str(trace_path))
            allure.attach(
                trace_path.read_bytes(),
                name="playwright trace",
                attachment_type=allure.attachment_type.ZIP,
            )
        except Exception:
            context.tracing.stop()
    else:
        context.tracing.stop()
