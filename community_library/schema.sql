CREATE TABLE IF NOT EXISTS folders (
 id TEXT PRIMARY KEY, title TEXT NOT NULL, creator TEXT NOT NULL, description TEXT NOT NULL,
 item_count INTEGER NOT NULL, oversized_count INTEGER NOT NULL, digest TEXT NOT NULL,
 owner_hash TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','withdrawn')),
 created_at TEXT NOT NULL, reviewed_at TEXT, review_note TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS folders_status_date ON folders(status,created_at,id);
CREATE TABLE IF NOT EXISTS folder_chunks (
 folder_id TEXT NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
 sequence INTEGER NOT NULL, content TEXT NOT NULL, PRIMARY KEY(folder_id,sequence)
);
CREATE TABLE IF NOT EXISTS team (
 user_id TEXT PRIMARY KEY, role TEXT NOT NULL CHECK(role IN ('reviewer','editor','admin','owner'))
);
CREATE TABLE IF NOT EXISTS audit (
 id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL,
 details TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mutation_guard (id TEXT PRIMARY KEY, passed INTEGER NOT NULL CHECK(passed=1));
