from flask.ext.wtf import Form
from wtforms import StringField, validators, TextAreaField


class ArticleForm(Form):
    title = StringField('Name', [validators.Length(min=3, max=75)])
    body = TextAreaField('Body')
