from flask import Flask, render_template, redirect, request, jsonify, make_response
import sqlite3
import json

def bb_validate_config(config):
	if not ('db' in config):
		raise Exception("invalid config ('db' missing)")
	return config

app = Flask(__name__, static_url_path='',
                      static_folder='public',
                      template_folder='templates')

with open('config.json') as fp:
	CONFIG = json.load(fp)
	CONFIG = bb_validate_config(CONFIG)