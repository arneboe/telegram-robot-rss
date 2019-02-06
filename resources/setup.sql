CREATE TABLE feed (
	url varchar PRIMARY KEY NOT NULL UNIQUE,
	last_updated timestamp
);

CREATE TABLE `user` (
	telegram_id	integer NOT NULL UNIQUE,
	muted integer NOT NULL DEFAULT 0,
	PRIMARY KEY(telegram_id)
);

CREATE TABLE filter (
    filter_id integer NOT NULL UNIQUE,
    regexp varchar NOT NULL,
    telegram_id integer NOT NULL,
    url varchar NOT NULL,
    FOREIGN KEY(url) REFERENCES feed(url),
    FOREIGN KEY(telegram_id) REFERENCES user(telegram_id),
    PRIMARY KEY(filter_id)
);
