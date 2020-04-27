from scraper import books, load_data
from flask import Flask, render_template, url_for

import os


load_data()


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', books=books)
   

@app.route('/<subject>')
def topic(subject):
    return render_template(subject + '.html', books=books, subject=subject)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
