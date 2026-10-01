ALTER TABLE folders ADD COLUMN media_revision INTEGER NOT NULL DEFAULT 0;
CREATE TABLE IF NOT EXISTS item_images (
 id TEXT PRIMARY KEY, folder_id TEXT NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
 serial_hash TEXT NOT NULL, content_hash TEXT NOT NULL, content BLOB NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(folder_id,serial_hash)
);
