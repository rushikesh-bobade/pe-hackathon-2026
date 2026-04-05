def register_routes(app):
    """Register all route blueprints with the Flask app."""
    from app.routes.shortener import shortener_bp
    from app.routes.users import users_bp
    from app.routes.events import events_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(events_bp)
    # Shortener LAST — its /<short_code> is a catch-all
    app.register_blueprint(shortener_bp)
