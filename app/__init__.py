from flask import Flask, g
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail

app = Flask(__name__)
#app.config['PROPAGATE_EXCEPTIONS'] = True
app.config.from_object('config')
app.config.from_envvar('APP_SETTINGS')

db = SQLAlchemy(app)
lm = LoginManager(app)
#lm.init_app(app)
lm.login_view = 'login'
mail = Mail(app)

from . import views
from . import user_views
from . import article_views

from .momentjs import momentjs
app.jinja_env.globals['momentjs'] = momentjs
app.jinja_env.globals['menu'] = {
    '/': "Home",
    '/article': 'Blog',
    '/login': 'Login',
    '/logout': 'Logout',
}
