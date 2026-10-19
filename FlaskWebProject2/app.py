"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request
from markupsafe import escape
app = Flask(__name__)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

@app.route("/",methods=['GET', 'POST'])  
def home():
    return render_template("form.html")

@app.route("/greet", methods=["GET","POST"])  
def greet():
    #username = request.form["name"]  # Получаем данные из формы
    return render_template("index.html",username = request.form["name"])  # Возвращаем ответ
if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)

