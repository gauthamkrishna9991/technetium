"""User Auth Routes using Flask Dance."""

from flask import redirect, url_for, flash, render_template, Blueprint
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_login import current_user, login_required, login_user, logout_user


from technetium.app import app, db
from . import models


users_blueprint = Blueprint("auth", __name__, template_folder="templates")


google_blueprint = make_google_blueprint(
    client_id=app.config.get("GOOGLE_ID"),
    client_secret=app.config.get("GOOGLE_SECRET"),
    scope=["profile", "email"],
)

# setup SQLAlchemy backend
google_blueprint.backend = SQLAlchemyStorage(
    models.OAuth, db.session, user=current_user
)


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(google_blueprint)
def google_logged_in(blueprint, token):
    """Log in user on successful Google authorization."""
    if not token:
        flash("Failed to log in {name}".format(name=blueprint.name))
        return
    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        msg = "Failed to fetch user info from GitHub."
        flash(msg, category="error")
        return False

    user_info = resp.json()
    user_id = str(user_info["id"])
    query = models.OAuth.query.filter_by(
        provider=blueprint.name,
        provider_user_id=user_id,
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = models.OAuth(
            provider=blueprint.name,
            provider_user_id=user_id,
            token=token,
        )

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in with Google.")

    else:
        # Create a new local user account for this user
        username = user_info["email"]
        user = models.User(username=username)
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        login_user(user)
        flash("Successfully signed in with Google.")
    # Disable Flask-Dance's default behavior for saving the OAuth token
    # return False
    return redirect(url_for("dashboard"))


# notify on OAuth provider error
@oauth_error.connect_via(google_blueprint)
def google_error(blueprint, error, error_description=None, error_uri=None):
    """Throw error on authentication failure from Google."""
    msg = (
        "OAuth error from {name}! " "error={error} description={description} uri={uri}"
    ).format(
        name=blueprint.name,
        error=error,
        description=error_description,
        uri=error_uri,
    )
    flash(msg, category="error")


@users_blueprint.route("/logout")
@login_required
def logout():
    """Log out current user."""
    logout_user()
    return redirect(url_for("auth.login"))


@users_blueprint.route("/")
def login():
    """Create default route for unauthenticated redirect."""
    return render_template("login.html")
