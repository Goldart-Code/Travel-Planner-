from app import create_app, db
from app.models import User, Trip, Destination

# Створюємо екземпляр додатку
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Дозволяє працювати з моделями БД через 'flask shell'
    """
    return {'db': db, 'User': User, 'Trip': Trip, 'Destination': Destination}

if __name__ == '__main__':
    # Запускаємо додаток
    app.run(debug=True)