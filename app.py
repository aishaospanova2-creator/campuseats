import os
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Настройка подключения к базе данных (PostgreSQL на Render или SQLite для локальной разработки)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель блюда в меню
class DishModel(db.Model):
    __tablename__ = 'dishes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False) # Первые блюда, Вторые блюда, Выпечка, Напитки
    image = db.Column(db.String(300), nullable=False)

# Создание таблиц и заполнение стартового меню при первом запуске
with app.app_context():
    db.create_all()
    # Проверяем, есть ли блюда в базе, если нет — добавляем стандартные
    if DishModel.query.count() == 0:
        default_dishes = [
            # Первые блюда
            {"title": "Суп куриный с лапшой", "price": 450, "category": "Первые блюда", "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500"},
            {"title": "Борщ украинский", "price": 500, "category": "Первые блюда", "image": "https://images.unsplash.com/photo-1594998893017-36147fc4e0ba?w=500"},
            
            # Вторые блюда
            {"title": "Плов узбекский", "price": 650, "category": "Вторые блюда", "image": "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?w=500"},
            {"title": "Котлета с пюре", "price": 600, "category": "Вторые блюда", "image": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=500"},
            
            # Выпечка
            {"title": "Самса с мясом", "price": 250, "category": "Выпечка", "image": "https://images.unsplash.com/photo-1626803775151-61d756612f77?w=500"},
            {"title": "Пирожок с картошкой", "price": 180, "category": "Выпечка", "image": "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?w=500"},
            
            # Напитки
            {"title": "Чай черный", "price": 100, "category": "Напитки", "image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500"},
            {"title": "Компот из сухофруктов", "price": 150, "category": "Напитки", "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"}
        ]
        
        for item in default_dishes:
            dish = DishModel(
                title=item["title"],
                price=item["price"],
                category=item["category"],
                image=item["image"]
            )
            db.session.add(dish)
        db.session.commit()

# Главная страница (отображение меню)
@app.route('/')
def index():
    dishes = DishModel.query.all()
    return render_template('index.html', dishes=dishes)

# Страница панели администратора
@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

# Страница кассы / кухни
@app.route('/cashier')
def cashier_panel():
    return render_template('cashier.html')

# API для получения списка блюд (используется в автотестах pytest)
@app.route('/api/dishes', methods=['GET'])
def get_dishes():
    dishes = DishModel.query.all()
    return jsonify([{
        "id": d.id,
        "title": d.title,
        "price": d.price,
        "category": d.category,
        "image": d.image
    } for d in dishes])

# API для добавления нового блюда (админка)
@app.route('/api/dishes', methods=['POST'])
def create_dish():
    data = request.get_json()
    new_dish = DishModel(
        title=data.get('title'),
        price=data.get('price'),
        category=data.get('category'),
        image=data.get('image', 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500')
    )
    db.session.add(new_dish)
    db.session.commit()
    return jsonify({"success": True, "id": new_dish.id}), 200

# API для редактирования существующего блюда (кнопка "Изменить" в админке)
@app.route('/api/dishes/<int:dish_id>', methods=['PUT', 'PATCH'])
def update_dish(dish_id):
    dish = DishModel.query.get_or_404(dish_id)
    data = request.get_json()
    
    if 'title' in data:
        dish.title = data['title']
    if 'price' in data:
        dish.price = data['price']
    if 'category' in data:
        dish.category = data['category']
    if 'image' in data:
        dish.image = data['image']
        
    db.session.commit()
    return jsonify({"success": True}), 200

# API для удаления блюда (кнопка "Удалить" в админке)
@app.route('/api/dishes/<int:dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    dish = DishModel.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    return jsonify({"success": True}), 200

if __name__ == '__main__':
    app.run(debug=True)