import allure


@allure.title('Test space name cannot be empty')
def test_me():
    a = 2
    print('test')
    assert a == 3
