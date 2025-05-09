from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import markdown
import json
from typing import *
from datetime import datetime
from enum import StrEnum
from bb_config import *
from bb_database import *
from html_sanitizer import Sanitizer
import re

MODS = {
	"abyssbox":    {'url': 'https://choptop84.github.io/abyssbox-app/'},
	"beepbox":     {'url': 'https://www.beepbox.co'},
	"goldbox":     {'url': 'https://aurysystem.github.io/goldbox/'},
	"jummbox":     {'url': 'https://jummb.us'},
	"modbox":      {'url': 'https://moddedbeepbox.github.io/3.0/'},
	"pandorasbox": {'url': 'https://paandorasbox.github.io/'},
	"sandbox":     {'url': 'https://fillygroove.github.io/sandbox-3.1/'},
	"slarmoosbox": {'url': 'https://slarmoo.github.io/slarmoosbox/website/'},
	"ultrabox":    {'url': 'https://ultraabox.github.io/'},
	"wackybox":    {'url': 'https://bluecatgamer.github.io/Wackybox/'}
}

def bb_sql_regexp(pattern, item):
    return re.search(pattern, item) is not None

def bb_connect_db():
	conn = sqlite3.connect(CONFIG['db'])
	conn.row_factory = bb_rowfactory
	conn.create_function("REGEXP", 2, bb_sql_regexp)
	return conn

def bb_rowfactory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def bb_datetime(timestamp):
	return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
def bb_date(timestamp):
	return datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

def bb_render_markdown(s):
	return markdown.markdown(s)

def bb_filter_comment(comment, detail = []):
	sanitizer = Sanitizer()
	
	if not comment:
		return None
	
	return {
		'id': comment['commentid'],
		
		'song': bb_filter_song(
					bb_get_songdata_by_id(comment['songid']),
					['author']
				) if 'song' in detail else comment['songid'],
		
		'user': bb_filter_user(
					bb_get_userdata_by_id(comment['userid']),
					[]
				) if 'user' in detail else comment['userid'],
		
		'created': {
			'time':      comment['timestamp'],
			'date':      bb_date(comment['timestamp']),
			'datetime':  bb_datetime(comment['timestamp']),
		},
		
		'content': {
			'raw':  comment['content'],
			'html': sanitizer.sanitize(bb_render_markdown(comment['content'])),
		},
		
		'replies': [bb_filter_comment(comment) for comment in
						bb_get_comments_by_parent(comment['commentid'])]
						if 'replies' in detail else None
						
		
		# 'likes': comment['likes']
	}

def bb_filter_comments(comments, parent = None, detail = []):
	sanitizer = Sanitizer()
	result = []
	
	if not comments:
		return []
	
	for comment in [comment for comment in comments if comment["parent"] == parent]:
		result.append({
			'id': comment['commentid'],
			
			'song': bb_filter_song(
						bb_get_songdata_by_id(comment['songid']),
						['author']
					) if 'song' in detail else comment['songid'],
			
			'user': bb_filter_user(
						bb_get_userdata_by_id(comment['userid']),
						[]
					) if 'user' in detail else comment['userid'],
			
			'created': {
				'time':      comment['timestamp'],
				'date':      bb_date(comment['timestamp']),
				'datetime':  bb_datetime(comment['timestamp']),
			},
			
			'content': {
				'raw':  comment['content'],
				'html': sanitizer.sanitize(bb_render_markdown(comment['content'])),
			},
			
			'replies': bb_filter_comments(comments, comment['commentid'], detail)
			# 'likes': comment['likes']
		})
	return result

def bb_get_comments_by_parent(parent):
	with bb_connect_db() as conn:
		db = conn.cursor()
		q = db.execute("SELECT * FROM comments WHERE parent = ?", (parent,))
		comments = q.fetchall()
		if not comments:
			comments = []
		return comments
		
def bb_get_comment_by_id(id):
	with bb_connect_db() as conn:
		db = conn.cursor()
		q = db.execute("SELECT * FROM comments WHERE commentid = ?", (id,))
		comment = q.fetchone()
		if not comment:
			comment = None
		return comment
		
def bb_get_comments_by_songid(song):
	with bb_connect_db() as conn:
		db = conn.cursor()
		q = db.execute("SELECT * FROM comments WHERE songid = ?", (song,))
		comments = q.fetchall()
		if not comments:
			comments = []
		return comments

def bb_filter_user(user, detail = []):
	# detail: list ("songs")
	sanitizer = Sanitizer()
	
	if not user:
		return None
	return {
		'id':   user['userid'],
		'username': user['username'],
		
		'created': {
			'time':      user['timestamp'],
			'date':      bb_date(user['timestamp']),
			'datetime':  bb_datetime(user['timestamp']),
		},
		
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
			'pfp':       {
				'id': user['pfp'],
				'url': '/Picture/' + user['pfp']
			},
			
			'bio': {
				'raw': user['bio'],
				'html': sanitizer.sanitize(bb_render_markdown(user['bio']))
			},
			
			'country': user['country'],
			'discordhandle': user['discordhandle']
		},
		
		'songs': bb_search_songs("newest", author = user['username'], filter = []) if "songs" in detail else None
	}

def bb_filter_song(song, detail = []):
	# detail: list ("author")
	sanitizer = Sanitizer('')
	
	if not song:
		return None
	return {
		'id':   song['songid'],
		'author': bb_filter_user(bb_get_userdata_by_id(song['userid'])) if "author" in detail else song['userid'],
		
		'stats': {
			'clicks': song['downloads'],
			'likes': song['likes'],
			'views': song['views']
		},
		
		'flags': {
			'deleted':  bool(song['deleted']),
			'featured': bool(song['featured'])
		},
		
		'content': {
			'name': song['name'],
			'tags': song['tags'],
			
			'desc': {
				'raw':  song['description'],
				'html': (bb_render_markdown(song['description']))
			},
			
			'url': {
				'url': MODS[song['songmod']]['url'] + "#" + song['songdata'],
				'data': song['songdata'],
				'mod': song['songmod']
			}
		},
		
		'created': {
			'time':      song['timestamp'],
			'date':      bb_date(song['timestamp']),
			'datetime':  bb_datetime(song['timestamp']),
		},
		
		'comments': bb_filter_comments(
						bb_get_comments_by_songid(song['songid']),
						detail = ['user']
					) if "comments" in detail else None
	}

def bb_get_userdata_by_id(id):
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		if not id:
			return None
		else:
			return db.execute(
					"SELECT * FROM users WHERE userid = ?", (str(id),)
				).fetchone()
				
def bb_get_songdata_by_id(id):
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		if not id:
			print("no id")
			return None
		else:
			songdata = db.execute("SELECT * FROM songs WHERE songid = ?", (str(id),)).fetchone()
			return songdata


def bb_get_userdata_by_token(token):
	with bb_connect_db() as conn:
		db = conn.cursor()
		
		if not token:
			return None
		else:
			return db.execute(
					"SELECT * FROM users WHERE token = ?", (token,)
				).fetchone()


def bb_search_songs(sort, after = 0, author = None, tags = None, query = None, limit = 3, filter = ["author"]):
	#stmt = StatementSelect(
	#	{ValueColumnName('*')},
	#	{ClauseFrom(ValueTableName('users')),
	#	 ClauseLimit(10)}
	#)
	
	clauses = {ClauseFrom(ValueTableName('songs', 'S')),
	           ClauseJoin(ValueTableName('users', 'U'),
	           	ConditionEQ(ValueColumnName('userid', 'S'),
	           	            ValueColumnName('userid', 'U'))
	           	      ),
	           ClauseOffset(after)
			   }
	if limit > 0:
		clauses.add(ClauseLimit(limit))
	
	params = {}
	
	if author:
		params['author'] = author
		clauses.update([
			ClauseWhere(ConditionEQ(
				Function('LOWER', ValueColumnName('username', 'U')),
				Function('LOWER', ':author')
			))
		])
	
	if tags:
		params['tags_exp'] = f"%,{tags},%"
		clauses.update([
			ClauseWhere(ConditionLIKE(
				Function('LOWER', ValueColumnName('tags', 'S')),
				Function('LOWER', ':tags_exp')
			))
		])
	
	if query:
		params['query_exp'] = f"%{query}%"
		clauses.update([
			ClauseWhere(ConditionLIKE(
				Function('LOWER', ValueColumnName('name', 'S')),
				Function('LOWER', ':query_exp')
			))
		])
	
	if sort == "popular":
		clauses.update([
			ClauseOrder({ValueColumnName('downloads', 'S'): OrderEnum.DESC,
			             ValueColumnName('likes', 'S'):     OrderEnum.DESC,
			             ValueColumnName('views', 'S'):     OrderEnum.DESC})
		])
	elif sort == "newest":
		clauses.update([
			ClauseOrder({ValueColumnName('timestamp', 'S'): OrderEnum.DESC})
		])
	else:
		return None
	
	song_statement = str(StatementSelect(
		{ValueColumnName('*', 'S')},
		 clauses
	))
	
	user_statement = str(StatementSelect(
		{ValueColumnName('*', 'U')},
		 clauses
	))
	
	with bb_connect_db() as conn:
		db = conn.cursor()
		songs   = db.execute(song_statement, params).fetchall()
		authors = db.execute(user_statement, params).fetchall()
		
		songs = [(song | {'author': bb_filter_user(author)})
					for song, author in zip(songs, authors)]
		
		results = [bb_filter_song(song, filter) for song in songs]
	
	return results
		
def bb_search_users(sort, after, query, limit):
	#stmt = StatementSelect(
	#	{ValueColumnName('*')},
	#	{ClauseFrom(ValueTableName('users')),
	#	 ClauseLimit(10)}
	#)
	
	clauses = {ClauseFrom(ValueTableName('users')),
	           ClauseOffset(after)}
	if limit > 0:
		clauses.add(ClauseLimit(limit))
	
	params = {}
	
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
	
	if query:
		params['query_exp'] = f"%{query}%"
		clauses.update([
			ClauseWhere(ConditionLIKE(
				Function('LOWER', ValueColumnName('username')),
				Function('LOWER', ':query_exp')
			))
		])
		
	with bb_connect_db() as conn:
		db = conn.cursor()
		q = db.execute(str(StatementSelect(
			{ValueColumnName('*')},
			clauses
		)), params)
		
		# return filtered result
		results = [bb_filter_user(user) for user in q.fetchall()]
		return results

def bb_get_interaction(type, userid, songid):
	with bb_connect_db() as conn:
		db = conn.cursor()
		q = db.execute("SELECT interactionid FROM interactions WHERE type = ? AND userid = ? AND songid = ?",
						(type, userid, songid))
		return q.fetchone()