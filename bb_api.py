from flask import *
import werkzeug
import sqlite3
import os
import binascii
import time
import json
from io import BytesIO
import uuid
from PIL import Image, ImageSequence

from bb_config   import *
from bb_database import *
from bb_functions import *

@app.route('/api/v1/Account/logout', methods=['POST'])
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
		res = redirect('/Account/logout')
		res.set_cookie('token', '', expires=0)
		return res

@app.route('/api/v1/Account/register', methods=['POST'])
def bb_api_register():
	# check if auth details are actually present
	if    not ('username' in request.form) \
	   or not ('password' in request.form):
		return (
			"Must include fields <code>username</code>, <code>password</code>",
			400
		)
		
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		# check if user already exists
		userdata = db.execute(
			"SELECT * FROM users WHERE username = ?",
			(request.form['username'],)
		).fetchone()
		
		# if there is no such username then return 403
		if userdata:
			return (f"{request.form['username']} already exists!", 400)
		
		hash = werkzeug.security.generate_password_hash(request.form['password'])
		
		# create the user
		db.execute("INSERT INTO users (username, password, timestamp) VALUES (?,?,?)",
		           (request.form['username'], hash, time.time()))
		
		# gen token
		token = binascii.hexlify(os.urandom(16)).decode()
		
		res = redirect('/welcome')
		
		# add token cookie
		res.set_cookie('token', token, 86400 * 30)
		
		# add token to DB
		db.execute("UPDATE users SET token = ? WHERE username = ?",
				   (token, request.form['username']))
		
		return res
	
@app.route('/api/v1/Account/login', methods=['POST'])
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
					<meta http-equiv='refresh' content='0; /Account/login'>
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
					<meta http-equiv='refresh' content='0; /Account/login'>
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
	or request.form["data"].startswith('http')  \
	or len(request.form["desc"]) > 1000:
		return (
			"Bad request. Click <a href='/Song/submit'>here</a> to return to the previous page.",
			400
		)
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		#check if user is logged in
		user = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
		if not user:
			return (
				"You're not authenticated.",
				400
			)
		
		# grab first free songid
		seq = db.execute("SELECT seq FROM sqlite_sequence WHERE name = 'songs'").fetchone()
			
		db.execute("INSERT INTO SONGS (userid, songdata, songmod, tags, name, description, timestamp) VALUES (?,?,?,?,?,?,?)",
		            (
		             user["id"],
		             request.form["data"],
		             request.form["mod"],
		             "," + request.form["tags"].strip(",") + ",",
		             request.form["title"],
		             request.form["desc"],
		             time.time()
		             ))
		
	# login user as well
	return redirect("/User/" + str(user['id']))

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

@app.route('/api/v1/Song/<int:songid>/comment', methods=['POST'])
def bb_api_postcomment(songid):
	if    not ('content' in request.form) \
	   or not ('parent' in request.form):
		return (
			"Bad parameters!",
			400
		)
	
	content  = request.form['content']
	parentid = request.form['parent']
	
	# validate content
	if len(content) < 1 or \
	   len(content) > 1024:
		return ("Invalid parameters!", 400)
	
	# check if song exists
	song = bb_filter_song(bb_get_songdata_by_id(songid))
	if not song:
		return ("Song doesn't exist!", 400)
	
	# check if parent actually exists
	if len(parentid) > 0: # exclude NULL parent
		parent = bb_filter_comment(bb_get_comment_by_id(parentid))
		if not parent:
			return ("No such parent comment!", 400)
	else:
		parentid = None
	
	# get poster
	token = request.cookies.get('token')
	if not token:
		return redirect('/Account/login')
	user = bb_filter_user(bb_get_userdata_by_token(token))
	if not user:
		return redirect('/Account/login')
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		db.execute('INSERT INTO comments (parent, songid, userid, content, timestamp) VALUES (?, ?,?,?,?)',
		           (parentid, songid, user["id"], content, time.time()))
	
	return redirect('/Song/' + str(song["id"]))

@app.route('/api/v1/Comment/<int:id>/delete', methods=['GET'])
def bb_api_deletecomment(id):
	# check if comment exists
	comment = bb_filter_comment(bb_get_comment_by_id(id), ['replies'])
	
	if not comment:
		return ("This comment doesn't exist.", 400)
	
	# check if comment belongs to user
	token = request.cookies.get('token')
	if not token:
		return redirect('/Account/login')
	user = bb_filter_user(bb_get_userdata_by_token(token))
	if not user:
		return redirect('/Account/login')
	
	if not user["id"] == comment["user"]:
		return ("You're not allowed to delete this comment!", 403)
	
	# delete comments
	with bb_connect_db() as conn:
		db = conn.cursor()
		db.execute("DELETE FROM comments WHERE commentid = ?", (comment['id'],))
		
		# delete the orphans
		db.execute("DELETE FROM comments WHERE parent = ?", (comment['id'],))
	
	return redirect("/Song/" + str(comment["song"]))

@app.route('/api/v1/User/<int:id>', methods=['GET'])
def bb_api_getuser(id):
	data = bb_get_userdata_by_id(id)
	if data:
		return bb_filter_user(data, request.args.to_dict().keys())
	else:
		return {'error': 'no such user'}, 404
	

@app.route('/api/v1/Song/<int:id>', methods=['GET'])
def bb_api_getsong(id):
	data = bb_get_songdata_by_id(id)
	if data:
		return bb_filter_song(data, request.args.to_dict().keys())
	else:
		return {'error': 'no such song'}, 404
	
@app.route('/api/v1/Comment/<int:id>', methods=['GET'])
def bb_api_getcomment(id):
	comment = bb_get_comment_by_id(id)
	if comment:
		return bb_filter_comment(comment, request.args.to_dict().keys())
	else:
		return {'error': 'no such comment'}, 404

@app.route('/api/v1/Profile/edit', methods=['POST'])
def bb_api_editprofile():
	print(request.form.to_dict(), request.files)
	print(request.content_type)
	
	if not request.content_type.startswith('multipart/form-data'):
		return ("invalid content type", 400)
	
	# check if user is authenticated
	token = request.cookies.get('token')
	if not token:
		return redirect('/Account/login')
	user = bb_filter_user(bb_get_userdata_by_token(token))
	if not user:
		return redirect('/Account/login')
	
	bio     = request.form['bio']
	country = request.form['country']
	handle  = request.form['discordhandle']
	pfp     = request.files['pfp']
	
	# validate data
	if len(bio     if bio     else '') > 1024 or \
	   len(country if country else '') > 2    or \
	   len(handle  if handle  else '') > 32:
		return ("Invalid parameters!", 400)
	
	if pfp:
		# the profile picture requires a bit of special logic,
		# because we need to store both the file itself separately
		# and a reference to the file in the database
		print("FILE TYPE", request.files['pfp'].content_type)
		if not (request.files['pfp'].content_type == 'image/png' or
		        request.files['pfp'].content_type == 'image/gif'):
			return ("Invalid image format!", 400)
		
		# load image in pillow
		img = Image.open(request.files['pfp'])
		w, h = img.size
		size = min(w, h)
		fmt = img.format
		
		frames = []
		
		# crop image to square
		# (using ImageSequence both for PNGs and GIFs to make the code simpler)
		for frame in ImageSequence.Iterator(img):
			frame = frame.crop((w / 2 - size / 2,
			                    h / 2 - size / 2,
			                    w / 2 + size / 2,
			                    h / 2 + size / 2)
			                  )
			frame = frame.copy()
			frame = frame.resize((128, 128), Image.NEAREST)
			frames.append(frame)
		
		# save image
		pfpid = str(uuid.uuid4())
		frames[0].save(
			f"{CONFIG['images']}/{pfpid}.png",
			save_all = True,
			append_images = frames[1:],
			format = "GIF",
			**img.info
		)
	
	# update data
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		# we must set each field, one by one,
		# since the request could have partial arguments
		if bio:
			db.execute("UPDATE users SET bio = ?           WHERE userid = ?",
			 (bio, user['id']))
		
		if country:
			db.execute("UPDATE users SET country = ?       WHERE userid = ?",
			 (country, user['id']))
		
		if handle:
			db.execute("UPDATE users SET discordhandle = ? WHERE userid = ?",
			 (handle, user['id']))
		
		if pfp:
			db.execute("UPDATE users SET pfp           = ? WHERE userid = ?",
			 (pfpid, user['id']))
		
	
	return redirect('/User/' + str(user['id']))