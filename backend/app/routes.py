import re
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from . import db, login_manager  # Імпортуємо з __init__.py в поточній папці
from .models import User, Trip, Destination  # Імпортуємо з models.py в поточній папці

# Створюємо Blueprint 'main'
main = Blueprint('main', __name__)


# --- Функція завантаження користувача за ID для Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ======================================================
# РОУТИ АВТЕНТИФІКАЦІЇ
# ======================================================

@main.route('/auth/register', methods=['POST'])
def register():
    """Реєструє нового користувача."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirmPassword = data.get('confirmPassword')

    if not all([username, email, password, confirmPassword]):
        return jsonify({"error": "All fields are required"}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Invalid email format"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 400
    if password != confirmPassword:
        return jsonify({"error": "Passwords do not match"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(
        username=username,
        email=email,
        password_hash=hashed_password
    )
    if User.query.count() == 0:
        new_user.is_admin = True
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return jsonify(new_user.to_dict()), 201  # 201 Created


@main.route('/auth/login', methods=['POST'])
def login():
    """Логінить користувача."""
    data = request.get_json()
    login_identifier = data.get('username')
    password = data.get('password')
    if not login_identifier or not password:
        return jsonify({"error": "Username/Email and password are required"}), 400
    user = User.query.filter(
        or_(User.username == login_identifier, User.email == login_identifier)
    ).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401
    login_user(user, remember=True)
    return jsonify(user.to_dict()), 200


@main.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Вихід користувача."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@main.route('/auth/status', methods=['GET'])
def status():
    """Перевіряє, чи авторизований поточний користувач."""
    if current_user.is_authenticated:
        return jsonify({
            "isAuthenticated": True,
            "user": current_user.to_dict()
        }), 200
    else:
        return jsonify({"isAuthenticated": False}), 200


# ======================================================
# РОУТИ ПОДОРОЖЕЙ
# ======================================================

@main.route('/trips', methods=['GET'])
@login_required
def get_trips():
    """Отримує всі подорожі поточного користувача."""
    # Модель Trip тепер автоматично сортує 'destinations'
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    trips_data = [trip.to_dict() for trip in trips]
    return jsonify(trips_data), 200


@main.route('/trips', methods=['POST'])
@login_required
def create_trip():
    """Створює нову подорож."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Trip name is required"}), 400
    new_trip = Trip(name=data['name'], user_id=current_user.id)
    db.session.add(new_trip)
    db.session.commit()
    return jsonify(new_trip.to_dict()), 201


@main.route('/trips/<int:trip_id>', methods=['DELETE'])
@login_required
def delete_trip(trip_id):
    """Видаляє подорож за ID."""
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    db.session.delete(trip)
    db.session.commit()
    return "", 204


# ======================================================
# РОУТИ ПУНКТІВ ПРИЗНАЧЕННЯ
# ======================================================

@main.route('/trips/<int:trip_id>/destinations', methods=['POST'])
@login_required
def add_destination(trip_id):
    """Додає новий пункт призначення до подорожі."""
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if not data or not data.get('name') or not data.get('lat') or not data.get('lon'):
        return jsonify({"error": "Missing data (name, lat, lon required)"}), 400

    # Встановлюємо order_index, щоб новий елемент був останнім
    max_index = db.session.query(db.func.max(Destination.order_index)).filter_by(trip_id=trip.id).scalar() or 0

    new_dest = Destination(
        name=data['name'],
        lat=data['lat'],
        lng=data['lon'],
        trip_id=trip.id,
        order_index=max_index + 1
    )
    db.session.add(new_dest)
    db.session.commit()
    return jsonify(new_dest.to_dict()), 201


@main.route('/destinations/<int:dest_id>', methods=['DELETE'])
@login_required
def delete_destination(dest_id):
    """Видаляє пункт призначення за ID."""
    dest = Destination.query.get_or_404(dest_id)
    if dest.trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    db.session.delete(dest)
    db.session.commit()
    return "", 204


# --- НОВИЙ РОУТ ---
@main.route('/destinations/<int:dest_id>', methods=['PATCH'])
@login_required
def update_destination(dest_id):
    """Оновлює пункт призначення (координати, дату, нотатки)."""
    dest = Destination.query.get_or_404(dest_id)
    if dest.trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()

    # Оновлення координат
    if 'lat' in data:
        dest.lat = data['lat']
    if 'lng' in data:
        dest.lng = data['lng']

    # Оновлення нотаток і дати
    if 'visit_date' in data:
        dest.visit_date = data['visit_date']
    if 'notes' in data:
        dest.notes = data['notes']

    db.session.commit()
    return jsonify(dest.to_dict()), 200


# --- НОВИЙ РОУТ ---
@main.route('/trips/<int:trip_id>/destinations/reorder', methods=['POST'])
@login_required
def reorder_destinations(trip_id):
    """Оновлює порядок пунктів призначення."""
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    destination_ids = data.get('destination_ids')  # Очікуємо [3, 1, 2]

    if not destination_ids:
        return jsonify({"error": "Missing destination_ids"}), 400

    # Оновлюємо order_index для кожного ID
    for index, dest_id in enumerate(destination_ids):
        dest = Destination.query.get(dest_id)
        if dest and dest.trip_id == trip.id:
            dest.order_index = index

    db.session.commit()
    return jsonify({"message": "Order updated"}), 200


# ======================================================
# АДМІН-РОУТИ
# ======================================================

@main.route('/admin/users', methods=['GET'])
@login_required
def get_all_users():
    """Повертає список всіх користувачів (тільки для адмінів)."""
    if not current_user.is_admin:
        return jsonify({"error": "Admin access required"}), 403
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200