from flask import *
import werkzeug
import sqlite3
import os
import binascii
import json

from bb_config   import *
from bb_database import *
from bb_functions import *

@app.route('/User/<int:id>')
def bb_user_view(id):
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
		user = bb_filter_user(db, bb_get_userdata_by_id(db, id))
		after = request.args.get('after')
		if not after:
			after = 0
		
		# update user profile views
		db.execute("UPDATE users SET profileviews = profileviews + 1 WHERE userid = :id",
		           (id,)
		           )
		songs = db.execute("SELECT * FROM songs WHERE userid = ? ORDER BY timestamp DESC LIMIT 5 OFFSET ?",
		           (id, after)
		           ).fetchall()
		songs = [bb_filter_song(db, song) for song in songs]
		playlists = [bb_filter_playlist(db, p, {'songs': 1, 'after': 0, 'limit': 500})
		             for p in bb_get_playlists_by_userid(db, user['id'])]

	if not user:
		return render_template("view_user.html", trending=trending, myself=myself, user=user), 404
	return render_template("view_user.html",
				trending=trending,
				myself=myself,
				user=user,
				songs=songs,
				playlists=playlists,
				after=after
				)

@app.route("/Profile/edit")
def bb_profile_edit():
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		trending = bb_get_trending(db)
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
	
	if not myself:
		return redirect("/Account/login")
	else:
		return render_template("profile_edit.html", trending=trending, myself=myself)

@app.route('/Users')
def bb_users_list_redirect():
	return redirect('/User/list', 301)

@app.route('/User/list')
def bb_user_list():
	# set default values for parameters
	sort  = request.args.get('sort')
	after = request.args.get('after')
	query = request.args.get('q')
	limit  = request.args.get('limit')
	if not sort:
		sort = 'popular'
	
	if not limit:
		limit = "10"
	limit = int(limit)
	if limit > 100 or limit < 1:
		return "invalid limit", 400
	
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		users = bb_search_users(db, sort, after, query, limit)
		
		#filter users
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
	
	return render_template("users.html",
		myself=myself,
		trending=trending,
		users=users,
		after=after,
		GET={'sort':sort,
		     'after':after,
		     'limit':limit,
		     'q':query}
	)