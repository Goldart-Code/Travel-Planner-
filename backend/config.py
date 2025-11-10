import os

# Визначаємо базову директорію проекту
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Клас конфігурації для Flask.
    Використовує змінні середовища для чутливих даних.
    """

    # Секретний ключ для підпису сесій
    # Для продакшену потрібно буде встановити його через змінну середовища.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-secret-key-for-development'

    # Конфігурація бази даних
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Налаштування для сесій (cookies)
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Для локальної розробки (http)
    SESSION_COOKIE_HTTPONLY = True

