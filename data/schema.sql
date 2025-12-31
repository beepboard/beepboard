PRAGMA foreign_keys=OFF;

CREATE TABLE IF NOT EXISTS "songs" (
	"songid"	INTEGER,
	"userid"	INTEGER NOT NULL,
	"views"	INTEGER NOT NULL DEFAULT 0,
	"likes"	INTEGER NOT NULL DEFAULT 0,
	"downloads"	INTEGER NOT NULL DEFAULT 0,
	"deleted"	INTEGER NOT NULL DEFAULT 0,
	"featured"	INTEGER NOT NULL DEFAULT 0,
	"songdata"	TEXT NOT NULL,
	"songmod"	TEXT NOT NULL,
	"tags"	TEXT NOT NULL,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"timestamp"	INTEGER NOT NULL, songtype TEXT NOT NULL DEFAULT 'original', remixof  INT,
	PRIMARY KEY("songid" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "interactions" (
	"interactionid"	INTEGER,
	"userid"	INTEGER NOT NULL,
	"songid"	INTEGER NOT NULL,
	"type"	TEXT NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	PRIMARY KEY("interactionid" AUTOINCREMENT),
	FOREIGN KEY("songid") REFERENCES "songs"
);

CREATE TABLE IF NOT EXISTS "comments" (
	"commentid"	INTEGER,
	"userid"	INTEGER NOT NULL,
	"songid"	INTEGER NOT NULL,
	"content"	TEXT NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	"parent"	INTEGER,
	PRIMARY KEY("commentid" AUTOINCREMENT),
	FOREIGN KEY("songid") REFERENCES "songs"
);

CREATE TABLE IF NOT EXISTS "playlist_songs" (
	"playlistid"	INTEGER,
	"songid"	INTEGER,
	"timestamp"	INT NOT NULL DEFAULT 0,
	FOREIGN KEY("songid") REFERENCES "songs"
);

CREATE TABLE IF NOT EXISTS "playlists" (
	"playlistid"	INTEGER,
	"userid"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"timestamp"	INT NOT NULL,
	PRIMARY KEY("playlistid" AUTOINCREMENT),
	FOREIGN KEY("userid") REFERENCES "users"
);

CREATE TABLE IF NOT EXISTS "users" (
	"userid"	INTEGER,
	"followers"	INTEGER NOT NULL DEFAULT 0,
	"views"	INTEGER NOT NULL DEFAULT 0,
	"likes"	INTEGER NOT NULL DEFAULT 0,
	"downloads"	INTEGER NOT NULL DEFAULT 0,
	"profileviews"	INTEGER NOT NULL DEFAULT 0,
	"rank"	INTEGER NOT NULL DEFAULT 0,
	"bio"	TEXT NOT NULL DEFAULT '',
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	"token"	TEXT,
	"timestamp"	INTEGER NOT NULL,
	"country"	TEXT NOT NULL DEFAULT '',
	"discordhandle"	TEXT,
	"pfp"	TEXT NOT NULL DEFAULT 'ae3728e6-3a0a-41ce-99fa-3b6650518de7',
	"isveteran"	INT NOT NULL DEFAULT 0,
	"lastlogin"	INT,
	PRIMARY KEY("userid" AUTOINCREMENT)
);
