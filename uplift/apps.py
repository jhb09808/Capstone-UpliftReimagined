from django.apps import AppConfig
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class YourAppNameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "uplift"

@app.route('/')
def home():
    return "Hello, CORS-enabled world!"

if __name__ == '__main__':
    app.run()

