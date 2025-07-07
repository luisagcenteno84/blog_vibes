from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=140)])
    body = TextAreaField('Content', validators=[DataRequired()])
    thumbnail = StringField('Thumbnail URL', validators=[DataRequired()])
    status = SelectField('Status', choices=[('draft', 'Draft'), ('published', 'Published')], validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)')
    submit = SubmitField('Submit')

class ChatForm(FlaskForm):
    message = TextAreaField('Your Message', validators=[DataRequired()])
    submit = SubmitField('Send')

class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])