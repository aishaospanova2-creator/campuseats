import json
import os
from datetime import date
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

app = Flask(__name__)

database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///campus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class DishModel(db.Model):
    __tablename__ = 'dishes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(300), nullable=False)


class OrderModel(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=True)
    group_id = db.Column(db.String(50), nullable=True)
    pickup_time = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    total_price = db.Column(db.Integer, nullable=True, default=0)
    status = db.Column(db.String(50), default='Новый')
    items = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.Date, default=date.today, nullable=False)


def init_db():
    db.create_all()

    inspector = inspect(db.engine)
    if inspector.has_table('orders'):
        columns = [col['name'] for col in inspector.get_columns('orders')]
        if 'created_at' not in columns:
            with db.engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE orders ADD COLUMN created_at DATE DEFAULT CURRENT_DATE")
                )

    if DishModel.query.count() == 0:
        default_dishes = [
            {"title": "Суп куриный с лапшой", "price": 450, "category": "Первые блюда", "image": "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500"},
            {"title": "Борщ", "price": 500, "category": "Первые блюда", "image": "https://images.unsplash.com/photo-1594998893017-36147fc4e0ba?w=500"},
            {"title": "Плов узбекский", "price": 650, "category": "Вторые блюда", "image": "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?w=500"},
            {"title": "Котлета с пюре", "price": 600, "category": "Вторые блюда", "image": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=500"},
            {"title": "Самса с мясом", "price": 250, "category": "Выпечка", "image": "https://images.unsplash.com/photo-1626803775151-61d756612f77?w=500"},
            {"title": "Пирожок с картошкой", "price": 180, "category": "Выпечка", "image": "https://images.unsplash.com/photo-1608198093002-ad4e005484ec?w=500"},
            {"title": "Чай черный", "price": 100, "category": "Напитки", "image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500"},
            {"title": "Компот из сухофруктов", "price": 150, "category": "Напитки", "image": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500"}
        ]
        for item in default_dishes:
            db.session.add(DishModel(
                title=item["title"],
                price=item["price"],
                category=item["category"],
                image=item["image"]
            ))
        db.session.commit()


with app.app_context():
    init_db()


@app.route('/')
def index():
    dishes = DishModel.query.all()
    return render_template('index.html', dishes=dishes)


@app.route('/admin')
def admin_panel():
    return render_template('admin.html')


@app.route('/cashier')
def cashier_panel():
    return render_template('cashier.html')


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


@app.route('/api/dishes', methods=['POST'])
def create_dish():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    category = (data.get('category') or '').strip()
    try:
        price = int(data.get('price', 0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Некорректная цена"}), 400

    if not title or not category or price < 0:
        return jsonify({"success": False, "error": "Заполните название, категорию и цену"}), 400

    new_dish = DishModel(
        title=title,
        price=price,
        category=category,
        image=(data.get('image') or 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500').strip()
    )
    db.session.add(new_dish)
    db.session.commit()
    return jsonify({"success": True, "id": new_dish.id}), 200


@app.route('/api/dishes/<int:dish_id>', methods=['PUT', 'PATCH'])
def update_dish(dish_id):
    dish = DishModel.query.get_or_404(dish_id)
    data = request.get_json() or {}

    if 'title' in data and str(data['title']).strip():
        dish.title = str(data['title']).strip()
    if 'price' in data:
        try:
            price = int(data['price'])
            if price < 0:
                return jsonify({"success": False, "error": "Цена не может быть отрицательной"}), 400
            dish.price = price
        except (ValueError, TypeError):
            return jsonify({"success": False, "error": "Некорректная цена"}), 400
    if 'category' in data and str(data['category']).strip():
        dish.category = str(data['category']).strip()
    if 'image' in data and str(data['image']).strip():
        dish.image = str(data['image']).strip()

    db.session.commit()
    return jsonify({"success": True}), 200


@app.route('/api/dishes/<int:dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
    dish = DishModel.query.get_or_404(dish_id)
    db.session.delete(dish)
    db.session.commit()
    return jsonify({"success": True}), 200


@app.route('/api/orders', methods=['GET', 'POST'])
def handle_orders():
    if request.method == 'GET':
        selected_date_str = request.args.get('date')
        target_date = date.today()

        if selected_date_str:
            try:
                target_date = date.fromisoformat(selected_date_str)
            except ValueError:
                return jsonify({"error": "Неверный формат даты. Используйте ГГГГ-ММ-ДД"}), 400

        orders = OrderModel.query.filter_by(created_at=target_date).order_by(OrderModel.id.desc()).all()
        return jsonify([{
            "id": o.id,
            "student_name": o.student_name,
            "group_id": o.group_id,
            "pickup_time": o.pickup_time,
            "payment_method": o.payment_method,
            "total_price": o.total_price,
            "status": o.status,
            "items": o.items,
            "created_at": o.created_at.isoformat() if o.created_at else date.today().isoformat()
        } for o in orders])

    try:
        data = request.get_json() or {}
        raw_items = data.get('items', [])
        if isinstance(raw_items, (list, dict)):
            items_str = json.dumps(raw_items, ensure_ascii=False)
        else:
            items_str = str(raw_items or '')

        try:
            total_price = int(data.get('total_price') or 0)
        except (ValueError, TypeError):
            total_price = 0

        new_order = OrderModel(
            student_name=(data.get('student_name') or 'Аноним').strip(),
            group_id=(data.get('group_id') or 'Не указана').strip(),
            pickup_time=(data.get('pickup_time') or 'Ближайшее время').strip(),
            payment_method=(data.get('payment_method') or 'Наличные').strip(),
            total_price=max(0, total_price),
            status='Новый',
            items=items_str,
            created_at=date.today()
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"success": True, "order_id": new_order.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/orders/<int:order_id>', methods=['PATCH', 'PUT'])
def update_order_status(order_id):
    order = OrderModel.query.get_or_404(order_id)
    data = request.get_json() or {}
    if 'status' in data and str(data['status']).strip():
        order.status = str(data['status']).strip()
        db.session.commit()
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "error": "No status provided"}), 400


if __name__ == '__main__':
    app.run(debug=True)