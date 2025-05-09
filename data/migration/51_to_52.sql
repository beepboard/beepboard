UPDATE users SET pfp = 'ae3728e6-3a0a-41ce-99fa-3b6650518de7'
           WHERE pfp = '/assets/default-pfp.png';

ALTER TABLE users ADD country TEXT NOT NULL DEFAULT '';
ALTER TABLE users ADD discordhandle TEXT;

ALTER TABLE users RENAME COLUMN pfp TO pfp_old;
ALTER TABLE users ADD    COLUMN pfp
	TEXT NOT NULL DEFAULT 'ae3728e6-3a0a-41ce-99fa-3b6650518de7';

UPDATE users SET pfp = pfp_old;