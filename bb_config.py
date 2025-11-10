from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import json
import os
import logging
from flask_uuid import FlaskUUID

def bb_validate_config(config):
	if not ('db' in config):
		raise Exception("invalid config ('db' missing)")

	if not ('images' in config):
		raise Exception("invalid config ('images' missing)")
	
	if not ('redirect_threshold' in config):
		config['redirect_threshold'] = 4096
	
	if not ('debug_build' in config):
		config['debug_build'] = False

	return config

def fromjson(data, *args):
	print(args)
	return json.loads(data) if type(data) is str else {}

with open('config.json') as fp:
	CONFIG = json.load(fp)
	CONFIG = bb_validate_config(CONFIG)
	if 'error_log' in CONFIG:
		logging.basicConfig(filename = CONFIG['error_log'], level=logging.DEBUG)

app = Flask(__name__, static_url_path='',
                      static_folder='public',
                      template_folder='templates')

app.add_template_filter(fromjson, "fromjson")
flask_uuid = FlaskUUID()
flask_uuid.init_app(app)
