from app import create_app, db
from sqlalchemy import text
from app.models import Parking

def check_database():
    try:
        # Intentar conectar a la base de datos
        db.session.execute(text('SELECT 1'))
        print("Conexión a la base de datos exitosa.")
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")

def create_tables():
    db.create_all()
    print("Tablas creadas exitosamente.")

def insert_parking_data():
    if Parking.query.count() < 25:
        parkings = [
            Parking(location='Parking Arriba', is_free=True),
            Parking(location='Parking Abajo', is_free=False),
            Parking(location='Parking Arriba', is_free=True),
            Parking(location='Parking Abajo', is_free=True),
            Parking(location='Parking Arriba', is_free=False)
        ]
        db.session.bulk_save_objects(parkings)
        db.session.commit()
        print("Datos de parking insertados exitosamente.")
    else:
        print("Ya hay 25 o más plazas de parking. No se insertaron nuevos datos.")

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        check_database()
        create_tables()
        insert_parking_data()
    app.run(host='0.0.0.0', port=81, debug=True)
