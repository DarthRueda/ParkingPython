from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ReservaForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired()])
    last_name = StringField('Apellido', validators=[DataRequired()])
    plate = StringField('Matricula', validators=[DataRequired()])
    vehicle_type = SelectField('Tipo de Vehículo', choices=[('Carro', 'Carro'), ('Moto', 'Moto'), ('Bicicleta', 'Bicicleta'), ('Patinete', 'Patinete')], validators=[DataRequired()])
    start_date = StringField('Fecha Inicio', validators=[DataRequired()])
    end_date = StringField('Fecha Final', validators=[DataRequired()])
    submit = SubmitField('Reservar')