CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT UNIQUE NOT NULL, 
    hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    patient_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    hospital TEXT NOT NULL,
    diagnosis TEXT,
    medication TEXT,
    FOREIGN KEY (patient_id) REFERENCES users(id)
);