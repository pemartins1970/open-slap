-- Description: Telegram links and link codes

CREATE TABLE IF NOT EXISTS telegram_link_codes (
  code TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  used_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_user
  ON telegram_link_codes(user_id);

CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_expires
  ON telegram_link_codes(expires_at);

CREATE TABLE IF NOT EXISTS telegram_links (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  telegram_user_id TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  revoked_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS idx_telegram_links_user
  ON telegram_links(user_id);

CREATE INDEX IF NOT EXISTS idx_telegram_links_pair
  ON telegram_links(telegram_user_id, chat_id);

-- DOWN
DROP TABLE IF EXISTS telegram_links;
DROP TABLE IF EXISTS telegram_link_codes;
