import logging
from flask import render_template, redirect, url_for, flash, session, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .forms import LoginForm, RegisterForm, ReservaForm, EditProfileForm
from .models import User, Reserva, Parking, Log, RegistroAcceso
from datetime import datetime

# Configuración para la depuracion del codigo, diferentes tipos de errores
logging.basicConfig(
    filename='logs/app.log',  
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def register_routes(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register_user():
        form = RegisterForm()
        if form.validate_on_submit():
            try:
                user = User(
                    username=form.username.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                )
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                logger.info(f'Nuevo usuario registrado: {user.username}')
                flash('Registro exitoso. Por favor, inicia sesión.')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                logger.error(f'Error en registro: {str(e)}')
                flash('Error al registrar el usuario.')
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user) 
                flash('Inicio de sesión exitoso')
                return redirect(url_for('home')) 
            else:
                flash('Credenciales incorrectas')
        return render_template('login.html', form=form)

    @app.route('/home')
    @login_required  
    def home():
        return render_template('home.html', user=current_user)
    
    @app.route('/info')
    @login_required  
    def info():
        return render_template('info.html')

    @app.route('/perfil', methods=['GET', 'POST'])
    @login_required
    def perfil():
        user = current_user
        
        if not user:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('home'))
        
        form = EditProfileForm(obj=user)
        if form.validate_on_submit():
            try:
                user.username = form.username.data
                user.first_name = form.first_name.data
                user.last_name = form.last_name.data
                user.email = form.email.data
                user.plate = form.plate.data
                db.session.commit()
                flash('Perfil actualizado exitosamente.', 'success')
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error al actualizar perfil: {e}")
                flash('Error al actualizar perfil.', 'danger')
        
        return render_template('perfil.html', user=user, form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Has cerrado sesión')
        return redirect(url_for('login'))

    @app.route('/parkings')
    @login_required  
    def parkings():
        return render_template('parkings.html', parkings=Parking.query.all())

    @app.route('/reservar_parking', methods=['GET', 'POST'])
    def reservar_parking():
        if 'user' not in session:
            return redirect(url_for('login'))
        parking_id = request.form.get('parking_id')
        parking = Parking.query.get(parking_id)
        if parking and parking.is_free:
            parking.is_free = False
            db.session.commit()
            flash('Parking reservado exitosamente.')
        else:
            flash('El parking no está disponible.')
        return redirect(url_for('parkings'))

    def calculate_parking_percentages():
        total_parkings = 25
        free_parkings = Parking.query.filter_by(is_free=True).count()
        occupied_parkings = Parking.query.filter_by(is_free=False).count()
        free_percentage = (free_parkings / total_parkings) * 100
        occupied_percentage = (occupied_parkings / total_parkings) * 100
        return round(free_percentage, 2), round(occupied_percentage, 2)

    def calculate_parking_counts():
        free_parkings = Parking.query.filter_by(is_free=True).count()
        occupied_parkings = Parking.query.filter_by(is_free=False).count()
        return free_parkings, occupied_parkings

    @app.route('/disponibilidad', methods=['GET'])
    def disponibilidad():
        if 'user' not in session:
            return redirect(url_for('login'))
        parkings = Parking.query.all()
        free_parkings, occupied_parkings = calculate_parking_counts()
        free_percentage, occupied_percentage = calculate_parking_percentages()
        return render_template('disponibilidad.html', parkings=parkings, free_parkings=free_parkings, occupied_parkings=occupied_parkings, free_percentage=free_percentage, occupied_percentage=occupied_percentage)



    # ESP32 and ESP32CAM
    @app.route('/api/entrada', methods=['POST'])
    def entrada():
        try:
            data = request.get_json()
            if not data or 'matricula' not in data:
                return jsonify({'error': 'Matrícula no detectada'}), 400
            
            matricula = data['matricula']
            user = User.query.filter_by(plate=matricula).first()
            if not user:
                logger.warning(f'Intento de acceso con matrícula no registrada: {matricula}')
                return jsonify({'error': 'Matrícula no registrada'}), 403 
            
            parking_disponible = Parking.query.filter_by(is_free=True).first()
            if not parking_disponible:
                logger.warning(f'Sin espacios disponibles para la matrícula: {matricula}')
                return jsonify({'error': 'No hay sitios disponibles'}), 409
            
            registro = RegistroAcceso(user_id=user.user_id, plate=matricula, tipo='entrada')
            db.session.add(registro)
            parking_disponible.is_free = False
            db.session.commit()
            
            logger.info(f'Acceso permitido para matrícula {matricula}')
            return jsonify({'message': 'Acceso permitido'}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error en acceso de matrícula: {str(e)}')
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/actualizarplaza', methods=['POST'])
    def actualizar_plaza():
        try:
            data = request.get_json()
            if not data or 'parking_id' not in data or 'estado' not in data:
                return jsonify({'error': 'Datos inválidos'}), 400
            
            parking_id = data['parking_id']
            estado = bool(data['estado'])
            parking = Parking.query.filter_by(parking_id=parking_id).first()
            if not parking:
                return jsonify({'error': 'Parking no encontrado'}), 404
            
            parking.is_free = estado
            db.session.commit()
            estado_texto = 'Libre' if estado else 'Ocupado'
            logger.info(f'Actualización de plaza {parking_id} a estado: {estado_texto}')
            return jsonify({'message': 'Estado actualizado correctamente'}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al actualizar plaza: {str(e)}')
            return jsonify({'error': str(e)}), 500
