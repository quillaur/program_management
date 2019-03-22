CREATE DATABASE program_management;

CREATE TABLE IF NOT EXISTS Brother (
	IdBrother INT UNSIGNED AUTO_INCREMENT,
	BrotherFirstName VARCHAR(20),
	BrotherLastName VARCHAR(20),
	PRIMARY KEY (IdBrother)
);

CREATE TABLE IF NOT EXISTS Action(
	IdAction TINYINT UNSIGNED AUTO_INCREMENT,
	ActionName VARCHAR(20),
	PRIMARY KEY (IdAction)
);

CREATE TABLE IF NOT EXISTS BrotherAction(
	IdBrotherAction INT UNSIGNED AUTO_INCREMENT,
	IdBrother INT UNSIGNED,
	ActionDate DATE,
	IdAction TINYINT UNSIGNED,
	foreign key (IdBrother) references Brother (IdBrother),
	foreign key (IdAction) references Action (IdAction)
);