import logging
from flask import Flask, flash, request, make_response, redirect, render_template, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import pymysql
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'CLAVE_OCULTA'  

# Conexión a la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root2025@localhost/ParkingPython_DB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    db = SQLAlchemy(app)
    logging.info("Conexión a la base de datos establecida correctamente")
except OperationalError as e:
    db = None
    logging.error(f"Error de conexión a la base de datos: {e.orig}")

# Modelo de usuario
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=True) 

    def __str__(self):
        return self.first_name

# Formulario de inicio de sesión
class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Página de inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if db is None:
        flash('No se ha podido conectar a la base de datos')
        return render_template('error.html')

    if login_form.validate_on_submit():
        email = login_form.email.data  
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()  

        if user:
            if user.password and check_password_hash(user.password, password):
                # Variable de sesion
                session['user'] = {
                    'user_id': user.user_id,
                    'first_name': user.first_name
                }

                flash('Inicio de sesión exitoso')
                return redirect('/home')
            else:
                flash('Contraseña incorrecta')
        else:
            flash('Usuario no encontrado')

    return render_template('login.html', form=login_form) 

class RegisterForm(FlaskForm):
    username = StringField('nombre', validators=[DataRequired()])
    lastname = StringField('apellidos', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('Register')

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()

    if db is None:
        flash('No se ha podido conectar a la base de datos')
        return render_template('error.html')
    
    if register_form.validate_on_submit():
        username = register_form.username.data
        lastname = register_form.lastname.data
        email = register_form.email.data  
        password = register_form.password.data
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('El correo electrónico ya está registrado. Intente con otro.')
            return redirect('/register')

        # Crear un nuevo usuario con la contraseña hasheada
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(first_name=username, last_name=lastname, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registro exitoso. Ahora puede iniciar sesión.')
            return redirect('/login')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al registrar usuario: {e}")
            flash('Ocurrió un error al registrar el usuario. Inténtelo de nuevo.')

    return render_template('register.html', form=register_form)

# página de perfil
@app.route('/perfil')
def perfil():
    # Llamada a la base de datos
    user_id = session['user']['user_id']
    user = User.query.filter_by(user_id=user_id).first()

    if user:
        logging.debug(f"Usuario encontrado: {user.first_name} {user.last_name}")
    else:
        logging.debug("Usuario no encontrado")

    return render_template('perfil.html', user=user)

# Edicion del perfil
@app.route('/editar_perfil', methods=['POST'])
def editar_perfil():
    if 'user' not in session:
        return redirect('/login')
    
    user_id = session['user']['user_id']
    user = User.query.filter_by(user_id=user_id).first()
    
    if user:
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.username = request.form['username']
        user.vehicle_type = request.form['vehicle_type']
        
        db.session.commit()
        flash('Perfil actualizado exitosamente.')
    else:
        flash('No se encontró la información del usuario.')
    
    return redirect('/perfil')

# Cerrar Sesion
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Has cerrado sesión exitosamente.')
    return redirect('/home')

# Página de inicio
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/login')
    user = session['user']
    return render_template('home.html', user=user)

# Página de Reserva
@app.route('/reserva')
def reserva():
    return render_template('reserva.html')


# Procesar Reserva
@app.route('/procesar_reserva', methods=['POST'])
def procesar_reserva():
    button_id = request.form['button_id']
    # Aquí puedes manejar la lógica según el botón que se haya presionado
    flash(f'Botón presionado: {button_id}')
    return redirect('reserva')

# Redireccion al iniciar el servidor 
first_request = True

@app.before_request
def initial_redirect():
    global first_request
    if first_request:
        first_request = False
        return redirect('/home')


# Crear tablas si no existen
if __name__ == '__main__':
    if db is not None:
        with app.app_context():
            try:
                db.create_all()
            except OperationalError as e:
                logging.error(f"Error creando las tablas: {e.orig}")

    app.run(host='0.0.0.0', port=91, debug=True)