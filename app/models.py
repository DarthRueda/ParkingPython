from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import enum
from datetime import datetime

# Enum para el tipo de acceso
class TipoAcceso(enum.Enum):
    ENTRADA = 'entrada'
    SALIDA = 'salida'

# Modelo de Usuarios
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    plate = db.Column(db.String(50), unique=True, nullable=True, index=True)  
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)

    reservas = db.relationship('Reserva', backref='user', lazy=True, cascade="all, delete-orphan")
    accesos = db.relationship('Log', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f'<User {self.username}>'


# Modelo de Parking
class Parking(db.Model):
    __tablename__ = 'parking'
    parking_id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    is_free = db.Column(db.Boolean, default=True)
    TimeStamp = db.Column(db.TIMESTAMP, server_default=db.func.now(), nullable=False)
    reservas = db.relationship('Reserva', backref='parking', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Parking {self.location} - {"Libre" if self.is_free else "Ocupado"}>'


# Modelo de Reservas
class Reserva(db.Model):
    __tablename__ = 'reservas'
    reserva_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.parking_id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'<Reserva {self.reserva_id} - Usuario {self.user_id} - Parking {self.parking_id}>'

# Modelo de Logs (Historial de acceso)
class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.parking_id', ondelete='SET NULL'), nullable=True)
    plate = db.Column(db.String(50), nullable=False, index=True)
    hora_entrada = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    hora_salida = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Log User {self.user_id} - Entrada: {self.hora_entrada} - Salida: {self.hora_salida}>'
