-- 1. convert tags to lowercase
UPDATE songs
	SET tags = lower(tags);

-- 2. add leading comma
UPDATE songs
	SET tags = ',' || tags
	WHERE NOT (tags LIKE ',%')
	AND NOT (tags = '');

-- 3. add trailing comma
UPDATE songs
	SET tags = tags || ','
	WHERE NOT (tags LIKE '%,')
	AND NOT (tags = '');

-- 4. add parent to comment
ALTER TABLE comments ADD parent INTEGER;