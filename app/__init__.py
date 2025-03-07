import os
from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from .config import Config

# Inicializar extensiones sin vincularlas a la app todavía
db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()
login_manager = LoginManager()
login_manager.login_view = 'login'  

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
