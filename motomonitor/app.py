from flask import Flask
from flask_wtf.csrf import CSRFProtect
from models.db import init_db
from config import SECRET_KEY, UPLOAD_FOLDER
from routes import all_blueprints
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY
csrf = CSRFProtect(app)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
init_db()

for bp in all_blueprints:
    app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=True)
