from flask import render_template, redirect, url_for, flash, session, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from .forms import LoginForm, RegisterForm, ReservaForm, EditProfileForm
from .models import User, Reserva, Parking, Log
from datetime import datetime
import time
import requests

def register_routes(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register_user():
        form = RegisterForm()
        if form.validate_on_submit():
            print("✅ El formulario es válido y se está procesando.")
        else:
            print("❌ El formulario tiene errores:", form.errors)


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
                flash('Registro exitoso. Por favor, inicia sesión.')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                print({e})
                flash('Error al registrar el usuario.')
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True) 
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
        if not current_user.is_authenticated:
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
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        parkings = Parking.query.all()
        free_parkings, occupied_parkings = calculate_parking_counts()
        free_percentage, occupied_percentage = calculate_parking_percentages()
        return render_template('disponibilidad.html', parkings=parkings, free_parkings=free_parkings, occupied_parkings=occupied_parkings, free_percentage=free_percentage, occupied_percentage=occupied_percentage)


   # Guardar matriculas para el Cooldown
    matricula_cooldown = {}

    # Cooldown para leer las matriculas
    COOLDOWN_TIME = 10

    # URL del ESP32 
    ESP32_URL = "http://172.16.1.116:81/api/abrirbarrera"

    @app.route('/api/entrada', methods=['POST'])
    def entrada():
        try:
            data = request.get_json()
            if not data or 'matricula' not in data:
                return jsonify({'error': 'Matrícula no detectada'}), 400

            matricula = data['matricula']
            current_time = time.time()

            # Verificar cooldown
            if matricula in matricula_cooldown:
                last_detected = matricula_cooldown[matricula]
                if current_time - last_detected < COOLDOWN_TIME:
                    return jsonify({'message': 'Matrícula ignorada por tiempo de espera'}), 429

            matricula_cooldown[matricula] = current_time

            # Buscar usuario en la base de datos
            user = User.query.filter_by(plate=matricula).first()

            if not user:
                return jsonify({'error': 'Matrícula no registrada'}), 403

            # Verificar si el vehículo está saliendo
            ultimo_registro = Log.query.filter_by(user_id=user.user_id, plate=matricula, hora_salida=None).first()

            if ultimo_registro:
                # Registrar salida
                ultimo_registro.hora_salida = db.func.now()
                db.session.commit()

                # Llamar al ESP32 para abrir la barrera
                try:
                    response = requests.get(ESP32_URL, timeout=5)  
                    if response.status_code == 200:
                        print(f"Barrera abierta correctamente para matrícula {matricula}")
                    else:
                        print(f"Error al activar la barrera: Código de estado {response.status_code}")
                except requests.ConnectionError:
                    print("Error: No se pudo conectar con la ESP32.")
                except requests.Timeout:
                    print("Error: Tiempo de espera agotado al intentar conectar con la ESP32.")
                except requests.RequestException as e:
                    print(f"Error inesperado al comunicarse con la ESP32: {e}")

                return jsonify({
                    'message': 'Salida registrada',
                    'plate': matricula,
                    'hora_salida': ultimo_registro.hora_salida
                }), 200

            # Si no está saliendo, registrar entrada
            parking_disponible = Parking.query.filter_by(is_free=True).first()
            if not parking_disponible:
                return jsonify({'error': 'No hay sitios disponibles'}), 409

            # Crear nuevo registro de entrada
            nuevo_log = Log(
                user_id=user.user_id,
                plate=matricula,
                hora_entrada=db.func.now(),
                parking_id=parking_disponible.parking_id
            )
            db.session.add(nuevo_log)
            parking_disponible.is_free = False  
            db.session.commit()

            # Llamar al ESP32 para abrir la barrera
            try:
                response = requests.get(ESP32_URL, timeout=5) 
                if response.status_code == 200:
                    print(f"Barrera abierta correctamente para matrícula {matricula}")
                else:
                    print(f"Error al activar la barrera: Código de estado {response.status_code}")
            except requests.ConnectionError:
                print("Error: No se pudo conectar con la ESP32.")
            except requests.Timeout:
                print("Error: Tiempo de espera agotado al intentar conectar con la ESP32.")
            except requests.RequestException as e:
                print(f"Error inesperado al comunicarse con la ESP32: {e}")

            print(f'Entrada registrada para matrícula {matricula}')

            return jsonify({
                'message': 'Entrada registrada',
                'plate': matricula,
                'hora_entrada': nuevo_log.hora_entrada
            }), 200

        except Exception as e:
            db.session.rollback()
            print(f"Error interno del servidor: {e}")
            return jsonify({'error': 'Error interno del servidor'}), 500
    

    @app.route('/api/actualizarplaza', methods=['POST'])
    def actualizar_plaza():
        try:
            data = request.get_json()
            print(f"📥 Datos recibidos: {data}")  # Log de entrada

            # Verificar si los datos son válidos
            if not data or 'parking_id' not in data or 'estado' not in data:
                print("⚠️ Datos inválidos en la solicitud")
                return jsonify({'error': 'Datos inválidos'}), 400
            
            try:
                parking_id = int(data['parking_id'])  # Aseguramos que sea un número
                estado = bool(int(data['estado']))  # Convertimos el estado a booleano
            except ValueError:
                print("❌ Error: parking_id o estado no son números válidos")
                return jsonify({'error': 'Formato inválido en parking_id o estado'}), 400

            # Buscar el parking en la base de datos
            parking = Parking.query.filter_by(parking_id=parking_id).first()
            if not parking:
                print(f"❌ Parking ID {parking_id} no encontrado en la BD")
                return jsonify({'error': 'Parking no encontrado'}), 404

            # Actualizar el estado del parking
            parking.is_free = estado
            db.session.commit()
            estado_texto = 'Libre' if estado else 'Ocupado'
            print(f"✅ Parking {parking_id} actualizado a {estado_texto}")

            return jsonify({'message': f'Estado actualizado correctamente a {estado_texto}'}), 200
        
        except Exception as e:
            db.session.rollback()
            print(f"🔥 Error en la API: {e}")  # Log del error
            return jsonify({'error': f'Error interno: {str(e)}'}), 500
