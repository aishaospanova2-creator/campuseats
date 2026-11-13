from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+pymysql://root:@localhost:3306/campuseats'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class DishModel(db.Model):
  __tablename__ = 'dishes'
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(100), nullable=False)
  price = db.Column(db.Integer, nullable=False)
  category = db.Column(db.String(50), nullable=False)
  image = db.Column(db.String(300), nullable=False)
  is_hidden = db.Column(db.Boolean, default=False)  # Скрыто ли блюдо


class OrderModel(db.Model):
  __tablename__ = 'orders'
  id = db.Column(db.Integer, primary_key=True)
  student_id = db.Column(db.String(50), nullable=False)
  student_name = db.Column(db.String(100), nullable=False)
  pickup_time = db.Column(db.String(100), nullable=False)
  payment_method = db.Column(db.String(50), nullable=False)
  status = db.Column(
      db.String(50), default='Готовится'
  )  # Готовится, Готов, Выдан
  items = db.relationship(
      'OrderItemModel', backref='order', lazy=True, cascade='all, delete-orphan'
  )


class OrderItemModel(db.Model):
  __tablename__ = 'order_items'
  id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
  title = db.Column(db.String(100), nullable=False)
  price = db.Column(db.Integer, nullable=False)


with app.app_context():
  db.create_all()


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/cashier')
def cashier_page():
  return render_template('cashier.html')


@app.route('/admin')
def admin_page():
  return render_template('admin.html')


# API блюд: студенты видят только нескрытые, админ через параметр может видеть все
@app.route('/api/dishes', methods=['GET', 'POST'])
def handle_dishes():
  if request.method == 'POST':
    data = request.json
    new_dish = DishModel(
        title=data.get('title', 'Блюдо'),
        price=int(data.get('price', 0)),
        category=data.get('category', 'Вторые блюда'),
        image=data.get(
            'image',
            'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500',
        ),
        is_hidden=data.get('is_hidden', False),
    )
    db.session.add(new_dish)
    db.session.commit()
    return jsonify({
        'success': True,
        'dish': {
            'id': new_dish.id,
            'title': new_dish.title,
            'price': new_dish.price,
            'category': new_dish.category,
            'image': new_dish.image,
            'is_hidden': new_dish.is_hidden,
        },
    })

  show_all = request.args.get('all', 'false') == 'true'
  if show_all:
    dishes = DishModel.query.all()
  else:
    dishes = DishModel.query.filter_by(is_hidden=False).all()

  return jsonify([{
      'id': d.id,
      'title': d.title,
      'price': d.price,
      'category': d.category,
      'image': d.image,
      'is_hidden': d.is_hidden,
  } for d in dishes])


@app.route('/api/dishes/<int:dish_id>', methods=['PUT'])
def update_dish(dish_id):
  dish = DishModel.query.get_or_404(dish_id)
  data = request.json
  dish.title = data.get('title', dish.title)
  dish.price = int(data.get('price', dish.price))
  dish.category = data.get('category', dish.category)
  dish.image = data.get('image', dish.image)
  if 'is_hidden' in data:
    dish.is_hidden = data.get('is_hidden')
  db.session.commit()
  return jsonify({
      'success': True,
      'dish': {
          'id': dish.id,
          'title': dish.title,
          'price': dish.price,
          'category': dish.category,
          'image': dish.image,
          'is_hidden': dish.is_hidden,
      },
  })


@app.route('/api/dishes/<int:dish_id>', methods=['DELETE'])
def delete_dish(dish_id):
  dish = DishModel.query.get_or_404(dish_id)
  db.session.delete(dish)
  db.session.commit()
  return jsonify({'success': True})


@app.route('/api/orders', methods=['GET', 'POST'])
def handle_orders():
  if request.method == 'POST':
    data = request.json
    new_order = OrderModel(
        student_id=data.get('student_id', 'Не указан'),
        student_name=data.get('student_name', 'Студент'),
        pickup_time=data.get(
            'pickup_time', 'После 1-й пары (10:00 - 10:10)'
        ),
        payment_method=data.get('payment_method', 'Kaspi QR'),
        status='Готовится',
    )
    db.session.add(new_order)
    db.session.flush()

    for item in data.get('items', []):
      order_item = OrderItemModel(
          order_id=new_order.id,
          title=item.get('title', 'Блюдо'),
          price=int(item.get('price', 0)),
      )
      db.session.add(order_item)

    db.session.commit()
    return jsonify({'success': True})

  orders = OrderModel.query.all()
  return jsonify([{
      'id': o.id,
      'student_id': o.student_id,
      'student_name': o.student_name,
      'pickup_time': o.pickup_time,
      'payment_method': o.payment_method,
      'status': o.status,
      'items': [{'title': i.title, 'price': i.price} for i in o.items],
  } for o in orders])


@app.route('/api/orders/<int:order_id>/status', methods=['PATCH'])
def update_status(order_id):
  order = OrderModel.query.get_or_404(order_id)
  data = request.json
  order.status = data.get('status', order.status)
  db.session.commit()
  return jsonify({'success': True})


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
  order = OrderModel.query.get_or_404(order_id)
  db.session.delete(order)
  db.session.commit()
  return jsonify({'success': True})


if __name__ == '__main__':
  app.run(debug=True, port=5000)