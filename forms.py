from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, HiddenField, SelectField, PasswordField, BooleanField, \
    SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_wtf.file import FileField

minLength = 4
maxLength = 20


class AddProduct(FlaskForm):
    name = StringField('Name')
    price = IntegerField('Price')
    stock = IntegerField('Stock')
    description = TextAreaField('Description')
    image = FileField('Image')


class EditProduct(FlaskForm):
    name = StringField('Name')
    price = IntegerField('Price')
    stock = IntegerField('Stock')
    description = TextAreaField('Description')


class AddToCart(FlaskForm):
    quantity = IntegerField('Quantity')
    id = HiddenField('ID')


class Checkout(FlaskForm):
    address = StringField('Адрес', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    country = StringField('Страна', validators=[DataRequired()])
    payment_type = SelectField('Payment Type', choices=[('online', 'Онлайн оплата'), ('offline', 'Наличная оплата')])


class Registration(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired(),
                                                Length(min=minLength, max=maxLength,
                                                       message="Имя должно быть от "
                                                               + str(minLength) + " до " + str(maxLength)
                                                               + " символов")])
    last_name = StringField('Фамилия', validators=[DataRequired(),
                                                   Length(min=minLength, max=maxLength,
                                                          message="Фамилия должна быть от "
                                                                  + str(minLength) + " до " + str(maxLength)
                                                                  + " символов")])
    phone_number = StringField('Телефон', validators=[DataRequired()])
    login = StringField('Логин', validators=[DataRequired(),
                                             Length(min=minLength, max=maxLength,
                                                    message="Логин должен быть от "
                                                            + str(minLength) + " до " + str(maxLength)
                                                            + " символов")])
    password = PasswordField('Пароль', validators=[DataRequired(),
                                                   Length(min=minLength, max=maxLength,
                                                          message="Пароль должен быть от "
                                                                  + str(minLength) + " до " + str(maxLength)
                                                                  + " символов")])
    password2 = PasswordField('Повтор пароля', validators=[DataRequired(),
                                                           EqualTo('password', message="Пароли не совпадают")])


class Login(FlaskForm):
    login = StringField('Логин', validators=[DataRequired(),
                                             Length(min=minLength, max=maxLength,
                                                    message="Логин должен быть от "
                                                            + str(minLength) + " до " + str(maxLength)
                                                            + " символов")])
    password = PasswordField('Пароль', validators=[DataRequired(),
                                                   Length(min=minLength, max=maxLength,
                                                          message="Пароль должен быть от "
                                                                  + str(minLength) + " до " + str(maxLength)
                                                                  + " символов")])
    remember = BooleanField("Запомнить", default=False)


class LoginAdmin(FlaskForm):
    user = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])


class SearchProduct(FlaskForm):
    search = StringField("Поиск товара", validators=[DataRequired()])
    '''default="{{request.args.get('search',''}}"'''
    submit = SubmitField("Искать")
