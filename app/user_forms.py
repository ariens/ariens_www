from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, validators, HiddenField
from wtforms.validators import DataRequired


class EmailOnlyForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=35)])


class LoginForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('Password')
    remember_me = BooleanField('remember_me', default=False)


class ConfirmForm(Form):
    pass


class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=3, max=35)])
    email = StringField('E-mail Address', [validators.Email()])
    email_confirm = StringField(
        'E-mail (confirm)', [DataRequired(), validators.EqualTo('email', message='Must match %(other_label)s')])
    first_name = StringField('First Name', [validators.Length(min=2, max=35)])
    last_name = StringField('First Name', [validators.Length(min=2, max=35)])
    password = PasswordField('Password', [DataRequired(), validators.Length(min=6)])
    password_confirm = PasswordField(
        'Password (confirm)', [validators.EqualTo('password', message='Must match %(other_label)s')])


class PasswordResetForm(Form):
    activation_code = HiddenField('activation_code')
    password = PasswordField('Password', [DataRequired(), validators.Length(min=6)])
    password_confirm = PasswordField(
        'Password (confirm)', [validators.EqualTo('password', message='Must match %(other_label)s')])