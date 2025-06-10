from backend_tests.config.settings import API_URL


def test_env_loaded():
    assert API_URL is not None
    print("API_URL =", API_URL)
