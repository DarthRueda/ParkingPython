import os

class Config:
    # Conexión a la base de datos
    SECRET_KEY = 'secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:root2025@localhost/ParkingPython_DB'
    SQLALCHEMY_TRACK_MODIFICATIONS = False