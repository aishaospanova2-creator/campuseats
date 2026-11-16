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
            {"title": "Суп куриный с лапшой", "price": 450, "category": "Первые блюда", "image": "soup.jpg"},
            {"title": "Борщ украинский", "price": 500, "category": "Первые блюда", "image": "borsch.jpg"},
            
            # Вторые блюда
            {"title": "Плов узбекский", "price": 650, "category": "Вторые блюда", "image": "plov.jpg"},
            {"title": "Котлета с пюре", "price": 600, "category": "Вторые блюда", "image": "cutlet.jpg"},
            
            # Выпечка
            {"title": "Самса с мясом", "price": 250, "category": "Выпечка", "image": "samsa.jpg"},
            {"title": "Пирожок с картошкой", "price": 180, "category": "Выпечка", "image": "pie.jpg"},
            
            # Напитки
            {"title": "Чай черный", "price": 100, "category": "Напитки", "image": "tea.jpg"},
            {"title": "Компот из сухофруктов", "price": 150, "category": "Напитки", "image": "compot.jpg"}
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
        image=data.get('image', 'default.jpg')
    )
    db.session.add(new_dish)
    db.session.commit()
    return jsonify({"success": True, "id": new_dish.id}), 200

if __name__ == '__main__':
    app.run(debug=True)