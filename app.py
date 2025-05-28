from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
from io import BytesIO
import json

from bb_config    import *
from bb_database  import *
from bb_api       import *
from bb_users     import *
from bb_songs     import *
from bb_wiki      import *
from bb_functions import *
from bb_errors    import *

@app.route('/')
def bb_index():
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
	return render_template("index.html", trending=trending, myself=myself)
	
@app.route('/welcome')
def bb_welcome():
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
	return render_template("welcome.html", trending=trending, myself=myself)


@app.route('/Jams')
@app.route('/Wiki')
def bb_under_construction():
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
	return render_template("workinprogress.html", trending=trending, myself=myself)



@app.route('/Account/login')
def bb_account_login():
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
	return render_template("login.html", trending=trending, myself=myself)
	
@app.route('/Account/register')
def bb_account_register():
	with bb_connect_db() as conn:
		db = conn.cursor()
		trending = bb_get_trending(db)
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
	return render_template("register.html", trending=trending, myself=myself)

@app.route('/Account/logout')
def bb_account_logout():
	with bb_connect_db() as conn:
		db = conn.cursor()
		trending = bb_get_trending(db)
	return render_template("logout.html")

@app.route('/Picture/<uuid:id>')
def bb_picture_get(id):
	path = f"{CONFIG['images']}/{id}.gif"
	if not os.path.isfile(path):
		return ("Image not found.", 404)
	return send_file(path, mimetype='image/gif')

if __name__ == '__main__':
	app.run(debug = False, port=5000)