from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    plate = db.Column(db.String(50), unique=True, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    reservas = db.relationship('Reserva', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Reserva(db.Model):
    __tablename__ = 'reservas'
    reserva_id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(50), db.ForeignKey('users.plate'), nullable=False)

    def __repr__(self):
        return f'<Reserva {self.reserva_id}>'

class Parking(db.Model):
    __tablename__ = 'parking'
    parking_id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    is_free = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Parking {self.location} - {"Libre" if self.is_free else "Ocupado"}>'