-- Migration: 001
-- Description: Schema inicial (users, conversations, messages, friction_events)
-- Author: sistema
-- Date: 2026-03-13
-- Reversible: yes (ver rollback abaixo)

-- UP
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  hashed_password TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  session_id TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  expert_id TEXT,
  provider TEXT,
  model TEXT,
  tokens INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conversation_id) REFERENCES conversations (id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

CREATE TABLE IF NOT EXISTS friction_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  meta_version TEXT NOT NULL,
  meta_product TEXT NOT NULL,
  meta_tier TEXT NOT NULL,
  meta_timestamp TEXT NOT NULL,
  meta_session_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_code TEXT NOT NULL,
  event_layer TEXT NOT NULL,
  action_attempted TEXT NOT NULL,
  blocked_by TEXT NOT NULL,
  user_message TEXT,
  context_os TEXT NOT NULL,
  context_runtime TEXT NOT NULL,
  context_skill_active TEXT,
  context_connector_active TEXT,
  payload_json TEXT NOT NULL,
  mode TEXT NOT NULL,
  sent INTEGER NOT NULL DEFAULT 0,
  github_url TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  sent_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_friction_events_sent ON friction_events(sent);
CREATE INDEX IF NOT EXISTS idx_friction_events_code ON friction_events(event_code);
CREATE INDEX IF NOT EXISTS idx_friction_events_layer ON friction_events(event_layer);

-- DOWN (rollback)
-- DROP TABLE IF EXISTS friction_events;
-- DROP TABLE IF EXISTS messages;
-- DROP TABLE IF EXISTS conversations;
-- DROP TABLE IF EXISTS users;
