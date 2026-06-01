-- Description: Adiciona tabelas para o Motor de Notas e FTS.

CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_id INTEGER,
    title TEXT NOT NULL,
    content_md TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

CREATE VIRTUAL TABLE notes_fts USING fts5(
    title,
    content_md,
    tags,
    note_id UNINDEXED
);

CREATE TRIGGER IF NOT EXISTS notes_fts_ai
AFTER INSERT ON notes
BEGIN
  INSERT INTO notes_fts(title, content_md, tags, note_id)
  VALUES (new.title, new.content_md, new.tags, new.id);
END;

CREATE TRIGGER IF NOT EXISTS notes_fts_ad
AFTER DELETE ON notes
BEGIN
  DELETE FROM notes_fts WHERE note_id = old.id;
END;

CREATE TRIGGER IF NOT EXISTS notes_fts_au
AFTER UPDATE OF title, content_md, tags ON notes
BEGIN
  UPDATE notes_fts
  SET title = new.title,
      content_md = new.content_md,
      tags = new.tags
  WHERE note_id = new.id;
END;

-- DOWN
DROP TRIGGER IF EXISTS notes_fts_ai;
DROP TRIGGER IF EXISTS notes_fts_ad;
DROP TRIGGER IF EXISTS notes_fts_au;
DROP TABLE IF EXISTS notes;
DROP TABLE IF EXISTS notes_fts;
