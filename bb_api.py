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
import bcrypt

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
					<meta http-equiv='refresh' content='1; /Account/login'>
					<p>User <code>{request.form['username']}</code> doesn't exist.</p>
					""", 403)
		
		# verify password hash
		# bcrypt
		
		if userdata['password'].startswith('$2'):
			password_valid = bcrypt.checkpw(
				request.form['password'].encode('utf-8'),
				userdata['password'].encode('utf-8')
			)
		else:
			password_valid = werkzeug.security.check_password_hash(
				userdata['password'],
				request.form['password']
			)
		
		if password_valid:
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
					<meta http-equiv='refresh' content='1; /Account/login'>
					<p>Wrong password.</p>
					""", 403)

@app.route('/api/v1/Song/<int:songid>/edit', methods=['POST'])
def bb_api_songedit(songid):
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		song = bb_filter_song(db, bb_get_songdata_by_id(db, songid))
		if not song:
			return "No such song", 400
		
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		if not myself:
			return redirect('/Account/login')
		
		# check if song belongs to user
		if not (song['author'] == myself['id']):
			return "You may not edit another user's song.", 403
		
		# do some data validation
		songname = None
		songdesc = None
		songmod  = None
		songdata = None
		if 'title' in request.form:
			songname = request.form['title']
			if len(songname) > 100 or \
			   len(songname) < 3:
				return "Invalid song name length", 400
		
		if 'desc' in request.form:
			songdesc = request.form['desc']
			if len(songdesc) > 1000:
				return "Invalid song description length", 400
		
		if 'mod' in request.form:
			songmod = request.form['mod']
			if not (songmod in MODS):
				return "Invalid song mod", 400
		
		if 'data' in request.form:
			songdata = request.form['data']
		
		# actually update the values in the db
		if songname:
			db.execute("UPDATE songs SET name = ?        WHERE songid = ?", (songname, songid))
		if songdesc:
			db.execute("UPDATE songs SET description = ? WHERE songid = ?", (songdesc, songid))
		if songmod:
			db.execute("UPDATE songs SET songmod = ?     WHERE songid = ?", (songmod, songid))
		if songdata:
			db.execute("UPDATE songs SET songdata = ?    WHERE songid = ?", (songdata, songid))
	
	return redirect("/Song/" + str(songid))

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
	if request.form["data"].startswith('http') \
	or len(request.form["title"]) > 100 \
	or len(request.form["title"]) < 3  \
	or request.form["mod"] not in MODS \
	or len(request.form["desc"]) > 1000:
		return (
			"Bad request. You're not supposed to see this - if you do, there's a bug. Report it to @fmixolydian",
			400
		)
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		#check if user is logged in
		user = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
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
	limit  = request.args.get('limit')
	author = request.args.get('author')
	tags   = request.args.get('tags')
	query  = request.args.get('q')
	
	if not sort:
		sort = 'newest'
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
	
	if not limit:
		limit = "10"
	limit = int(limit)
	if limit > 100 or limit < 1:
		return "invalid limit", 400
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		songs = bb_search_songs(db, sort, after, author, tags, query, limit)
	
	if songs:
		return songs
	else:
		return []

@app.route('/api/v1/User/search', methods=['GET'])
def bb_api_searchusers():
	# set default values for parameters
	sort  = request.args.get('sort')
	after = request.args.get('after')
	limit = request.args.get('limit')
	query  = request.args.get('q')
	if not sort:
		sort = 'popular'
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
	
	if not limit:
		limit = "10"
	limit = int(limit)
	if limit > 100 or limit < 1:
		return "invalid limit", 400
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		users = bb_search_users(db, sort, after, query, limit)
	
	if users:
		return users
	else:
		return []

@app.route('/api/v1/Song/<int:songid>/delete')
def bb_api_songdelete(songid):
	token = request.cookies.get('token')
	if not token:
		return redirect('/Account/login')
	
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, token))
		if not myself:
			return redirect('/Account/login')
		
		songdata = bb_filter_song(db, bb_get_songdata_by_id(db, songid))
		if not songdata:
			return "No such song!", 400
		
		if not (songdata['author'] == myself['id']):
			return "You cannot delete another user's song.", 403
		
		# delete the song
		db.execute("DELETE FROM songs WHERE songid = ?", (songid,))
		
		# delete all comments
		db.execute("DELETE FROM comments WHERE songid = ?", (songid,))
		
		# delete all interactions
		db.execute("DELETE FROM interactions WHERE songid = ?", (songid,))
		
		return redirect('/User/' + str(myself["id"]))

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
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		# check if song exists
		song = bb_filter_song(db, bb_get_songdata_by_id(db, songid))
		if not song:
			return ("Song doesn't exist!", 400)
		
		# check if parent actually exists
		if len(parentid) > 0: # exclude NULL parent
			parent = bb_filter_comment(db, bb_get_comment_by_id(db, parentid))
			if not parent:
				return ("No such parent comment!", 400)
		else:
			parentid = None
		
		# get poster
		token = request.cookies.get('token')
		if not token:
			return redirect('/Account/login')
		
		user = bb_filter_user(db, bb_get_userdata_by_token(db, token))
		if not user:
			return redirect('/Account/login')
		
		db.execute('INSERT INTO comments (parent, songid, userid, content, timestamp) VALUES (?, ?,?,?,?)',
		           (parentid, songid, user["id"], content, time.time()))
	
	return redirect('/Song/' + str(song["id"]))

@app.route('/api/v1/Comment/<int:id>/delete', methods=['GET'])
def bb_api_deletecomment(id):
	# check if comment exists
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		comment = bb_filter_comment(db, bb_get_comment_by_id(db, id), ['replies'])
		
		if not comment:
			return ("This comment doesn't exist.", 400)
		
		# check if comment belongs to user
		token = request.cookies.get('token')
		if not token:
			return redirect('/Account/login')
		user = bb_filter_user(db, bb_get_userdata_by_token(db, token))
		if not user:
			return redirect('/Account/login')
		
		if not user["id"] == comment["user"]:
			return ("You're not allowed to delete this comment!", 403)
		
		db.execute("DELETE FROM comments WHERE commentid = ?", (comment['id'],))
		
		# delete the orphans
		db.execute("DELETE FROM comments WHERE parent = ?", (comment['id'],))
	
	return redirect("/Song/" + str(comment["song"]))

@app.route('/api/v1/User/<int:id>', methods=['GET'])
def bb_api_getuser(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		data = bb_get_userdata_by_id(db, id)
		if data:
			return bb_filter_user(db, data, request.args.to_dict().keys())
		else:
			return {'error': 'no such user'}, 404
	

@app.route('/api/v1/Song/<int:id>', methods=['GET'])
def bb_api_getsong(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		data = bb_get_songdata_by_id(db, id)
		if data:
			return bb_filter_song(db, data, request.args.to_dict().keys())
		else:
			return {'error': 'no such song'}, 404
	
@app.route('/api/v1/Comment/<int:id>', methods=['GET'])
def bb_api_getcomment(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		comment = bb_get_comment_by_id(db, id)
		if comment:
			return bb_filter_comment(db, comment, request.args.to_dict().keys())
		else:
			return {'error': 'no such comment'}, 404

@app.route('/api/v1/Profile/edit', methods=['POST'])
def bb_api_editprofile():
	if not request.content_type.startswith('multipart/form-data'):
		return ("invalid content type", 400)
	
	# check if user is authenticated
	token = request.cookies.get('token')
	if not token:
		return redirect('/Account/login')
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		user = bb_filter_user(db, bb_get_userdata_by_token(db, token))
		if not user:
			return redirect('/Account/login')
		
		name    = request.form.get('username')
		bio     = request.form.get('bio')
		country = request.form.get('country')
		handle  = request.form.get('discordhandle')
		pfp     = request.files.get('pfp')
		
		# validate data
		if len(bio     if bio     else '') > 1024 or \
		   len(country if country else '') > 2    or \
		   len(handle  if handle  else '') > 32   or \
		   len(name    if name    else '') > 32:
			return ("Invalid parameters!", 400)
		
		if pfp:
			# the profile picture requires a bit of special logic,
			# because we need to store both the file itself separately
			# and a reference to the file in the database
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
				f"{CONFIG['images']}/{pfpid}.gif",
				save_all = True,
				append_images = frames[1:],
				format = "GIF",
				**img.info
			)
		
		# we must set each field, one by one,
		# since the request could have partial arguments
		if name:
			db.execute("UPDATE users SET username = ?      WHERE userid = ?",
			 (name, user['id']))
		
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