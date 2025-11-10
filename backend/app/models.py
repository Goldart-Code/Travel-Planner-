# Тут описуємо структуру бази даних

from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


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
    destinations = db.relationship('Destination', backref='trip', lazy='dynamic', cascade="all, delete-orphan")

    def to_dict(self):
        """Повертає дані подорожі у форматі JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'destinations': [dest.to_dict() for dest in self.destinations]
        }

    def __repr__(self):
        return f'<Trip {self.name}>'


class Destination(db.Model):
    """
    Модель Пункту Призначення.
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    address = db.Column(db.String(255))
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)

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
            'trip_id': self.trip_id
        }

    def __repr__(self):
        return f'<Destination {self.name}>'
