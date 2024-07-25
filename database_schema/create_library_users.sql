use library;

DROP USER IF EXISTS 'library-read-only';
DROP USER IF EXISTS 'library-read-write';

CREATE USER 'library-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'library-read-write' IDENTIFIED BY 'def456!!';

GRANT SELECT, SHOW VIEW ON library.* 
      TO 'library-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON library.* 
      TO 'library-read-write';
      
FLUSH PRIVILEGES;