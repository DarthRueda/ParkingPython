from . import db
from werkzeug.security import generate_password_hash, check_password_hash

# Modelo de Usuarios
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
    accesos = db.relationship('RegistroAcceso', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User {self.username}>'


# Modelo de Parking
class Parking(db.Model):
    __tablename__ = 'parking'
    parking_id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    is_free = db.Column(db.Boolean, default=True)

    reservas = db.relationship('Reserva', backref='parking', lazy=True)

    def __repr__(self):
        return f'<Parking {self.location} - {"Libre" if self.is_free else "Ocupado"}>'


# Modelo de Reservas
class Reserva(db.Model):
    __tablename__ = 'reservas'
    reserva_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.parking_id'), nullable=False)

    def __repr__(self):
        return f'<Reserva {self.reserva_id} - Usuario {self.user_id} - Parking {self.parking_id}>'


# Modelo de Registros de Acceso (para detección de matrículas)
class RegistroAcceso(db.Model):
    __tablename__ = 'registro_acceso'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    plate = db.Column(db.String(50), nullable=False)  # Matrícula detectada
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    tipo = db.Column(db.String(10))  # 'entrada' o 'salida'

    def __repr__(self):
        return f'<Acceso {self.plate} - {self.tipo} - {self.timestamp}>'


# Modelo de Logs (Historial de acceso)
class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    parking_id = db.Column(db.Integer, db.ForeignKey('parking.parking_id'), nullable=True)
    hora_entrada = db.Column(db.DateTime, nullable=False)
    hora_salida = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Log User {self.user_id} - Entrada: {self.hora_entrada} - Salida: {self.hora_salida}>'
