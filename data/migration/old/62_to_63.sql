CREATE TABLE playlists (
	playlistid	INTEGER PRIMARY KEY AUTOINCREMENT,
	userid	INTEGER NOT NULL,
	name	TEXT NOT NULL,
	timestamp INT NOT NULL,
	FOREIGN KEY(userid) REFERENCES users
);

CREATE TABLE playlist_songs (
	playlistid	INTEGER,
	songid	INTEGER,
	FOREIGN KEY(songid) REFERENCES "songs",
	FOREIGN KEY(playlistid) REFERENCES "playlists"
);

ALTER TABLE users RENAME COLUMN ismod TO rank;
UPDATE users SET rank = 3 WHERE rank = 1;