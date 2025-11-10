import os
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=Config):
    # Налаштовуємо Flask, щоб він шукав 'index.html' у теці 'frontend'
    # Визначаємо шлях до теки 'frontend', яка лежить на рівень вище
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))

    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "Not authorized. Please log in."}), 401

    with app.app_context():
        from . import models

        from .routes import main as main_routes
        app.register_blueprint(main_routes, url_prefix='/api')

        db.create_all()

    # Додаємо роут, який віддає frontend
    @app.route('/')
    def index():
        """Віддає головну сторінку React-додатку."""
        return render_template("index.html")

    # Роут для статичної сторінки "Про додаток"
    @app.route('/about')
    def about():
        """Віддає статичну сторінку 'about.html'."""
        return render_template("about.html")

    return app