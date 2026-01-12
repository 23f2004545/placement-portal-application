from flask import Flask , render_template
from models.db import db
from config import config

app = Flask(__name__)
# app.config.from_object(config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement_portal.db'
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def hello():
    return render_template('base.html')

if __name__ == '__main__':
    app.run(debug=True)