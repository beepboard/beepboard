from flask import *
import werkzeug
import sqlite3
import os
import binascii
import time
import json

from bb_config   import *
from bb_database import *
from bb_functions import *

@app.route('/api/v1/Account/Logout', methods=['POST'])
def bb_api_logout():
	# check if auth details are actually present
	if not request.cookies.get('token'):
		return (
			"You're not logged in, <strong>BOZO</strong>",
			400
		)
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		# remove cookie from db
		db.execute("UPDATE users SET token = NULL WHERE token = ?",
		           (request.cookies.get('token'),)
		           )
		
		# remove cookie from client
		res = redirect('/Account/Logout')
		res.set_cookie('token', '', expires=0)
		return res

@app.route('/api/v1/Account/Login', methods=['POST'])
def bb_api_login():
	# check if auth details are actually present
	if    not ('username' in request.form) \
	   or not ('password' in request.form):
		return (
			"Must include fields <code>username</code>, <code>password</code>",
			400
		)
		
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		# get password hash
		userdata = db.execute(
			"SELECT password FROM users WHERE username = ?",
			(request.form['username'],)
		).fetchone()
		
		# if there is no such username then return 403
		if userdata == None:
			return (f"""
					<meta http-equiv='refresh' content='0; /Account/Login'>
					<p>User <code>{request.form['username']}</code> doesn't exist.</p>
					""", 403)
		
		# verify password hash
		if werkzeug.security.check_password_hash(userdata['password'], request.form['password']):
			res = redirect('/')
			
			# correct password; generate a token
			token = binascii.hexlify(os.urandom(16)).decode()
			
			# add token cookie
			res.set_cookie('token', token, 86400 * 30)
			
			# add token to DB
			db.execute("UPDATE users SET token = ? WHERE username = ?",
						(token, request.form['username']))
			
			return res
		else:
			return ("""
					<meta http-equiv='refresh' content='0; /Account/Login'>
					<p>Wrong password.</p>
					""", 403)

@app.route('/api/v1/Song/submit', methods=['POST'])
def bb_api_songsubmit():
	if    not ('title' in request.form) \
	   or not ('desc' in request.form) \
	   or not ('mod' in request.form) \
	   or not ('data' in request.form) \
	   or not ('tags' in request.form):
		return (
			"Bad parameters!",
			400
		)
	# vaildate params
	if len(request.form["title"]) > 100 \
	or len(request.form["title"]) < 3   \
	or request.form["mod"] not in MODS  \
	or len(request.form["desc"]) > 1000:
		return (
			"Bad request.",
			400
		)
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		#check if user is logged in
		user = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
		if not user:
			return (
				"Bad request.",
				400
			)
		songid = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'songs'").fetchone()['seq']
		db.execute("INSERT INTO SONGS (userid, songdata, songmod, tags, name, description, timestamp) VALUES (?,?,?,?,?,?,?)",
		            (
		             user["id"],
		             request.form["data"],
		             request.form["mod"],
		             request.form["tags"].strip(","),
		             request.form["title"],
		             request.form["desc"],
		             time.time()
		             ))
	return redirect("/Song/" + str(songid))

@app.route('/api/v1/Song/search', methods=['GET'])
def bb_api_searchsongs():
	sort   = request.args.get('sort')
	after  = request.args.get('after')
	author = request.args.get('author')
	tags   = request.args.get('tags')
	query  = request.args.get('q')
	if not sort:
		sort = 'newest'
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
		
	songs = bb_search_songs(sort, after, author, tags, query)
	if songs:
		return songs
	else:
		return []

@app.route('/api/v1/User/search', methods=['GET'])
def bb_api_searchusers():
	# set default values for parameters
	sort  = request.args.get('sort')
	after = request.args.get('after')
	query  = request.args.get('q')
	if not sort:
		sort = 'popular'
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
	
	users = bb_search_users(sort, after, query)
	
	if users:
		return users
	else:
		return []

@app.route('/api/v1/User/<int:id>', methods=['GET'])
def bb_api_getuser(id):
	data = bb_get_userdata_by_id(id)
	if data:
		return bb_filter_user(data)
	else:
		return {'error': 'no such user'}, 404
	

@app.route('/api/v1/Song/<int:id>', methods=['GET'])
def bb_api_getsong(id):
	data = bb_get_songdata_by_id(id)
	if data:
		return bb_filter_song(data)
	else:
		return {'error': 'no such song'}, 404
	