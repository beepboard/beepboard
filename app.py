from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import json

from bb_config    import *
from bb_database  import *
from bb_api       import *
from bb_users     import *
from bb_songs     import *
from bb_functions import *

@app.route('/')
def bb_index():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("index.html", myself=myself)

@app.route('/Songs')
def bb_list_songs():
	# set default values for parameters
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
		     'q':query},
	)



@app.route('/Users')
def bb_list_users():
	# set default values for parameters
	sort  = request.args.get('sort')
	after = request.args.get('after')
	query = request.args.get('q')
	if not sort:
		sort = 'popular'
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
	
	users = bb_search_users(sort, after, query)
	
	#filter users
	
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	
	return render_template("users.html",
		myself=myself,
		users=users,
		after=after,
		GET={'sort':sort,
		     'after':after,
		     'q':query}
	)

@app.route('/Jams')
@app.route('/Wiki')
def bb_under_construction():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("workinprogress.html", myself=myself)



@app.route('/Account/Login')
def bb_account_login():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("login.html", myself=myself)
	
@app.route('/Account/Register')
def bb_account_register():
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("register.html", myself=myself)

@app.route('/Account/Logout')
def bb_account_logout():
	return render_template("logout.html")