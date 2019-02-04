BEGIN;
CREATE TABLE templates (
    id INTEGER PRIMARY KEY NOT NULL UNIQUE,
    name text UNIQUE NOT NULL,
    path text NOT NULL UNIQUE,
    checksum text NOT NULL,
    active integer NOT NULL DEFAULT 1
);

CREATE TABLE instances (
    id INTEGER PRIMARY KEY NOT NULL UNIQUE,
    path text NOT NULL UNIQUE,
    template_id int NOT NULL,
    active integer NOT NULL DEFAULT 1,
    FOREIGN KEY(template_id) REFERENCES templates
);
COMMIT;
