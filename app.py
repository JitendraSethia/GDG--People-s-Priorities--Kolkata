import os

from dotenv import load_dotenv

load_dotenv()

from peoples_priorities import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, host=host, port=5000)
