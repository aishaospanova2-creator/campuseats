import pytest
from app import app, dishes, orders

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Тест 1: Проверка получения списка блюд
def test_get_dishes(client):
    response = client.get('/api/dishes')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0

# Тест 2: Проверка создания нового заказа (Main Flow)
def test_create_order(client):
    payload = {
        "student_id": "ST-2026-999",
        "student_name": "Тестовый Студент",
        "items": [{"id": 1, "title": "Плов узбекский", "price": 450}],
        "pickup_time": "После 2-й пары (11:40 - 12:10)",
        "payment_method": "Kaspi QR"
    }
    response = client.post('/api/orders', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['order']['student_name'] == "Тестовый Студент"
    assert data['order']['payment_method'] == "Kaspi QR"
# Тест 3: Проверка обновления статуса заказа поваром
def test_update_order_status(client):
    order_id = orders[-1]['id'] if orders else 1
    response = client.patch(f'/api/orders/{order_id}/status', json={"status": "Готов к выдаче"})
    assert response.status_code == 200
    assert response.get_json()['order']['status'] == "Готов к выдаче"

# Тест 4: Проверка добавления нового блюда через админку
def test_add_dish_admin(client):
    new_dish = {
        "title": "Баурсаки горячие (10 шт)",
        "price": 300,
        "category": "Выпечка",
        "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500"
    }
    response = client.post('/api/dishes', json=new_dish)
    assert response.status_code == 200
    assert response.get_json()['success'] is True
