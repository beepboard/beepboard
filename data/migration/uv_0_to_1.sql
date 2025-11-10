-- TAG LIST (for searching)
UPDATE db_version SET v = 1;

CREATE TABLE tag_list (tag UNIQUE, frequency);
