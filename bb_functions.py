from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import markdown
import json
from typing import *
from datetime import datetime
from enum import Enum
from bb_config import *
from bb_database import *
from html_sanitizer import Sanitizer
import html_sanitizer
import re

MODS = {
	"abyssbox":     {'url': 'https://choptop84.github.io/abyssbox-app/'},
	"beepbox":      {'url': 'https://www.beepbox.co'},
	"cardboardbox": {'url': 'https://hidden-realm.github.io/cardboardbox/'},
	"goldbox":      {'url': 'https://aurysystem.github.io/goldbox/'},
	"jummbox":      {'url': 'https://jummb.us'},
	"lemmbox":      {'url': 'https://lemmbox.github.io/'},
	"modbox":       {'url': 'https://moddedbeepbox.github.io/3.0/'},
	"pandorasbox":  {'url': 'https://paandorasbox.github.io/'},
	"sandbox":      {'url': 'https://fillygroove.github.io/sandbox-3.1/'},
	"slarmoosbox":  {'url': 'https://slarmoo.github.io/slarmoosbox/website/'},
	"ultrabox":     {'url': 'https://ultraabox.github.io/'},
	"wackybox":     {'url': 'https://bluecatgamer.github.io/Wackybox/'},
}

SONGTYPES = ["original", 'remix', 'cover']

def bb_flags(f):
	return sorted([
		n for n in f.keys() if f[n]
	])

def bb_connect_db():
	conn = sqlite3.connect(CONFIG['db'])
	conn.row_factory = bb_rowfactory
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

def bb_filter_comment(db, comment, detail = []):
	sanitizer = Sanitizer()
	
	if not comment:
		return None
	
	return {
		'id': comment['commentid'],
		
		'song': bb_filter_song(
		            db,
					bb_get_songdata_by_id(db, comment['songid']),
					['author']
				) if 'song' in detail else comment['songid'],
		
		'user': bb_filter_user(
		            db,
					bb_get_userdata_by_id(db, comment['userid']),
					[]
				) if 'user' in detail else comment['userid'],
		
		'created': bb_format_time(comment['timestamp']),
		'content': bb_filter_text(comment['content']),
		
		'replies': [bb_filter_comment(db, comment) for comment in
						bb_get_comments_by_parent(db, comment['commentid'])]
						if 'replies' in detail else None
						
		
		# 'likes': comment['likes']
	}

def bb_filter_comments(db, comments, parent = None, detail = []):
	sanitizer = Sanitizer()
	result = []
	
	if not comments:
		return []
	
	for comment in [comment for comment in comments if comment["parent"] == parent]:
		result.append({
			'id': comment['commentid'],
			
			'song': bb_filter_song(
			            db,
						bb_get_songdata_by_id(db, comment['songid']),
						['author']
					) if 'song' in detail else comment['songid'],
			
			'user': bb_filter_user(
			            db,
						bb_get_userdata_by_id(db, comment['userid']),
						[]
					) if 'user' in detail else comment['userid'],
			
			'created': bb_format_time(comment['timestamp']),
			'content': bb_filter_text(comment['content']),
			
			'replies': bb_filter_comments(db, comments, comment['commentid'], detail)
			# 'likes': comment['likes']
		})
	return result

def bb_get_comments_by_parent(db, parent):
	q = db.execute("SELECT * FROM comments WHERE parent = ?", (parent,))
	comments = q.fetchall()
	if not comments:
		comments = []
	return comments
		
def bb_get_comment_by_id(db, id):
	q = db.execute("SELECT * FROM comments WHERE commentid = ?", (id,))
	comment = q.fetchone()
	if not comment:
		comment = None
	return comment
		
def bb_get_comments_by_songid(db, song):
	q = db.execute("SELECT * FROM comments WHERE songid = ?", (song,))
	comments = q.fetchall()
	if not comments:
		comments = []
	return comments

def bb_filter_text(text):
	sanitizer = Sanitizer()
	
	if not text:
		return None
	
	return {
		'raw': text,
		'html': sanitizer.sanitize(bb_render_markdown(text)),
		'sanitized': sanitizer.sanitize(text),
		'preview': text.split('\r\n')[0]
	}

def bb_format_time(timestamp):
	if not timestamp:
		return None
	
	return {
		'time':      timestamp,
		'date':      bb_date(timestamp),
		'datetime':  bb_datetime(timestamp)
	}

def bb_filter_user(db, user, detail = []):
	# detail: list ("songs")
	
	if not user:
		return None
	return {
		'id':   user['userid'],
		'username': user['username'],
		
		'created': bb_format_time(user['timestamp']),
		
		'totalstats': {
			'views':  user['views'],
			'likes':  user['likes'],
			'clicks': user['downloads']
		},
		
		'badges': bb_flags({
			'moderator': user['ismod'],
			'veteran':   user['isveteran']
		}),
		
		'profile': {
			'views':     user['profileviews'],
			'followers': user['followers'],
			'pfp':       {
				'id': user['pfp'],
				'url': '/Picture/' + user['pfp']
			},
			
			'bio': bb_filter_text(user['bio']),
			
			'country': user['country'],
			'discordhandle': user['discordhandle']
		},
		
		'songs': bb_search_songs(db, "newest", author = user['username'], filter = []) if "songs" in detail else None
	}

def bb_filter_song(db, song, detail = []):
	# detail: list ("author")
	sanitizer = Sanitizer('')
	
	if not song:
		return None
	
	return {
		'id':   song['songid'],
		'author': bb_filter_user(db, bb_get_userdata_by_id(db, song['userid'])) if "author" in detail else song['userid'],
		'base':   bb_filter_song(db, bb_get_songdata_by_id(db, song['remixof'])) if 'remix' in detail else song['remixof'],
		'type': song['songtype'],
		
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
			
			'desc': bb_filter_text(song['description']),
			
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
						db,
						bb_get_comments_by_songid(db, song['songid']),
						detail = ['user']
					) if "comments" in detail else None
	}

def bb_get_userdata_by_id(db, id):
	if not id:
		return None
	else:
		return db.execute(
				"SELECT * FROM users WHERE userid = ?", (str(id),)
			).fetchone()
				
def bb_get_songdata_by_id(db, id):
	if not id:
		print("no id")
		return None
	else:
		songdata = db.execute("SELECT * FROM songs WHERE songid = ?", (str(id),)).fetchone()
		return songdata


def bb_get_userdata_by_token(db, token):
	if not token:
		return None
	else:
		return db.execute(
				"SELECT * FROM users WHERE token = ?", (token,)
			).fetchone()


def bb_search_songs(db, sort, after = 0, author = None, tags = None, query = None, limit = 3, filter = ["author"]):
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
	elif sort == "trending":
		clauses.update([
			ClauseOrder({'date(S.timestamp, "unixepoch")': OrderEnum.DESC,
			             ValueColumnName('likes', 'S'):     OrderEnum.DESC,
			             ValueColumnName('downloads', 'S'): OrderEnum.DESC,
			             ValueColumnName('views', 'S'):     OrderEnum.DESC})
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
	
	print(song_statement, user_statement)
	
	songs   = db.execute(song_statement, params).fetchall()
	authors = db.execute(user_statement, params).fetchall()
	
	songs = [({**song, 'author': bb_filter_user(db, author)})
				for song, author in zip(songs, authors)]
	
	results = [bb_filter_song(db, song, filter) for song in songs]
	
	return results
		
def bb_search_users(db, sort, after, query, limit):
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
			ClauseOrder({ValueColumnName('likes'):     OrderEnum.DESC,
			             ValueColumnName('downloads'): OrderEnum.DESC,
			             ValueColumnName('views'):     OrderEnum.DESC})
		])
	elif sort == "newest":
		clauses.update([
			ClauseOrder({ValueColumnName('timestamp'): OrderEnum.DESC})
		])
	else:
		return None
	
	if query:
		params['query_exp'] = f"%{query}%"
		clauses.update([
			ClauseWhere(ConditionLIKE(
				Function('LOWER', ValueColumnName('username')),
				Function('LOWER', ':query_exp')
			))
		])
	
	q = db.execute(str(StatementSelect(
		{ValueColumnName('*')},
		clauses
	)), params)
	
	# return filtered result
	results = [bb_filter_user(db, user) for user in q.fetchall()]
	return results

def bb_get_interaction(db, type, userid, songid):
	q = db.execute("SELECT interactionid FROM interactions WHERE type = ? AND userid = ? AND songid = ?",
					(type, userid, songid))
	return q.fetchone()

def bb_get_trending(db):
	# get 3 most trending songs
	return bb_search_songs(db, 'trending', 0, None, None, None, 5)