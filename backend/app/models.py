# Тут описуємо структуру бази даних

from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import json  # знадобиться для to_dict


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login вимагає цю функцію, щоб знати, як завантажити
    користувача з сесії за його ID.
    """
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """
    Модель Користувача.
    UserMixin додає необхідні поля для Flask-Login
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    # Змінено на nullable=True, щоб дозволити міграцію на існуючих даних
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    password_hash = db.Column(db.String(128))

    # Поле для реалізації вимоги про "адміністративних користувачів"
    is_admin = db.Column(db.Boolean, default=False)

    # Зв'язок з подорожами (один користувач - багато подорожей)
    trips = db.relationship('Trip', backref='author', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        """Створює хеш пароля."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Перевіряє хеш пароля."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Повертає дані користувача у форматі JSON."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Trip(db.Model):
    """
    Модель Подорожі.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)

    # Зв'язок з користувачем (багато подорожей - один користувач)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Зв'язок з пунктами призначення
    destinations = db.relationship(
        'Destination',
        backref='trip',
        lazy='dynamic',
        cascade="all, delete-orphan",
        order_by='Destination.order_index'  # Порядок за замовчуванням
    )

    def to_dict(self):
        """Повертає дані подорожі у форматі JSON."""
        # Отримуємо пункти призначення вже у правильному порядку
        dests_list = [dest.to_dict() for dest in self.destinations]

        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'destinations': dests_list
        }

    def __repr__(self):
        return f'<Trip {self.name}>'


class Destination(db.Model):
    """
    Модель Пункту Призначення.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)

    # Зберігаємо як YYYY-MM-DD для простоти
    visit_date = db.Column(db.String(10), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # --- Сортування ---
    order_index = db.Column(db.Integer, nullable=False, default=0)

    # Зв'язок з подорожжю
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)

    def to_dict(self):
        """Повертає дані пункту призначення у форматі JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'lat': self.lat,
            'lng': self.lng,
            'trip_id': self.trip_id,
            'visit_date': self.visit_date,
            'notes': self.notes,
            'order_index': self.order_index
        }

    def __repr__(self):
        return f'<Destination {self.name}>'