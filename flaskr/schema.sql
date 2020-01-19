DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS organization;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL,
  organization_id INTEGER NOT NULL,
  is_admin BOOLEAN NOT NULL,
  FOREIGN KEY (organization_id) REFERENCES organization (id)
);

CREATE TABLE organization (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  name TEXT NOT NULL,
  organization_deck TEXT NOT NULL,
  organization_logo_url TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (id)
);