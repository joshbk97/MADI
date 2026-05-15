from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_WEBAPP_ROOT = os.path.dirname(_PKG_DIR)
load_dotenv(os.path.join(_WEBAPP_ROOT, '.env'))

db = SQLAlchemy()
DB_NAME = 'database.db'


def create_app():
    app = Flask(__name__)

    # SQLite URI must be absolute so the DB is always beside this package (not cwd-dependent)
    _db_path = os.path.join(_PKG_DIR, DB_NAME).replace('\\', '/')
    _sqlite_uri = 'sqlite:///' + _db_path

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'madi-dev-fallback-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = _sqlite_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    # Avoid stale CSS/JS/HTML in the browser while developing (Flask defaults to long static max-age).
    _flask_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if _flask_debug:
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        @app.after_request
        def _dev_disable_document_cache(response):
            ct = response.headers.get('Content-Type', '')
            if 'text/html' in ct:
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            return response

    db.init_app(app)

    # Register blueprints
    from .views import views
    from .prediction import prediction
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(prediction, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Setup Flask-Login
    from .models import User

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Create database tables
    create_database(app)

    return app


def create_database(app):
    db_path = os.path.join(_PKG_DIR, DB_NAME)
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
            print('Database created.')
