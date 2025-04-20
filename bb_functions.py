from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import json
from typing import *
from datetime import datetime
from enum import StrEnum
from bb_config import *
from bb_database import *

def bb_rowfactory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def bb_datetime(timestamp):
	return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
def bb_date(timestamp):
	return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

def bb_filter_user(user):
	if not user:
		return None
	return {
		'id':   user['userid'],
		'username': user['username'],
		
		'created_time':      user['timestamp'],
		'created_date':      bb_date(user['timestamp']),
		'created_datetime':  bb_datetime(user['timestamp']),
		
		'totalstats': {
			'views':  user['views'],
			'likes':  user['likes'],
			'clicks': user['downloads']
		},
		
		'flags': {
			'moderator': bool(user['ismod'])
		},
		
		'profile': {
			'views':     user['profileviews'],
			'followers': user['followers'],
			'pfp': user['pfp'],
			'bio': user['bio']
		}
	}

def bb_get_userdata_by_id(id):
	with sqlite3.connect(CONFIG['db']) as conn:
		conn.row_factory = bb_rowfactory
		db = conn.cursor()
		
		if not id:
			return None
		else:
			return db.execute(
					"SELECT * FROM users WHERE userid = ?", (str(id),)
				).fetchone()


def bb_get_userdata_by_token(token):
	with sqlite3.connect(CONFIG['db']) as conn:
		conn.row_factory = bb_rowfactory
		db = conn.cursor()
		
		if not token:
			return None
		else:
			return db.execute(
					"SELECT * FROM users WHERE token = ?", (token,)
				).fetchone()


def bb_search_users(sort, after):
	#stmt = StatementSelect(
	#	{ValueColumnName('*')},
	#	{ClauseFrom(ValueTableName('users')),
	#	 ClauseLimit(10)}
	#)
	
	clauses = {ClauseFrom(ValueTableName('users')),
			   ClauseLimit(10)}
	
	if sort == "popular":
		clauses.update([
			ClauseOrder({ValueColumnName('downloads'): OrderEnum.DESC,
			             ValueColumnName('likes'):     OrderEnum.DESC,
			             ValueColumnName('views'):     OrderEnum.DESC})
		])
	elif sort == "newest":
		clauses.update([
			ClauseOrder({ValueColumnName('timestamp'): OrderEnum.DESC})
		])
	else:
		return None
	
	with sqlite3.connect(CONFIG['db']) as conn:
		conn.row_factory = bb_rowfactory
		db = conn.cursor()
		q = db.execute(str(StatementSelect(
			{ValueColumnName('*')},
			clauses
		)))
		
		# return filtered result
		results = [bb_filter_user(user) for user in q.fetchall()]
		
		return results