from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

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

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], password_hash=hashed_password)

    # Робимо першого зареєстрованого користувача адміном
    if User.query.count() == 0:
        new_user.is_admin = True

    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)

    # Повертаємо повний об'єкт користувача
    return jsonify(new_user.to_dict()), 201  # 201 Created


@main.route('/auth/login', methods=['POST'])
def login():
    """Логінить користувача."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({"error": "Invalid username or password"}), 401  # 401 Unauthorized

    login_user(user, remember=True)

    # Повертаємо повний об'єкт користувача
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
        # Повертаємо повний об'єкт користувача
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
    trips = Trip.query.filter_by(user_id=current_user.id).all()
    # Конвертуємо подорожі та їхні пункти призначення у JSON
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

    # Перевірка, чи належить подорож поточному користувачу
    if trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403  # 403 Forbidden

    # Пункти призначення видаляться автоматично завдяки 'cascade'
    db.session.delete(trip)
    db.session.commit()

    return "", 204  # 204 No Content


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

    new_dest = Destination(
        name=data['name'],
        lat=data['lat'],
        lng=data['lon'],
        trip_id=trip.id
    )
    db.session.add(new_dest)
    db.session.commit()

    return jsonify(new_dest.to_dict()), 201


@main.route('/destinations/<int:dest_id>', methods=['DELETE'])
@login_required
def delete_destination(dest_id):
    """Видаляє пункт призначення за ID."""
    dest = Destination.query.get_or_404(dest_id)

    # Перевірка, чи належить цей пункт поточному користувачу
    # (через перевірку належності подорожі)
    if dest.trip.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(dest)
    db.session.commit()

    return "", 204  # 204 No Content


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