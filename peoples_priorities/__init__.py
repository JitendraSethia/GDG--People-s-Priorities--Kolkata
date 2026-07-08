import os

from flask import Flask, send_from_directory


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    from config import Config
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    from . import db
    db.init_app(app)

    from .blueprints.citizen import citizen_bp
    from .blueprints.official import official_bp
    from .blueprints.api import api_bp

    app.register_blueprint(citizen_bp)
    app.register_blueprint(official_bp, url_prefix="/officials")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app
