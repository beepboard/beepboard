from flask import *
import werkzeug
import sqlite3
import os
import binascii
import json

from bb_config   import *
from bb_database import *
from bb_functions import *

@app.route('/Wiki/<page>')
def bb_wiki_page(page):
	myself = bb_filter_user(bb_get_userdata_by_token(request.cookies.get('token')))
	return render_template("viewwiki.html", myself=myself, page=page), 404