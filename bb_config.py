from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import json
import os
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

def bb_validate_config(config):
	if not ('db' in config):
		raise Exception("invalid config ('db' missing)")
	return config

with open('config.json') as fp:
	CONFIG = json.load(fp)
	CONFIG = bb_validate_config(CONFIG)
	if 'error_log' in CONFIG:
		logging.basicConfig(filename = CONFIG['error_log'], level=logging.DEBUG)

app = Flask(__name__, static_url_path='',
                      static_folder='public',
                      template_folder='templates')
