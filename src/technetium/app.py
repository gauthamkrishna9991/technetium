"""
Main Server Application
"""
from math import isfinite
from typing import Dict, List
from flask import Flask, request, flash, redirect, url_for, send_file, abort
from flask_cors import CORS
from flask_login import LoginManager, login_required
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from csv import DictReader, DictWriter
from os import environ, makedirs, walk, getcwd
from shutil import rmtree
from os.path import join, exists
from zipfile import ZipFile
from .models import AppType, PlayStoreElement, RatingRoundoff
from werkzeug.datastructures import FileStorage


# initialize app
app = Flask(__name__, instance_relative_config=True, template_folder="templates")
# Set up CORS
CORS(app, supports_credentials=True)
# Config Setup
app.config.from_object("config")
# OAUTHLIB setup
environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# Initialize Flask-SQLAlchemy Database
db: SQLAlchemy = SQLAlchemy(app)


# Initialize Flask Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"


# Import User Model
from technetium.auth.models import User


# Login Manager User Setup
@login_manager.user_loader
def load_user(user_id):
    # print(User.query.get(int(user_id)))
    return User.query.get(int(user_id))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("index.html")


@app.route("/load", methods=["POST"])
@login_required
def load_data():
    if request.method == "POST":
        if "data_file" not in request.files:
            flash("No file part")
            return redirect(url_for("dashboard"))
        file: FileStorage = request.files["data_file"]
        if file.filename == "":
            flash("No Selected File")
            return redirect(url_for("dashboard"))
        if (
            file
            and "." in file.filename
            and file.filename.rsplit(".", 1)[1].lower() == "csv"
        ):
            # Save the file to read, first.
            file.save("temp.csv")
            with open("temp.csv", "r") as data_file:
                playstore_data = list(
                    map(lambda x: PlayStoreElement(**x), DictReader(data_file))
                )
                # App Lists, Categorized as Free and Paid
                free_apps: List[PlayStoreElement] = []
                paid_apps: List[PlayStoreElement] = []
                app_type_outliers: List[PlayStoreElement] = []
                for playstore_ele in playstore_data:
                    if playstore_ele.app_type in [item.value for item in AppType]:
                        if playstore_ele.app_type == AppType.Free:
                            free_apps.append(playstore_ele)
                        elif playstore_ele.app_type == AppType.Paid:
                            paid_apps.append(playstore_ele)
                        else:
                            app_type_outliers.append(playstore_ele)
                    else:
                        app_type_outliers.append(playstore_ele)
                free_apps = round_off_values(free_apps)
                paid_apps = round_off_values(paid_apps)

                # App Lists, Further Categorized by Rating Roundoffs
                rated_free_apps: Dict[RatingRoundoff, List[PlayStoreElement]] = {
                    rroff: [] for rroff in RatingRoundoff
                }
                rated_paid_apps: Dict[RatingRoundoff, List[PlayStoreElement]] = {
                    rroff: [] for rroff in RatingRoundoff
                }
                for free_ele in free_apps:
                    rated_free_apps[RatingRoundoff(free_ele.rating_roundoff)].append(
                        free_ele
                    )
                for paid_ele in paid_apps:
                    rated_paid_apps[RatingRoundoff(paid_ele.rating_roundoff)].append(
                        paid_ele
                    )

                # Define the output directory, and the corresponding filename
                out_dir = "data"
                zipfile_name = out_dir + ".zip"

                # If directory tree exists, delete directory tree.
                if exists(out_dir):
                    rmtree(out_dir)

                # Build Rating Categorized Directory, Free Apps
                build_rating_path(rated_free_apps, join(out_dir, "free_apps"))
                # Build Rating Categorized Directory, Paid Apps
                build_rating_path(rated_paid_apps, join(out_dir, "paid_apps"))
                # Add up the outliers in outliers file
                build_csv_file(app_type_outliers, join(out_dir, "outliers.csv"))

                # Create a new ZIP file with the name zipfile_name
                with ZipFile(zipfile_name, "w") as zipfile:
                    # Walk through the directory tree and add all files into
                    # the zip file
                    for root, dirs, files in walk(out_dir):
                        for file in files:
                            zipfile.write(join(root, file))

                # Try sending the zip file back
                try:
                    return send_file(
                        join(getcwd(), zipfile_name), mimetype="application/zip"
                    )
                # If unable to be sent, send a 404.
                except FileNotFoundError as fe:
                    abort(404)
        else:
            flash("CSV File not given")
            return redirect(url_for("dashboard"))
        # return render_template("data.html")
    else:
        return redirect(url_for("dashboard"))


def build_rating_path(
    ratings_dict_list: Dict[RatingRoundoff, List[PlayStoreElement]], parent_path: str
):
    # Make the directory for adding rating-categorized files
    makedirs(parent_path)
    # For each rating we have:
    for filename in [item for item in RatingRoundoff]:
        # Create the path. Since None has not path we used the string "UNRATED" instead
        path_part = str(filename.value) if filename.value is not None else "UNRATED"
        full_path = join(parent_path, path_part + ".csv")
        build_csv_file(ratings_dict_list[filename], full_path)


def build_csv_file(apps_data: List[PlayStoreElement], output_file: str):
    values = [app_data.dict(by_alias=True) for app_data in apps_data]
    with open(output_file, "w") as outfile:
        csvwriter = DictWriter(
            outfile,
            [
                "App",
                "Category",
                "Rating",
                "Reviews",
                "Size",
                "Installs",
                "Type",
                "Price",
                "Rating Roundoff",
                "Genres",
                "Last Updated",
                "Current Ver",
                "Android Ver",
                "Rating Roundoff",
            ],
            extrasaction="ignore",
        )
        csvwriter.writeheader()
        csvwriter.writerows(values)


def round_off_values(values: List[PlayStoreElement]) -> List[PlayStoreElement]:
    """
    Utility function for rounding off values for objects, if possible.
    """
    for i in values:
        if isfinite(float(i.rating)):
            i.rating_roundoff = 1 if round(i.rating) <= 1 else round(i.rating)
    return values


from technetium.auth.views import users_blueprint
from technetium.auth.views import google_blueprint

app.register_blueprint(users_blueprint, prefix="/users")
app.register_blueprint(google_blueprint, prefix="/login")
