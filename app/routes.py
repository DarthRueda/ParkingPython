from flask import render_template, redirect, url_for, flash, session, request, jsonify
from . import db
from .forms import LoginForm, RegisterForm, ReservaForm, EditProfileForm
from .models import User, Reserva, Parking, Log, RegistroAcceso
from datetime import datetime
import cv2
import numpy as np
import pytesseract

def register_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register_user():
        form = RegisterForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registro exitoso. Por favor, inicia sesión.')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                session['user'] = {
                    'user_id': user.user_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'plate': user.plate
                }
                flash('Inicio de sesión exitoso')
                return redirect(url_for('home'))
            else:
                flash('Contraseña incorrecta' if user else 'Usuario no encontrado')
        return render_template('login.html', form=form)

    @app.route('/home')
    def home():
        if 'user' not in session:
            return redirect(url_for('login'))
        return render_template('home.html', user=session['user'])
    
    @app.route('/info')
    def info():
        return render_template('info.html')

    @app.route('/perfil', methods=['GET', 'POST'])
    def perfil():
        if 'user' not in session:
            return redirect(url_for('login'))
        user_id = session['user']['user_id']
        user = User.query.get(user_id)
        form = EditProfileForm(obj=user)
        if form.validate_on_submit():
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.email = form.email.data
            user.plate = form.plate.data
            db.session.commit()
            flash('Perfil actualizado exitosamente.')
            return redirect(url_for('home'))
        return render_template('perfil.html', user=user, form=form)

    @app.route('/parkings', methods=['GET'])
    def parkings():
        if 'user' not in session:
            return redirect(url_for('login'))
        parkings = Parking.query.all()
        return render_template('parkings.html', parkings=parkings)

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

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        flash('Has cerrado sesión exitosamente.')
        return redirect(url_for('home'))
    
    @app.route('/api/entrada', methods=['POST'])
    def entrada():
        try:
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'No se recibió un JSON válido'}), 400
            
            matricula = data.get('matricula')
            if not matricula:
                return jsonify({'error': 'Matrícula no detectada'}), 400

            user = User.query.filter_by(plate=matricula).first()
            if not user:
                return jsonify({'error': 'Matrícula no registrada'}), 403 
            
            parking_disponible = Parking.query.filter_by(is_free=True).first()
            if not parking_disponible:
                return jsonify({'error': 'No hay sitios disponibles'}), 409
            
            registro = RegistroAcceso(user_id=user.user_id, plate=matricula, tipo='entrada')
            db.session.add(registro)

            parking_disponible.is_free = False
            db.session.commit()

            return jsonify({'message': 'Acceso permitido'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
    @app.route('/api/actualizarplaza', methods=['POST'])
    def actualizar_plaza():
        try:
            data = request.get_json()
            if not data or 'parking_id' not in data or 'estado' not in data:
                return jsonify({'error': 'Datos inválidos'}), 400

            parking_id = data['parking_id']
            estado = bool(data['estado'])  # 0 = Ocupado, 1 = Libre

            # Buscar el parking en la base de datos
            parking = Parking.query.filter_by(parking_id=parking_id).first()
            if not parking:
                return jsonify({'error': 'Parking no encontrado'}), 404

            # Actualizar el estado del parking
            parking.is_free = estado
            db.session.commit()

            return jsonify({'message': 'Estado actualizado correctamente'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500