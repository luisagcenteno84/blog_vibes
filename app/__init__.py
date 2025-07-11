from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = app.config['SECRET_KEY'] # Set secret key for session

    try:
        db.init_app(app)
        migrate.init_app(app, db)
        login.init_app(app)
        bootstrap.init_app(app)
    except Exception as e:
        app.logger.error(f"Error initializing database or extensions: {e}")
        raise # Re-raise the exception to ensure the container fails to start

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Register CLI commands
    from app import cli
    cli.init_app(app)

    return app

from app import models