from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import json

from bb_config    import *
from bb_database  import *
from bb_api       import *
from bb_users     import *
from bb_functions import *

@app.route('/')
def bb_index():
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	return render_template("index.html", userdata=userdata)



@app.route('/Songs')
def bb_list_songs():
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	return render_template("songs.html", userdata=userdata)



@app.route('/Users')
def bb_list_users():
	# set default values for parameters
	sort  = request.args.get('sort')
	after = request.args.get('after')
	if not sort:
		sort = 'popular'
	if not after:
		after = '0'
	if not after.isdigit():
		after = '0'
	
	users = bb_search_users(sort, after)
	
	#filter users
	
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	
	return render_template("users.html", userdata=userdata,
	                                     users=users,
	                                     sort=sort,
	                                     after=after)
	
	
	
@app.route('/Jams')
def bb_list_jams():
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	return render_template("jams.html", userdata=userdata)
	
	
	
@app.route('/Roadmap')
def bb_roadmap():
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	return render_template("roadmap.html", userdata=userdata)



@app.route('/Account/Login')
def bb_account_login():
	userdata = bb_get_userdata_by_token(request.cookies.get('token'))
	return render_template("login.html", userdata=userdata)