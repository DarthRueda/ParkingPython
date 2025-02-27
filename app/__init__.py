import os
import logging
from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler
from .config import Config

# Inicializar extensiones sin vincularlas a la app todavía
db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()
login_manager = LoginManager()
login_manager.login_view = 'login'  

def configure_logging(app):
    if not os.path.exists('logs'):
        os.makedirs('logs')

    log_file = 'logs/app.log'
    handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    login_manager.init_app(app)

    # Importar modelos después de inicializar db (evita ciclos de importación)
    from .models import User  

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Configurar logs
    configure_logging(app)

    # Registrar rutas
    from .routes import register_routes
    register_routes(app)

    @app.route('/')
    def index():
        return redirect(url_for('home'))

    # Validación extra para los archivos estáticos
    @app.route('/static/<path:filename>')
    def static_files(filename):
        static_folder = app.static_folder
        file_path = os.path.join(static_folder, filename)

        if os.path.exists(file_path):
            return send_from_directory(static_folder, filename)
        return "Archivo no encontrado", 404

    return app
