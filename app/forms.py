from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio."),
        Email(message="Ingrese un email válido.")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria."),
        Length(min=6, message="La contraseña debe tener al menos 6 caracteres.")
    ])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message="El nombre de usuario es obligatorio."),
        Length(min=4, max=25, message="El usuario debe tener entre 4 y 25 caracteres.")
    ])
    first_name = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio."),
        Length(min=2, max=50, message="El nombre debe tener entre 2 y 50 caracteres.")
    ])
    last_name = StringField('Apellido', validators=[
        DataRequired(message="El apellido es obligatorio."),
        Length(min=2, max=50, message="El apellido debe tener entre 2 y 50 caracteres.")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio."),
        Email(message="Ingrese un email válido.")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="La contraseña es obligatoria."),
        Length(min=6, message="Debe tener al menos 6 caracteres."),
    ])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message="Confirme su contraseña."),
        EqualTo('password', message="Las contraseñas no coinciden.")
    ])
    submit = SubmitField('Registrarse')

class ReservaForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired(message="El nombre es obligatorio.")])
    last_name = StringField('Apellido', validators=[DataRequired(message="El apellido es obligatorio.")])
    plate = StringField('Matrícula', validators=[
        DataRequired(message="La matrícula es obligatoria."),
        Length(min=6, max=10, message="Debe tener entre 6 y 10 caracteres."),
        Regexp(r'^[A-Z0-9-]+$', message="Formato inválido de matrícula.")
    ])
    vehicle_type = StringField('Tipo de Vehículo', validators=[DataRequired(message="El tipo de vehículo es obligatorio.")])
    start_date = DateField('Fecha de Inicio', format='%Y-%m-%d', validators=[DataRequired(message="Seleccione una fecha de inicio.")])
    end_date = DateField('Fecha de Fin', format='%Y-%m-%d', validators=[DataRequired(message="Seleccione una fecha de finalización.")])
    submit = SubmitField('Reservar Parking')

class EditProfileForm(FlaskForm):
    username = StringField('Usuario', validators=[
        DataRequired(message="El nombre de usuario es obligatorio."),
        Length(min=4, max=25, message="Debe tener entre 4 y 25 caracteres.")
    ])
    first_name = StringField('Nombre', validators=[
        DataRequired(message="El nombre es obligatorio."),
        Length(min=2, max=50, message="Debe tener entre 2 y 50 caracteres.")
    ])
    last_name = StringField('Apellido', validators=[
        DataRequired(message="El apellido es obligatorio."),
        Length(min=2, max=50, message="Debe tener entre 2 y 50 caracteres.")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="El email es obligatorio."),
        Email(message="Ingrese un email válido.")
    ])
    plate = StringField('Matrícula', validators=[
        DataRequired(message="La matrícula es obligatoria."),
        Length(min=6, max=10, message="Debe tener entre 6 y 10 caracteres."),
        Regexp(r'^[A-Z0-9-]+$', message="Formato inválido de matrícula.")
    ])
    submit = SubmitField('Guardar Cambios')
