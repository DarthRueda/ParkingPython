from flask import render_template, redirect, url_for, flash, session, request
from . import db
from .forms import LoginForm, RegisterForm, ReservaForm
from .models import User, Reserva
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
            if user and user.check_password(form.password.data):
                session['user'] = {
                    'user_id': user.user_id,
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
        return render_template('home.html')

    @app.route('/perfil')
    def perfil():
        if 'user' not in session:
            return redirect(url_for('login'))
        user_id = session['user']['user_id']
        user = User.query.filter_by(user_id=user_id).first()
        return render_template('perfil.html', user=user)

    @app.route('/reserva2', methods=['GET', 'POST'])
    def reserva2():
        form = ReservaForm()
        if form.validate_on_submit():
            button_id = request.form.get('button_id')
            session['parking'] = button_id
            return redirect(url_for('procesar_reserva'))
        return render_template('reserva2.html', form=form)

    @app.route('/procesar_reserva', methods=['POST'])
    def procesar_reserva():
        form = ReservaForm()
        if form.validate_on_submit():
            first_name = form.first_name.data
            last_name = form.last_name.data
            plate = form.plate.data
            vehicle_type = form.vehicle_type.data
            start_date = datetime.strptime(form.start_date.data, '%Y-%m-%d')
            end_date = datetime.strptime(form.end_date.data, '%Y-%m-%d')

            nueva_reserva = Reserva(
                user_id=session['user']['user_id'],
                first_name=first_name,
                last_name=last_name,
                plate=plate,
                vehicle_type=vehicle_type,
                reservation_start_time=start_date,
                reservation_end_time=end_date,
                import_price=0.0
            )

            db.session.add(nueva_reserva)
            db.session.commit()
            flash('Reserva completada exitosamente.')
            return redirect(url_for('perfil'))
        return redirect(url_for('reserva2'))

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        flash('Has cerrado sesión exitosamente.')
        return redirect(url_for('login'))