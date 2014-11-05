from flask.ext.wtf import Form
from wtforms import TextField, validators, TextAreaField


class ArticleForm(Form):
    title = TextField('Name', [validators.Length(min=3, max=75)])
    body = TextAreaField('Body')
