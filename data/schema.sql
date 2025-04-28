PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS users (
	userid      INTEGER PRIMARY KEY AUTOINCREMENT,
	
	followers    INTEGER NOT NULL DEFAULT 0,
	views        INTEGER NOT NULL DEFAULT 0,
	likes        INTEGER NOT NULL DEFAULT 0,
	downloads    INTEGER NOT NULL DEFAULT 0,
	profileviews INTEGER NOT NULL DEFAULT 0,
	
	ismod        INTEGER NOT NULL DEFAULT 0,
	
	bio         TEXT NOT NULL DEFAULT '',
	username    TEXT NOT NULL,
	password    TEXT NOT NULL,
	token       TEXT,
	
	pfp         TEXT NOT NULL DEFAULT '/assets/default-pfp.png',
	
	timestamp   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS songs (
	songid      INTEGER PRIMARY KEY AUTOINCREMENT,
	userid      INTEGER NOT NULL,
	
	views       INTEGER NOT NULL DEFAULT 0,
	likes       INTEGER NOT NULL DEFAULT 0,
	downloads   INTEGER NOT NULL DEFAULT 0,
	deleted     INTEGER NOT NULL DEFAULT 0,
	featured    INTEGER NOT NULL DEFAULT 0,
	
	songdata    TEXT NOT NULL,
	songmod     TEXT NOT NULL,
	tags        TEXT NOT NULL,
	name        TEXT NOT NULL,
	description TEXT NOT NULL,
	
	timestamp   INTEGER NOT NULL,
	
	FOREIGN KEY (userid) REFERENCES users
);

CREATE TABLE IF NOT EXISTS comments (
	commentid INTEGER PRIMARY KEY AUTOINCREMENT,
	
	userid    INTEGER NOT NULL,
	songid    INTEGER NOT NULL,
	content   TEXT    NOT NULL,
	
	timestamp INTEGER NOT NULL,
	
	FOREIGN KEY (userid) REFERENCES users,
	FOREIGN KEY (songid) REFERENCES songs
);

CREATE TABLE IF NOT EXISTS interactions (
	interactionid INTEGER PRIMARY KEY AUTOINCREMENT,
	
	userid        INTEGER NOT NULL,
	songid        INTEGER NOT NULL,
	type          TEXT    NOT NULL,
	
	timestamp     INTEGER NOT NULL,
	
	FOREIGN KEY (userid) REFERENCES users,
	FOREIGN KEY (songid) REFERENCES songs
);

COMMIT;