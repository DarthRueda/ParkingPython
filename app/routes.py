from flask import render_template, redirect, url_for, flash, session, request
from . import db
from .forms import LoginForm, RegisterForm, ReservaForm, EditProfileForm
from .models import User, Reserva, Parking, Log
from datetime import datetime

def register_routes(app):

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data
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
            if user and user.check_password(form.password.data):  # Verificar la contraseña hasheada
                session['user'] = {
                    'user_id': user.user_id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email
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

    @app.route('/perfil', methods=['GET', 'POST'])
    def perfil():
        if 'user' not in session:
            return redirect(url_for('login'))
        user_id = session['user']['user_id']
        user = User.query.filter_by(user_id=user_id).first()
        form = EditProfileForm(obj=user)
        if form.validate_on_submit():
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.email = form.email.data
            user.plate = request.form.get('plate')  # Update the plate field
            db.session.commit()
            flash('Perfil actualizado exitosamente.')
            return redirect(url_for('home'))  # Redirect to home instead of perfil
        return render_template('perfil.html', user=user, form=form)

    @app.route('/parkings', methods=['GET'])
    def parkings():
        if 'user' not in session:
            return redirect(url_for('login'))
        parkings = Parking.query.all()
        return render_template('parkings.html', parkings=parkings)

    @app.route('/reservar_parking', methods=['POST'])
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
        return redirect(url_for('home'))  # Redirect to home instead of login

    @app.route('/info')
    def info():
        return render_template('info.html')

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

    @app.route('/reservar', methods=['GET'])
    def reservar():
        return redirect(url_for('parkings'))
    
    @app.route('/api/entrada', methods=['POST'])
    def entrada():
        data = request.get_json(force=True)
        plate = data.get('plate')

        if not plate:
            return {'error': 'Matricula no proporcionada'}, 400

        user = User.query.filter_by(plate=plate).first()

        if user:
            parking = Parking.query.filter_by(is_free=True).first()
            if parking:
                new_log = Log(
                    matricula=plate,
                    hora_entrada=datetime.now()
                )
                db.session.add(new_log)
                db.session.commit()
                return {'message': 'Benvingut al bernat el ferrer'}, 200
            else:
                return {'message': 'Matricula en el sistema, pero no hay parkings libres'}, 200
        else:
            return {'error': 'Matricula no encontrada'}, 404

        return data

    @app.route('/api/actualizarplaza', methods=['POST'])
    def actualizar_plaza():
        data = request.get_json(force=True)
        parking_id = data.get('plaza_parking')

        if not parking_id:
            return {'error': 'ID de plaza no proporcionado'}, 400

        parking = Parking.query.get(parking_id)

        if not parking:
            return {'error': 'Plaza no encontrada'}, 404

        parking.is_free = not parking.is_free
        db.session.commit()
        return {'message': 'Estado de la plaza actualizado'}, 200

    @app.route('/api/salida', methods=['POST'])
    def salida():
        data = request.get_json(force=True)
        plate = data.get('plate')

        if not plate:
            return {'error': 'Matricula no proporcionada'}, 400

        log = Log.query.filter_by(matricula=plate, hora_salida=None).first()

        if log:
            log.hora_salida = datetime.now()
            db.session.commit()
            return {'message': "Esperem veure't aviat"}, 200
        else:
            return {'error': 'Matricula no encontrada o ya ha salido'}, 404