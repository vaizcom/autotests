



def test_user_db(main_client, db):
    # 1. Делаем API запрос на создание юзера
    # response = main_client.post(...)

    # 2. Идем напрямую в базу данных и проверяем, что юзер появился в коллекции "users"
    collection = db["users"]  # Имя коллекции в Монго

    user_in_db = collection.find_one({"email": "mastretsovaone+manager@gmail.com"})

    assert user_in_db is not None, "Пользователь не найден в базе данных"
    assert user_in_db["fullName"] == "manager"