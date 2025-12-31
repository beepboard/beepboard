from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
from io import BytesIO
import json

from bb_config    import *
from bb_database  import *
from bb_api       import *
from bb_users     import *
from bb_songs     import *
from bb_wiki      import *
from bb_functions import *
from bb_errors    import *

STATIC_ROUTE_TEMPLATES = {
	'/welcome':          'welcome.html',
	'/settings':         'settings.html',
	'/Jams':             'workinprogress.html',
	'/Wiki':             'workinprogress.html',
	'/Playlist/new':     'playlist_new.html',
	'/Account/login':    'login.html',
	'/Account/logout':   'logout.html',
	'/Account/register': 'register.html',
	'/Admin':            'admin/index.html',
}

@app.route('/')
def bb_index():
	with bb_connect_db() as conn:
		db = conn.cursor()
		trending = bb_get_trending(db)
		return render_template("index.html", **bb_get_route_vars(db), trending = trending)

@app.route('/welcome')
@app.route('/settings')
@app.route('/Jams')
@app.route('/Wiki')
@app.route('/Playlist/new')
@app.route('/Account/login')
@app.route('/Account/register')
@app.route('/Account/logout')
@app.route('/Admin')
def bbr_static():
	with bb_connect_db() as conn:
		db = conn.cursor()
		return render_template(STATIC_ROUTE_TEMPLATES[request.path], **bb_get_route_vars(db))

@app.route('/Admin/Stats')
def bb_stats_get():
	with bb_connect_db() as conn:
		db = conn.cursor()
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))

		if not myself or ('admin' not in myself['badges']):
			return (render_template('admin/nope.html', **bb_get_route_vars(db)), 403)
		
		no_users = db.execute('SELECT COUNT(*) as c FROM users;').fetchone()['c']
		no_songs = db.execute('SELECT COUNT(*) as c FROM songs;').fetchone()['c']
		stats = {'no_users': no_users, 'no_songs': no_songs}

		return render_template('admin/stats.html', **bb_get_route_vars(db), **stats)

@app.route('/Picture/<uuid:id>')
def bb_picture_get(id):
	path = f"{CONFIG['images']}/{id}.gif"
	if not os.path.isfile(path):
		return ("Image not found.", 404)
	return send_file(path, mimetype='image/gif')

@app.route('/Playlist/<int:id>')
def bb_playlist_view(id):
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		after = request.args.get('after')
		if not after:
			after = 0
		playlist = bb_filter_playlist(db, bb_get_playlist_by_id(db, id),
		                              {'limit': 5, 'after': after, 'songs': 1, 'author': 1}
		                              )
		
		myself = bb_filter_user(db, bb_get_userdata_by_token(db, request.cookies.get('token')))
		return render_template("playlist_view.html", 
							**bb_get_route_vars(db), playlist=playlist, after=after)


if __name__ == '__main__':
	app.run(debug = False, port=5000)
