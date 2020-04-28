from scraper import books, load_data
from flask import Flask, render_template, url_for
from flask import send_from_directory

import os


load_data()


app = Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    return render_template('index.html', books=books)
   

@app.route('/<subject>')
def topic(subject):
    return render_template(subject + '.html', books=books, subject=subject)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
