INSERT OR IGNORE INTO tag_list WITH RECURSIVE Splitter AS (
    SELECT
        SUBSTR(tags, 1, INSTR(tags, ',') - 1) AS tag,
        SUBSTR(tags, INSTR(tags, ',') + 1) AS remainder
    FROM
        songs
    UNION ALL
    SELECT
        SUBSTR(remainder, 1, INSTR(remainder, ',') - 1) AS tag,
        SUBSTR(remainder, INSTR(remainder, ',') + 1) AS remainder
    FROM
        Splitter
    WHERE
        remainder != ''
)

SELECT DISTINCT tag, (SELECT COUNT(*) FROM Splitter WHERE tag = o.tag) as frequency FROM Splitter o WHERE tag != '';
