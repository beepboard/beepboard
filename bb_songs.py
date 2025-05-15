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

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id), ['author', 'comments'])
		if myself and song:
			has_interacted = bb_get_interaction(db, "like", myself["id"], song['id'])
		else:
			has_interacted = None
		
		db.execute("UPDATE songs SET views = views + 1 WHERE songid = :id",
		           (id,)
		           )
	
	if not song:
		return render_template("view_song.html", myself=myself, song=song), 404
	return render_template("view_song.html", myself=myself, song=song, has_interacted = has_interacted)

@app.route('/Song/submit')
def bb_song_submit():

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		trending = bb_get_trending(db)
		if not myself:
			return redirect("/Account/login")
		return render_template("submit_song.html", myself=myself)


@app.route('/Song/<int:id>/play')
def bb_song_play(id):
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id))
		db.execute("UPDATE songs SET downloads = downloads + 1 WHERE songid = :id",
		           (id,)
		           )
	if song:
		url = song['content']['url']['url']
		if len(url) > CONFIG['redirect_threshold']:
			return f"Redirecting, just a moment... <meta http-equiv=refresh content='0; {url}'>"
		else:
			return redirect(song['content']['url']['url']);
	else:
		return "Song not found.", 404


@app.route('/Song/<int:id>/upvote')
def bb_song_upvote(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		if not myself:
			return redirect('/Account/login')
		
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id))
		if not song:
			return "Song not found", 404
		
		if bb_get_interaction(db, "like", myself['id'], song['id']):
			return "You already liked this song.", 400
		
		db.execute("UPDATE songs SET likes = likes + 1 WHERE songid = :id",
		           (id,)
		           )
		
		db.execute("INSERT INTO interactions (type, songid, userid, timestamp) VALUES (?,?,?,?)",
		           ("like", song["id"], myself['id'], time.time())
		           )
		
		return redirect(f"/Song/{song['id']}")


@app.route('/Song/<int:id>/downvote')
def bb_song_downvote(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		if not myself:
			return redirect('/Account/login')
		
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id))
		if not song:
			return "Song not found", 404
		
		if not bb_get_interaction(db, "like", myself['id'], song['id']):
			return "You did not already like this song.", 400
	
		# update song views
		db.execute("UPDATE songs SET likes = likes - 1 WHERE songid = :id",
		           (id,)
		           )
		db.execute("DELETE FROM interactions WHERE type = ? AND userid = ? AND songid = ?",
		           ("like", myself['id'], song["id"])
		           )
	return redirect(f"/Song/{song['id']}")