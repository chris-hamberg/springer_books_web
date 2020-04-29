import pandas as pd
import lxml.html
import requests
import shelve
import os, sys
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


if not os.path.exists('database'):
    os.mkdir('database')
elif not os.path.isdir('database'):
    os.remove('database')
    os.mkdir('database')


xlsx = 'database/Free+English+textbooks.xlsx'
xfile = pd.ExcelFile(xlsx)
df = xfile.parse()


books = shelve.open('database/serial')


class Book:


    PARENT = 'https://link.springer.com'


    def __init__(self, idx, title, edition, subject, url):

        self.title      = title.replace('/', '_')
        self.idx        = idx

        self.name       = f'{self.title}, {edition}'
        self.subject    = self._process(subject)
        self._image_url = None
        self._url       = url

        self.pdf        = None
        self.epub       = None


    def __repr__(self):
        return f'{self.idx}: {self.name}'


    def __eq__(self, other):
        return self.idx == other.idx


    def _process(self, subject):

        subject = subject.split(';')[0]

        book = self

        try:
            books[subject].append(book)
        except (KeyError, AttributeError):
            books[subject] = []
            books[subject].append(book)

        self._make_template(book, subject)

        return subject


    def _make_template(self, book, subject):

        path = os.path.join('templates', subject)

        if os.path.exists(path):
            return
        else:
            html = '''{% extends "base.html" %}
{% block content %}

<hr>

<a href="{{ url_for('index') }}"><< BACK TO INDEX</a>

<hr>

<h1><center>{{ subject }} Books</center></h1>

    {% for book in books[subject] %}
        <hr>

        <h3>{{ book.name }}</h3>

        <img src="static/images/{{ book.image}}" />

        <p><u>DOWNLOAD</u>:

        {% if book.pdf %}
            <a href="{{ book.pdf }}">PDF</a>
        {% endif %}

        {% if book.epub %}
            <a href="{{ book.epub }}">EPUB</a>
        {% endif %}

        {% if not book.pdf and not book.epub %}
            <em>unavailable.</em>
        {% endif %}

        </p>

    {% endfor %}

{% endblock %}'''

            with open(path + '.html', 'w') as fhand:
                fhand.write(html)


    def _scrape(self):

        name = self.name.replace(' ', '_') + '.html'
        path = os.path.join('static', 'cache', name)

        if os.path.exists(path):
            with open(path, 'rb') as fhand:
                html = fhand.read()
                html = lxml.html.fromstring(html)
        else:
            response = requests.get(self._url)
            content  = response.content
            with open(path, 'wb') as fhand:
                fhand.write(content)
            html = lxml.html.fromstring(content)

        try:
            xpath, epub = self.__get_xpaths(html)
        except IndexError:
            print(f'Error: {self.idx} {self.name}'
                  ' server access point missing')
            return False

        else:
            self.__make_links(xpath, epub)

        finally:
            self.image = self.name.replace(' ', '_').replace('\\', '_') + '.jpeg'
            path       = os.path.join('static', 'images', self.image)
            if not os.path.exists(self.image):
                self.__set_image_url(html)
                try:
                    image = requests.get(self._image_url).content
                except:
                    image = ""
                finally:
                    with open(path, 'wb') as fhand:
                        fhand.write(image)
            


    def __get_xpaths(self, html):
        epub  = None
        xpath = html.xpath('//*[@id="main-content"]/article[1]/'
                           'div/div/div[2]/div/div/a')
        if not bool(xpath):
            xpath = html.xpath(
                '//*[@id="main-content"]/article[1]/div/div/div[2]/div[1]/a'
                )
            epub  = html.xpath(
                '//*[@id="main-content"]/article[1]/div/div/div[2]/div[2]/a'
                )
            epub = epub[0]
        xpath = xpath[0]
        return xpath, epub


    def __make_links(self, xpath, epub):
        stub     = xpath.get('href')
        self.pdf = __class__.PARENT + stub
        if epub is not None:
            stub      = epub.get('href')
            self.epub = __class__.PARENT + stub


    def __set_image_url(self, html):
        if self.pdf or self.epub:
            img_xpath = html.xpath(
                '//*[@id="main-content"]/article[1]/div/aside[1]/'
                'div/div/div/img'
            )
            img_xpath = None if not len(img_xpath) else img_xpath[0]
            self._image_url = img_xpath.get('src')
        else:
            self._image_url = ""


def load_data():

    for idx, row in df.iterrows():

        book = Book(idx, 
                df['Book Title'].iloc[idx], 
                df['Edition'].iloc[idx], 
                df['Subject Classification'].iloc[idx],
                df['OpenURL'].iloc[idx])
    
        try:    

            assert book in books[book.subject]
            logger.info(f' SKIPPING : {book.name}')
            continue

        except (KeyError, AssertionError) as init:

            subject = books[book.subject]
            book._scrape()
            subject.append(book)
            books[book.subject] = subject
            logger.info(f' SERIALIZED : {book.name}')

    else: books.close()
