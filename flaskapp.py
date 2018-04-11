from flask import Flask, render_template, request, send_file
import click

import subprocess

import users.routes
import meds.routes
import update.routes
import notification.routes

import db
import db.util


import boto3
from botocore.exceptions import ClientError

from error import Error, response_for_error

app = Flask(__name__)
app.register_blueprint(users.routes.blueprint, url_prefix='/user')
app.register_blueprint(meds.routes.blueprint, url_prefix='/meds')
app.register_blueprint(update.routes.blueprint, url_prefix='/update')
app.register_blueprint(notification.routes.blueprint, url_prefix='/notification')

@app.errorhandler(Error)
def handle_error(error):
    return response_for_error(error)

# Home Directory
@app.route('/')
def hello_world():
	return render_template('index.html')

@app.route('/update/git', methods = ['GET', 'POST'])
def update():
	cmd = ["./hook.sh", ]
	return "hi"

@app.route('/database/connectiontest')
def connectiokn_test():
        config = db.config.read()
        output = "User: " + config['database']['user'] + "<br>Host: " + config['database']['host'] 
        
        return output

@app.route('/img/<img>')
def post_image(img):
    file_to_return = "/static/img/" + img
    #return send_file(file_to_return)
    print(file_to_return)
    return "<html><body><img style=\"max-height:500px;max-width:500px\;\" src=\"" + file_to_return + "\"/></body></html>"



# Command Line Utils
# NOT ACCESSIBLE BY WEB, DONT WORRY
# Use like so on terminal: `flask $CMD_NAME_HERE $ARG1 $ARG2 ... $ARGN

@app.cli.command("init-db")
def db_init(*args, **kwargs):
    db.util.init(*args, **kwargs)

@app.cli.command("add-user")
@click.option("--first", default="FIRST")
@click.option("--last", default="LAST")
@click.option("--email", default="EMAIL")
@click.option("--passwd", default="PASSWD")
def db_add_user(first, last, email, passwd):
    db.util.add_user(first, last, email, passwd)

if __name__ == '__main__':
  app.run(debug=True)
