CREATE DATABASE library;

DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS authors;

CREATE TABLE books
(
    bookid            int not null AUTO_INCREMENT,	  
    title             varchar(256) not null,
    volumeid		  varchar(256) not null,
    genre             varchar(256),
    pagecount         int,
    summary           TEXT,
    avg_review	      DECIMAL(3,2),
    num_reviews       int,
    pgsread		      int,
    predremaining	  varchar(256),
    ranking	          int,
    client_review     TEXT,
    PRIMARY KEY (bookid)
    
);
