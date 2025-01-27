from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Reserva(db.Model):
    reserva_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    reservation_start_time = db.Column(db.TIMESTAMP, nullable=False)
    reservation_end_time = db.Column(db.TIMESTAMP, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=True)
    plate = db.Column(db.String(50), nullable=True)
    import_price = db.Column(db.Float, nullable=False)

    def __str__(self):
        return str(self.reserva_id)