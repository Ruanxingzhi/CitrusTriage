from flask import Flask, render_template, g
from util.db import get_db

app = Flask(__name__)

app.config['SECRET_KEY'] = 'vbasfoiuypawpyfivawiyfvpaw'

from blueprint import project
app.register_blueprint(project.bp)

from blueprint import bug
app.register_blueprint(bug.bp)

app.add_url_rule('/', 'index', project.show_list)

@app.before_request
def open_db():
    g.db = get_db()

@app.teardown_request
def close_db(_):
    g.db.commit()
    g.db.close()

if __name__ == '__main__':
    app.run(debug=True)