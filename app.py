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

@app.route('/')
def bb_index():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("index.html", myself=myself)
	
@app.route('/welcome')
def bb_welcome():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("welcome.html", myself=myself)

@app.route('/Songs')
def bb_list_songs():
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
	
	songs = bb_search_songs(sort, after, author, tags, query, limit)
	
	if not author:
		author = ''
	if not tags:
		tags = ''
	if not query:
		query = ''
		
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
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



@app.route('/Users')
def bb_list_users():
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
	
	users = bb_search_users(sort, after, query, limit)
	
	#filter users
	
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	
	return render_template("users.html",
		myself=myself,
		users=users,
		after=after,
		GET={'sort':sort,
		     'after':after,
		     'limit':limit,
		     'q':query}
	)

@app.route('/Jams')
@app.route('/Wiki')
def bb_under_construction():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("workinprogress.html", myself=myself)



@app.route('/Account/login')
def bb_account_login():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("login.html", myself=myself)
	
@app.route('/Account/register')
def bb_account_register():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("register.html", myself=myself)

@app.route('/Account/logout')
def bb_account_logout():
	return render_template("logout.html")

@app.route('/Picture/<uuid:id>')
def bb_picture_get(id):
	path = f"{CONFIG['images']}/{id}.png"
	if not os.path.isfile(path):
		return ("Image not found.", 404)
	return send_file(path, mimetype='image/gif')

if __name__ == '__main__':
	app.run(debug = False, port=5000)