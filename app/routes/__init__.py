def register_routes(app):
    """Register all route blueprints with the Flask app."""
    from app.routes.shortener import shortener_bp
    from app.routes.users import users_bp

    app.register_blueprint(shortener_bp)
    app.register_blueprint(users_bp)
