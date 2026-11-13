import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_full_order_lifecycle_integration(client):
    # 1. Создание заказа студентом
    res = client.post('/api/orders', json={
        "student_id": "ST-2026-777",
        "student_name": "Ернар Сериков",
        "items": [{"id": 3, "title": "Плов узбекский", "price": 450}],
        "pickup_time": "После 2-й пары (11:40 - 12:10)",
        "payment_method": "Kaspi QR"
    })
    assert res.status_code == 200
    order_id = res.get_json()['order']['id']

    # 2. Проверка отображения у кассира
    all_orders = client.get('/api/orders').get_json()
    assert any(o['id'] == order_id for o in all_orders)

    # 3. Смена статуса кассиром
    patch_res = client.patch(f'/api/orders/{order_id}/status', json={"status": "Готов к выдаче"})
    assert patch_res.status_code == 200

    # 4. Выдача заказа
    del_res = client.delete(f'/api/orders/{order_id}')
    assert del_res.status_code == 200

def test_admin_menu_management_integration(client):
    # 1. Добавление блюда админом
    add_res = client.post('/api/dishes', json={
        "title": "Самса с сыром",
        "price": 320,
        "category": "Выпечка",
        "image": "[https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500](https://images.unsplash.com/photo-1601050690597-df0568f70950?w=500)"
    })
    assert add_res.status_code == 200
    dish_id = add_res.get_json()['dish']['id']

    # 2. Проверка появления блюда в меню
    dishes = client.get('/api/dishes').get_json()
    assert any(d['id'] == dish_id for d in dishes)

    # 3. Удаление блюда админом
    assert client.delete(f'/api/dishes/{dish_id}').status_code == 200