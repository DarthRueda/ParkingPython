class Config:
    # Conexión a la base de datos
    SECRET_KEY = 'secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/ParkingPython'
    SQLALCHEMY_TRACK_MODIFICATIONS = False