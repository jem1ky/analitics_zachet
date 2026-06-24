from flask import Flask

from app.routes.web import register_routes


app = Flask(__name__, template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
register_routes(app)


if __name__ == "__main__":
    app.run(debug=True)
