from flask import *
import werkzeug
import sqlite3
import os
import time
import binascii
import json

from bb_config   import *
from bb_database import *
from bb_functions import *

@app.route('/Song/<int:id>')
def bb_song_view(id):
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	song = bb_filter_song(bb_get_songdata_by_id(id))
	if userdata and song:
		has_interacted = bb_get_interaction("like", userdata["userid"], song['id'])
	else:
		has_interacted = None
	
	# update song views
	with sqlite3.connect(CONFIG['db']) as conn:
		db = conn.cursor()
		db.execute("UPDATE songs SET views = views + 1 WHERE songid = :id",
		           (id,)
		           )
	if not song:
		return render_template("view_song.html", userdata=userdata, song=song), 404
	return render_template("view_song.html", userdata=userdata, song=song, has_interacted = has_interacted)



@app.route('/Song/<int:id>/play')
def bb_song_play(id):
	song = bb_filter_song(bb_get_songdata_by_id(id))
	# update song views
	with sqlite3.connect(CONFIG['db']) as conn:
		db = conn.cursor()
		db.execute("UPDATE songs SET downloads = downloads + 1 WHERE songid = :id",
		           (id,)
		           )
	if song:
		return redirect(song['content']['url']['url']);
	else:
		return "Song not found.", 404


@app.route('/Song/<int:id>/upvote')
def bb_song_upvote(id):
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	if not userdata:
		return redirect('/Account/Login')
	
	song = bb_filter_song(bb_get_songdata_by_id(id))
	if not song:
		return "Song not found", 404
	
	if bb_get_interaction("like", userdata['userid'], song['id']):
		return "You already liked this song.", 400
	
	# update song views
	with sqlite3.connect(CONFIG['db']) as conn:
		db = conn.cursor()
		db.execute("UPDATE songs SET likes = likes + 1 WHERE songid = :id",
		           (id,)
		           )
		db.execute("INSERT INTO interactions (type, songid, userid, timestamp) VALUES (?,?,?,?)",
		           ("like", song["id"], userdata['userid'], time.time())
		           )
	return redirect(f"/Song/{song['id']}")


@app.route('/Song/<int:id>/downvote')
def bb_song_downvote(id):
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	if not userdata:
		return redirect('/Account/Login')
	
	song = bb_filter_song(bb_get_songdata_by_id(id))
	if not song:
		return "Song not found", 404
	
	if not bb_get_interaction("like", userdata['userid'], song['id']):
		return "You did not already like this song.", 400
	
	# update song views
	with sqlite3.connect(CONFIG['db']) as conn:
		db = conn.cursor()
		db.execute("UPDATE songs SET likes = likes - 1 WHERE songid = :id",
		           (id,)
		           )
		db.execute("DELETE FROM interactions WHERE type = ? AND userid = ? AND songid = ?",
		           ("like", userdata['userid'], song["id"])
		           )
	return redirect(f"/Song/{song['id']}")