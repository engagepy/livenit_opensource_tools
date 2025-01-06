import os
from flask import Flask
from flask_bootstrap import Bootstrap

my_secret = os.environ['SECRET_KEY']
id_key = 0

app = Flask(__name__)
import logic

app.config['SECRET_KEY'] = my_secret

Bootstrap(app)

if __name__ == '__main__':
  app.run(debug=False, host='0.0.0.0')
