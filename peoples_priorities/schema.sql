PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS grievances (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id       TEXT NOT NULL UNIQUE,
    citizen_name    TEXT,
    citizen_phone   TEXT,
    raw_text        TEXT NOT NULL,
    language        TEXT NOT NULL DEFAULT 'en',
    category        TEXT NOT NULL DEFAULT 'other',
    summary         TEXT,
    urgency_score   INTEGER NOT NULL DEFAULT 0,
    urgency_level   TEXT NOT NULL DEFAULT 'low',
    urgency_reasons TEXT,
    status          TEXT NOT NULL DEFAULT 'submitted',
    ward            TEXT NOT NULL,
    latitude        REAL,
    longitude       REAL,
    cluster_id      TEXT,
    affected_count  INTEGER NOT NULL DEFAULT 1,
    safety_risk     INTEGER NOT NULL DEFAULT 0,
    photo_path      TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS status_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    grievance_id    INTEGER NOT NULL REFERENCES grievances(id) ON DELETE CASCADE,
    status          TEXT NOT NULL,
    note            TEXT,
    changed_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE INDEX IF NOT EXISTS idx_grievances_ward     ON grievances(ward);
CREATE INDEX IF NOT EXISTS idx_grievances_category ON grievances(category);
CREATE INDEX IF NOT EXISTS idx_grievances_status   ON grievances(status);
CREATE INDEX IF NOT EXISTS idx_grievances_cluster  ON grievances(cluster_id);
CREATE INDEX IF NOT EXISTS idx_grievances_urgency  ON grievances(urgency_score DESC);
CREATE INDEX IF NOT EXISTS idx_status_history_grievance ON status_history(grievance_id);
