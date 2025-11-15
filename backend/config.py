import os

# Визначаємо базову директорію проекту
basedir = os.path.abspath(os.path.dirname(__file__))

# Визначаємо, чи працюємо ми в режимі 'production'
IS_PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

class Config:
    """
    Клас конфігурації для Flask.
    Використовує змінні середовища для чутливих даних.
    """

    # Секретний ключ для підпису сесій
    # Для продакшену ПОТРІБНО буде встановити його через змінну середовища.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-secret-key-for-development'

    # Конфігурація бази даних
    # На Render ми будемо використовувати DATABASE_URL для збереження даних на диску.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Налаштування для сесій (cookies)
    SESSION_COOKIE_SAMESITE = 'Lax'
    # У режимі 'production' (на HTTPS) cookies мають бути 'Secure'
    SESSION_COOKIE_SECURE = IS_PRODUCTION
    SESSION_COOKIE_HTTPONLY = True