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
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	user = bb_filter_user(bb_get_userdata_by_id(id))
	# update user profile views
	with bb_connect_db() as conn:
		db = conn.cursor()
		db.execute("UPDATE users SET profileviews = profileviews + 1 WHERE userid = :id",
		           (id,)
		           )
		songs = db.execute("SELECT * FROM songs WHERE userid = ? ORDER BY likes DESC LIMIT 5",
		           (id,)
		           ).fetchall()
		songs = [bb_filter_song(song) for song in songs]
		print(songs)
	if not user:
		return render_template("view_user.html", myself=myself, user=user), 404
	return render_template("view_user.html", myself=myself, user=user, songs=songs)