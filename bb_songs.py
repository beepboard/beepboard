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
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id), ['author', 'comments'])
		if myself and song:
			has_interacted = bb_get_interaction(db, "like", myself["id"], song['id'])
		else:
			has_interacted = None
		
		db.execute("UPDATE songs SET views = views + 1 WHERE songid = :id",
		           (id,)
		           )
		db.execute("UPDATE users SET views = views + 1 WHERE userid = :id",
		           (song['author']['id'],)
		           )
	
	
	if not song:
		return render_template("view_song.html",  myself=myself, song=song), 404
	return render_template("view_song.html",  myself=myself, song=song, has_interacted = has_interacted)

@app.route('/Song/<int:id>/edit')
def bb_song_edit(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id))
	
	if not song:
		return "No such song.", 404
	if not myself:
		return redirect('/Account/login')
	if not (myself['id'] == song['author']):
		return "You cannot edit this song!", 403
	
	return render_template("song_edit.html",  myself=myself, song=song)

@app.route('/Song/submit')
def bb_song_submit():

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		if not myself:
			return redirect("/Account/login")
		return render_template("submit_song.html",  myself=myself)


@app.route('/Song/<int:id>/play')
def bb_song_play(id):
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id))
		print(song['author'])
		db.execute("UPDATE songs SET downloads = downloads + 1 WHERE songid = :id", (id,))
		db.execute("UPDATE users SET downloads = downloads + 1 WHERE userid = :id", (song['author'],))
	if song:
		url = song['content']['url']['url']
		if len(url) > CONFIG['redirect_threshold']:
			APOS = "'"
			return f"Redirecting, just a moment... <meta http-equiv=refresh content='0; {url.replace(APOS, '&apos;')}'>"
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

		db.execute("UPDATE users SET likes = likes + 1 WHERE userid = :id",
		           (song['author'],)
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

		db.execute("UPDATE users SET likes = likes - 1 WHERE userid = :id",
		           (song['author'],)
		           )

		db.execute("DELETE FROM interactions WHERE type = ? AND userid = ? AND songid = ?",
		           ("like", myself['id'], song["id"])
		           )
	return redirect(f"/Song/{song['id']}")

@app.route('/Song/<int:id>/playlistadd')
def bb_song_playlistadd(id):

	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		if not myself:
			return redirect('/Account/login')
		
		song = bb_filter_song(db, bb_get_songdata_by_id(db, id))
		if not song:
			return "Song not found", 404
		
		playlists = [bb_filter_playlist(db, p)
		             for p in bb_get_playlists_by_userid(db, myself['id'])]
		if not playlists:
			return redirect('/Playlist/new')
		
	return render_template("playlist_add.html",
	                       myself=myself,
	                       
	                       song=song,
	                       playlists=playlists)

@app.route('/Songs')
def bb_songs_list_redirect():
	return redirect('/Song/list', 301)

@app.route('/Song/list')
def bb_songs_list():
	# set default values for parameters
	sort   = request.args.get('sort')
	after  = request.args.get('after')
	author = request.args.get('author')
	tags   = request.args.get('tags')
	query  = request.args.get('q')
	limit  = request.args.get('limit')
	if not sort:
		sort = 'newest'
	
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
		songs = bb_search_songs(db, sort, after, author, tags, query, limit)
		
		if not author:
			author = ''
		if not tags:
			tags = ''
		if not query:
			query = ''
		
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
	
	return render_template("songs.html",
		myself=myself,
		songs=songs,
		GET={'sort':sort,
		     'after':after,
		     'author':author,
		     'tags':tags,
		     'limit':limit,
		     'q':query},
	)
