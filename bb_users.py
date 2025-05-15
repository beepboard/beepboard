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
		
		# update user profile views
		db.execute("UPDATE users SET profileviews = profileviews + 1 WHERE userid = :id",
		           (id,)
		           )
		songs = db.execute("SELECT * FROM songs WHERE userid = ? ORDER BY likes DESC LIMIT 5",
		           (id,)
		           ).fetchall()
		songs = [bb_filter_song(db, song) for song in songs]
	
	if not user:
		return render_template("view_user.html", myself=myself, user=user), 404
	return render_template("view_user.html", myself=myself, user=user, songs=songs)

@app.route("/Profile/edit")
def bb_profile_edit():
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		trending = bb_get_trending(db)
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
	
	if not myself:
		return redirect("/Account/login")
	else:
		return render_template("profile_edit.html", myself=myself)