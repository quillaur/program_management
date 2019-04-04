CREATE DATABASE program_management;

CREATE TABLE IF NOT EXISTS Brother (
	IdBrother INT UNSIGNED AUTO_INCREMENT,
	BrotherFirstName VARCHAR(20),
	BrotherLastName VARCHAR(20),
	Micro ENUM("0", "1") NOT NULL DEFAULT "0",
	Stage ENUM("0", "1") NOT NULL DEFAULT "0",
	Sono ENUM("0", "1") NOT NULL DEFAULT "0",
	PRIMARY KEY (IdBrother)
);

CREATE TABLE IF NOT EXISTS Action(
	IdAction TINYINT UNSIGNED AUTO_INCREMENT,
	ActionName VARCHAR(20),
	PRIMARY KEY (IdAction)
);

CREATE TABLE IF NOT EXISTS BrotherAction(
	IdBrotherAction INT UNSIGNED AUTO_INCREMENT,
	IdBrother INT UNSIGNED NOT NULL,
	ActionDate DATE NOT NULL,
	IdAction TINYINT UNSIGNED NOT NULL,
	foreign key (IdBrother) references Brother (IdBrother),
	foreign key (IdAction) references Action (IdAction),
	PRIMARY KEY (IdBrotherAction)
);

CREATE TABLE IF NOT EXISTS ActionCount(
    IdActionCount INT UNSIGNED AUTO_INCREMENT,
	IdBrother INT UNSIGNED NOT NULL,
	IdAction TINYINT UNSIGNED NOT NULL,
	CountBrotherAction INT UNSIGNED NOT NULL DEFAULT 0,
	foreign key (IdBrother) references Brother (IdBrother),
	foreign key (IdAction) references Action (IdAction),
	PRIMARY KEY (IdActionCount)
);