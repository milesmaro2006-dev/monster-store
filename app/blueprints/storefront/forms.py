# Storefront forms
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import Length, Optional


class SearchForm(FlaskForm):
    q = StringField("Search", validators=[Optional(), Length(max=120)])