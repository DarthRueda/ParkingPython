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

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        flash('Has cerrado sesión exitosamente.')
        return redirect(url_for('home'))

    @app.route('/disponibilidad', methods=['GET'])
    def disponibilidad():
        if 'user' not in session:
            return redirect(url_for('login'))
        parkings = Parking.query.all()
        total_parkings = len(parkings)
        free_parkings = sum(1 for p in parkings if p.is_free)
        occupied_parkings = total_parkings - free_parkings
        free_percentage = (free_parkings / total_parkings) * 100 if total_parkings > 0 else 0
        occupied_percentage = 100 - free_percentage
        return render_template('disponibilidad.html', parkings=parkings, free_parkings=free_parkings, occupied_parkings=occupied_parkings, free_percentage=round(free_percentage, 2), occupied_percentage=round(occupied_percentage, 2))

    # API para ESP32-CAM - Registro de entrada de vehículos
    @app.route('/api/entrada', methods=['POST'])
    def entrada():
        data = request.get_json()
        plate = data.get('plate')

        if not plate:
            return jsonify({'error': 'Matrícula no proporcionada'}), 400

        user = User.query.filter_by(plate=plate).first()

        if user:
            parking = Parking.query.filter_by(is_free=True).first()
            if parking:
                parking.is_free = False  # Marcar el parking como ocupado
                acceso = RegistroAcceso(user_id=user.user_id, plate=plate, tipo='entrada')
                log = Log(user_id=user.user_id, parking_id=parking.parking_id, hora_entrada=datetime.now())
                db.session.add_all([acceso, log])
                db.session.commit()
                return jsonify({'message': 'Bienvenido, acceso permitido'}), 200
            else:
                return jsonify({'message': 'Matrícula reconocida, pero no hay parkings disponibles'}), 200
        else:
            return jsonify({'error': 'Matrícula no registrada'}), 404

    # API para ESP32-CAM - Registro de salida de vehículos
    @app.route('/api/salida', methods=['POST'])
    def salida():
        data = request.get_json()
        plate = data.get('plate')

        if not plate:
            return jsonify({'error': 'Matrícula no proporcionada'}), 400

        log = Log.query.join(User).filter(User.plate == plate, Log.hora_salida.is_(None)).first()

        if log:
            log.hora_salida = datetime.now()
            parking = Parking.query.get(log.parking_id)
            if parking:
                parking.is_free = True  # Liberar la plaza de parking
            acceso = RegistroAcceso(user_id=log.user_id, plate=plate, tipo='salida')
            db.session.add(acceso)
            db.session.commit()
            return jsonify({'message': 'Salida registrada, hasta pronto'}), 200
        else:
            return jsonify({'error': 'Matrícula no encontrada o ya registrada como salida'}), 404

    # API para actualizar estado de plaza de parking
    @app.route('/api/actualizarplaza', methods=['POST'])
    def actualizar_plaza():
        data = request.get_json()
        parking_id = data.get('plaza_parking')

        if not parking_id:
            return jsonify({'error': 'ID de plaza no proporcionado'}), 400

        parking = Parking.query.get(parking_id)

        if not parking:
            return jsonify({'error': 'Plaza no encontrada'}), 404

        parking.is_free = not parking.is_free
        db.session.commit()
        return jsonify({'message': 'Estado de la plaza actualizado'}), 200
    
    def process_license_plate(image_path):
        img = cv2.imread(image_path)

        # Convertir a escala de grises
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Aplicar umbral adaptativo
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # Usar Tesseract para reconocer el texto
        plate_text = pytesseract.image_to_string(thresh, config='--psm 8')
        
        return plate_text.strip()

    @app.route('/api/procesar_imagen', methods=['POST'])
    def procesar_imagen():
        # Recibe la imagen de la ESP32-CAM y extrae la matrícula.
        if 'image' not in request.files:
            return jsonify({'error': 'No se envió ninguna imagen'}), 400

        image = request.files['image']
        image_path = f"temp/{image.filename}"  # Guardamos la imagen temporalmente
        image.save(image_path)

        # Extraer matrícula
        plate = process_license_plate(image_path)

        if not plate:
            return jsonify({'error': 'No se detectó matrícula'}), 400

        # Buscar usuario en la base de datos
        user = User.query.filter_by(plate=plate).first()

        if user:
            # Registrar la entrada en logs
            new_log = Log(user_id=user.user_id, hora_entrada=datetime.now())
            db.session.add(new_log)
            db.session.commit()
            return jsonify({'message': 'Acceso permitido', 'plate': plate}), 200
        else:
            return jsonify({'error': 'Matrícula no registrada'}), 404
