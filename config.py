import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "jutan-office-dev-key"

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database", "jutan.db")

SQLALCHEMY_TRACK_MODIFICATIONS = False