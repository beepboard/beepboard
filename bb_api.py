from flask import *
import werkzeug
import sqlite3
import os
import binascii
import json

from bb_config   import *
from bb_database import *
from bb_functions import *

@app.route('/api/v1/Account/login', methods=['POST'])
def bb_api_login():
	# check if auth details are actually present
	if    not ('username' in request.form) \
	   or not ('password' in request.form):
		return (
			"Must include fields <code>username</code>, <code>password</code>",
			400
		)
		
	with sqlite3.connect(CONFIG['db']) as conn:
		conn.row_factory = bb_rowfactory
		db = conn.cursor()
		
		# get password hash
		userdata = db.execute(
			"SELECT password from users WHERE username = ?",
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

@app.route('/api/v1/User/<int:id>', methods=['GET'])
def bb_api_getuser(id):
	data = bb_get_userdata_by_id(id)
	if data:
		return bb_filter_user(data)
	else:
		return {'error': 'no such userid'}, 404
	