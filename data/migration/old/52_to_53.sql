ALTER TABLE users ADD isveteran INT NOT NULL DEFAULT 0;
ALTER TABLE users ADD lastlogin INT;

UPDATE sqlite_sequence SET seq = (SELECT MAX(songid) + 1 FROM songs)       where name = 'songs';
UPDATE sqlite_sequence SET seq = (SELECT MAX(userid) + 1 FROM users)       where name = 'users';
UPDATE sqlite_sequence SET seq = (SELECT MAX(commentid) + 1 FROM comments) where name = 'comments';