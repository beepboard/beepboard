UPDATE users SET likes     = coalesce((SELECT SUM(likes)     FROM songs WHERE userid = users.userid), 0);
UPDATE users SET views     = coalesce((SELECT SUM(views)     FROM songs WHERE userid = users.userid), 0);
UPDATE users SET downloads = coalesce((SELECT SUM(downloads) FROM songs WHERE userid = users.userid), 0);
