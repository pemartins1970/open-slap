# Módulo de Migrations e Backup — Open Slap! + Slap! GO
**Especificação Técnica v1.0 — Março 2026**

---

## Princípio Central

Toda atualização que toca em dados do usuário deve ser **reversível, auditável e transparente**. O usuário nunca perde dados por causa de um update. O produto nunca entra em estado inconsistente silencioso. Em caso de falha em qualquer etapa, rollback automático para o estado anterior.

---

## 1. Escopo por Produto

| Componente | Open Slap! | Slap! GO |
|---|---|---|
| Schema SQLite versionado | ✅ | ✅ |
| Migrations automáticas na inicialização | ✅ | ✅ |
| Backup automático pré-update | ✅ | ✅ |
| Backup automático pré-migration | ✅ | ✅ |
| Smoke test pós-migration | ✅ | ✅ |
| Rollback automático em falha | ✅ | ✅ |
| Notificação ao usuário | ✅ UI + log | ✅ log + resposta de API |
| Cobertura de arquivos JSON de estado | ✅ | ✅ |
| Cobertura de brain files (MD) | ✅ | N/A |
| Cobertura de working set (contexts/) | ✅ | ✅ |

---

## 2. Versionamento de Schema

### 2.1 Tabela de controle (ambos os produtos)

A primeira tabela criada em qualquer banco do ecossistema Slap! é sempre `schema_version`:

```sql
CREATE TABLE IF NOT EXISTS schema_version (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  version     INTEGER NOT NULL UNIQUE,
  applied_at  TEXT    NOT NULL,
  description TEXT    NOT NULL,
  checksum    TEXT    NOT NULL  -- SHA256 do script SQL da migration
);
```

### 2.2 Convenção de numeração

```
001 — schema inicial (criação das tabelas base)
002 — primeira evolução
003 — segunda evolução
...
NNN — sempre incremental, nunca pula número, nunca reutiliza
```

### 2.3 Localização dos scripts

```
Open Slap!
└── src/backend/migrations/
    ├── 001_initial_schema.sql
    ├── 002_add_project_id_to_messages.sql
    ├── 003_add_friction_events.sql
    └── ...

Slap! GO
└── src/migrations/
    ├── 001_initial_schema.sql
    ├── 002_add_audit_trail.sql
    ├── 003_add_friction_events.sql
    └── ...
```

### 2.4 Formato de cada script SQL

```sql
-- Migration: 003
-- Description: Adiciona tabela de friction events
-- Author: sistema
-- Date: 2026-03-11
-- Reversible: yes (ver rollback abaixo)

-- UP
CREATE TABLE IF NOT EXISTS friction_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at  TEXT    NOT NULL,
  code        TEXT    NOT NULL,
  layer       TEXT    NOT NULL,
  payload     TEXT    NOT NULL,
  sent        INTEGER DEFAULT 0,
  github_url  TEXT
);

-- DOWN (rollback)
-- DROP TABLE IF EXISTS friction_events;
```

**Regra obrigatória:** todo script tem seção `-- DOWN` comentada. Mesmo que nunca seja executada automaticamente, documenta como reverter manualmente.

---

## 3. Engine de Migration

### 3.1 Fluxo de execução (inicialização do produto)

```
Produto inicializa
        ↓
Abre conexão com SQLite
        ↓
schema_version existe?
    ├── Não → criar tabela + executar migration 001
    └── Sim → ler versão atual (MAX(version))
        ↓
Validar integridade das migrations já aplicadas (checksum)
    ├── Script ausente ou checksum diverge? → ABORT + alerta crítico
    └── OK → continuar
        ↓
Listar scripts em migrations/ ordenados por número
        ↓
Para cada script com version > versão_atual:
    ├── Verificar checksum do script (SHA256)
    │   └── Checksum diverge? → ABORT + alerta crítico
    ├── Criar backup pré-migration (ver Seção 4)
    ├── Executar script em transação
    │   ├── Sucesso → registrar em schema_version + log
    │   └── Falha   → rollback da transação + restaurar backup + ABORT
    └── Próxima migration
        ↓
Todas as migrations aplicadas → produto continua inicialização
```

### 3.2 Implementação — Open Slap! (Python)

```python
# src/backend/migration_engine.py

import sqlite3
import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
DB_PATH = Path(os.getenv("SLAP_DB_PATH", "data/auth.db"))
BACKUP_DIR = Path(os.getenv("SLAP_BACKUP_DIR", "data/backups"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_current_version(conn: sqlite3.Connection) -> int:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            version     INTEGER NOT NULL UNIQUE,
            applied_at  TEXT    NOT NULL,
            description TEXT    NOT NULL,
            checksum    TEXT    NOT NULL
        )
    """)
    conn.commit()
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] or 0


def list_pending_migrations(current_version: int) -> list[Path]:
    scripts = sorted(MIGRATIONS_DIR.glob("*.sql"))
    pending = []
    for script in scripts:
        try:
            num = int(script.stem.split("_")[0])
        except ValueError:
            continue
        if num > current_version:
            pending.append(script)
    return pending


def extract_description(script: Path) -> str:
    for line in script.read_text().splitlines():
        if line.startswith("-- Description:"):
            return line.replace("-- Description:", "").strip()
    return script.stem


def run_migrations() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        current = get_current_version(conn)
        verify_applied_migrations(conn)
        pending = list_pending_migrations(current)

        if not pending:
            return  # Nada a fazer

        print(f"[migration] {len(pending)} migration(s) pendente(s)")

        for script in pending:
            version = int(script.stem.split("_")[0])
            checksum = sha256_file(script)
            description = extract_description(script)

            # Backup antes de cada migration
            backup_path = create_backup(label=f"pre_migration_{version:03d}")
            print(f"[migration] Backup criado: {backup_path}")

            try:
                sql = script.read_text()
                # Executar apenas a seção UP (antes de "-- DOWN")
                up_sql = sql.split("-- DOWN")[0]

                with conn:  # transação automática
                    conn.executescript(up_sql)
                    conn.execute(
                        "INSERT INTO schema_version (version, applied_at, description, checksum) "
                        "VALUES (?, ?, ?, ?)",
                        (version, datetime.now(timezone.utc).isoformat(), description, checksum)
                    )

                print(f"[migration] ✓ Migration {version:03d} aplicada: {description}")

            except Exception as e:
                print(f"[migration] ✗ Falha na migration {version:03d}: {e}")
                print(f"[migration] Restaurando backup: {backup_path}")
                conn.close()
                restore_backup(backup_path)
                raise SystemExit(
                    f"CRÍTICO: Migration {version:03d} falhou. "
                    f"Backup restaurado de {backup_path}. "
                    f"Verifique o log e o script {script.name}."
                )

        smoke_test(conn)

    finally:
        conn.close()

def verify_applied_migrations(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT version, checksum FROM schema_version ORDER BY version ASC"
    ).fetchall()
    for version, expected_checksum in rows:
        scripts = sorted(MIGRATIONS_DIR.glob(f"{int(version):03d}_*.sql"))
        if not scripts:
            raise SystemExit(
                f"CRÍTICO: Script da migration {int(version):03d} não encontrado em {MIGRATIONS_DIR}."
            )
        script = scripts[0]
        actual_checksum = sha256_file(script)
        if actual_checksum != expected_checksum:
            raise SystemExit(
                f"CRÍTICO: Checksum diverge para migration {int(version):03d}. "
                f"Esperado={expected_checksum} Atual={actual_checksum}. ABORT."
            )


def smoke_test(conn: sqlite3.Connection) -> None:
    checks = [
        ("schema_version", "SELECT COUNT(*) FROM schema_version"),
        ("conversations",  "SELECT COUNT(*) FROM conversations"),
        ("messages",       "SELECT COUNT(*) FROM messages"),
        ("friction_events","SELECT COUNT(*) FROM friction_events"),
    ]
    for name, query in checks:
        try:
            conn.execute(query)
            print(f"[smoke_test] ✓ {name}")
        except Exception as e:
            raise RuntimeError(f"[smoke_test] ✗ {name} falhou: {e}")

    print("[smoke_test] Todas as verificações passaram.")
```

### 3.3 Implementação — Slap! GO (TypeScript)

```typescript
// src/migrations/migrationEngine.ts

import Database from "better-sqlite3";
import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";
import { createBackup, restoreBackup } from "./backupManager";

const MIGRATIONS_DIR = path.join(__dirname, "migrations");
const DB_PATH = process.env.SLAPGO_DB_PATH ?? "data/openslapgo.db";

interface MigrationRecord {
  version: number;
  applied_at: string;
  description: string;
  checksum: string;
}

function sha256File(filePath: string): string {
  const content = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(content).digest("hex");
}

function getCurrentVersion(db: Database.Database): number {
  db.exec(`
    CREATE TABLE IF NOT EXISTS schema_version (
      id          INTEGER PRIMARY KEY AUTOINCREMENT,
      version     INTEGER NOT NULL UNIQUE,
      applied_at  TEXT    NOT NULL,
      description TEXT    NOT NULL,
      checksum    TEXT    NOT NULL
    )
  `);
  const row = db.prepare("SELECT MAX(version) as v FROM schema_version").get() as { v: number | null };
  return row?.v ?? 0;
}

function listPendingMigrations(currentVersion: number): string[] {
  const files = fs.readdirSync(MIGRATIONS_DIR)
    .filter(f => f.endsWith(".sql"))
    .sort();

  return files.filter(f => {
    const num = parseInt(f.split("_")[0], 10);
    return !isNaN(num) && num > currentVersion;
  }).map(f => path.join(MIGRATIONS_DIR, f));
}

function extractDescription(scriptPath: string): string {
  const lines = fs.readFileSync(scriptPath, "utf-8").split("\n");
  const line = lines.find(l => l.startsWith("-- Description:"));
  return line ? line.replace("-- Description:", "").trim() : path.basename(scriptPath);
}

export async function runMigrations(): Promise<void> {
  const db = new Database(DB_PATH);

  try {
    const current = getCurrentVersion(db);
    const pending = listPendingMigrations(current);

    if (pending.length === 0) return;

    console.log(`[migration] ${pending.length} migration(s) pendente(s)`);

    for (const scriptPath of pending) {
      const version = parseInt(path.basename(scriptPath).split("_")[0], 10);
      const checksum = sha256File(scriptPath);
      const description = extractDescription(scriptPath);

      const backupPath = await createBackup(`pre_migration_${String(version).padStart(3, "0")}`);
      console.log(`[migration] Backup criado: ${backupPath}`);

      try {
        let sql = fs.readFileSync(scriptPath, "utf-8");
        // Usar apenas a seção UP
        sql = sql.split("-- DOWN")[0];

        const applyMigration = db.transaction(() => {
          db.exec(sql);
          db.prepare(
            "INSERT INTO schema_version (version, applied_at, description, checksum) VALUES (?, ?, ?, ?)"
          ).run(version, new Date().toISOString(), description, checksum);
        });

        applyMigration();
        console.log(`[migration] ✓ Migration ${version.toString().padStart(3, "0")} aplicada: ${description}`);

      } catch (err) {
        console.error(`[migration] ✗ Falha na migration ${version}: ${err}`);
        db.close();
        await restoreBackup(backupPath);
        throw new Error(
          `CRÍTICO: Migration ${version} falhou. Backup restaurado de ${backupPath}.`
        );
      }
    }

    smokeTest(db);

  } finally {
    db.close();
  }
}

function smokeTest(db: Database.Database): void {
  const checks = [
    ["schema_version", "SELECT COUNT(*) FROM schema_version"],
    ["conversations",  "SELECT COUNT(*) FROM conversations"],
    ["messages",       "SELECT COUNT(*) FROM messages"],
    ["friction_events","SELECT COUNT(*) FROM friction_events"],
  ];

  for (const [name, query] of checks) {
    try {
      db.prepare(query).get();
      console.log(`[smoke_test] ✓ ${name}`);
    } catch (err) {
      throw new Error(`[smoke_test] ✗ ${name} falhou: ${err}`);
    }
  }

  console.log("[smoke_test] Todas as verificações passaram.");
}
```

---

## 4. Módulo de Backup

### 4.1 O que é incluído no backup

| Arquivo / Diretório | Open Slap! | Slap! GO |
|---|---|---|
| `data/auth.db` / `data/openslapgo.db` | ✅ | ✅ |
| `state/*.json` | ✅ | ✅ |
| `storage/contexts/*.json` | ✅ | ✅ |
| `brain/*.md` | ✅ | N/A |
| `projects/*/memory.md` | ✅ | N/A |
| `.env` (sem valores, apenas chaves) | ✅ | ✅ |

**Nunca incluir no backup:**
- Tokens, API keys, secrets (qualquer valor de `.env`)
- Arquivos de log brutos
- `node_modules/`, `__pycache__/`, binários

### 4.2 Estrutura do diretório de backup

```
data/backups/
├── 2026-03-11T14-32-00_pre_migration_003/
│   ├── auth.db                  (cópia do SQLite)
│   ├── state/
│   │   ├── user.json
│   │   ├── activities.json
│   │   └── projects.json
│   ├── brain/
│   │   ├── SOUL.md
│   │   ├── STYLE.md
│   │   └── SECURITY.md
│   ├── storage/contexts/        (working sets)
│   └── backup_manifest.json     (metadados do backup)
│
├── 2026-03-11T15-00-00_pre_update_v0.9/
│   └── ...
│
└── 2026-03-12T09-00-00_manual/
    └── ...
```

### 4.3 backup_manifest.json

```json
{
  "label": "pre_migration_003",
  "created_at": "2026-03-11T14:32:00Z",
  "product": "open-slap",
  "product_version": "0.8.1",
  "schema_version": 2,
  "trigger": "auto_migration",
  "files": [
    { "path": "auth.db",              "sha256": "abc123..." },
    { "path": "state/user.json",      "sha256": "def456..." },
    { "path": "state/activities.json","sha256": "ghi789..." }
  ],
  "restorable": true
}
```

### 4.4 Implementação — Open Slap! (Python)

```python
# src/backend/backup_manager.py

import json
import os
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path

DB_PATH      = Path(os.getenv("SLAP_DB_PATH",    "data/auth.db"))
BACKUP_DIR   = Path(os.getenv("SLAP_BACKUP_DIR", "data/backups"))
STATE_DIR    = Path("state")
BRAIN_DIR    = Path("brain")
CONTEXTS_DIR = Path("storage/contexts")
PROJECTS_DIR = Path("projects")

BACKUP_SOURCES = [
    DB_PATH,
    STATE_DIR,
    BRAIN_DIR,
    CONTEXTS_DIR,
    PROJECTS_DIR,
]

MAX_BACKUPS = int(os.getenv("SLAP_BACKUP_MAX_RETAIN", "10"))


def sha256_path(path: Path) -> str:
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return ""


def create_backup(label: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    backup_path = BACKUP_DIR / f"{timestamp}_{label}"
    backup_path.mkdir(parents=True, exist_ok=True)

    manifest_files = []

    for source in BACKUP_SOURCES:
        if not source.exists():
            continue
        dest = backup_path / source
        if source.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            manifest_files.append({
                "path": str(source),
                "sha256": sha256_path(source)
            })
        elif source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)
            for f in source.rglob("*"):
                if f.is_file():
                    manifest_files.append({
                        "path": str(f),
                        "sha256": sha256_path(f)
                    })

    manifest = {
        "label": label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "product": "open-slap",
        "product_version": os.getenv("SLAP_VERSION", "unknown"),
        "schema_version": _get_schema_version(),
        "trigger": label,
        "files": manifest_files,
        "restorable": True
    }

    (backup_path / "backup_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False)
    )

    _prune_old_backups()
    return backup_path


def restore_backup(backup_path: Path) -> None:
    manifest_path = backup_path / "backup_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest não encontrado em {backup_path}")

    manifest = json.loads(manifest_path.read_text())

    targets_to_clean = [DB_PATH, STATE_DIR, BRAIN_DIR, CONTEXTS_DIR, PROJECTS_DIR]
    for t in targets_to_clean:
        if t.is_file() and t.exists():
            t.unlink()
        elif t.is_dir() and t.exists():
            shutil.rmtree(t)

    for entry in manifest["files"]:
        src = backup_path / entry["path"]
        dst = Path(entry["path"])
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    print(f"[backup] Restaurado de {backup_path}")


def list_backups() -> list[dict]:
    if not BACKUP_DIR.exists():
        return []
    result = []
    for d in sorted(BACKUP_DIR.iterdir(), reverse=True):
        manifest = d / "backup_manifest.json"
        if manifest.exists():
            result.append(json.loads(manifest.read_text()))
    return result


def _prune_old_backups() -> None:
    if not BACKUP_DIR.exists():
        return
    backups = sorted(
        [d for d in BACKUP_DIR.iterdir() if d.is_dir()],
        key=lambda d: d.stat().st_mtime,
        reverse=True
    )
    for old in backups[MAX_BACKUPS:]:
        shutil.rmtree(old)
        print(f"[backup] Backup antigo removido: {old.name}")


def _get_schema_version() -> int:
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        conn.close()
        return row[0] or 0
    except Exception:
        return 0
```

### 4.5 Implementação — Slap! GO (TypeScript)

```typescript
// src/backup/backupManager.ts

import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";
import Database from "better-sqlite3";

const DB_PATH      = process.env.SLAPGO_DB_PATH    ?? "data/openslapgo.db";
const BACKUP_DIR   = process.env.SLAPGO_BACKUP_DIR ?? "data/backups";
const MAX_BACKUPS  = parseInt(process.env.SLAPGO_BACKUP_MAX_RETAIN ?? "10", 10);

const BACKUP_SOURCES = [
  DB_PATH,
  "state",
  "storage/contexts",
];

function sha256File(filePath: string): string {
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) return "";
  const content = fs.readFileSync(filePath);
  return crypto.createHash("sha256").update(content).digest("hex");
}

function copyRecursive(src: string, dest: string, files: { path: string; sha256: string }[]) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  if (stat.isFile()) {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
    files.push({ path: src, sha256: sha256File(src) });
  } else if (stat.isDirectory()) {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src)) {
      copyRecursive(path.join(src, entry), path.join(dest, entry), files);
    }
  }
}

export async function createBackup(label: string): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  const backupPath = path.join(BACKUP_DIR, `${timestamp}_${label}`);
  fs.mkdirSync(backupPath, { recursive: true });

  const manifestFiles: { path: string; sha256: string }[] = [];

  for (const source of BACKUP_SOURCES) {
    copyRecursive(source, path.join(backupPath, source), manifestFiles);
  }

  const manifest = {
    label,
    created_at: new Date().toISOString(),
    product: "slap-go",
    product_version: process.env.SLAPGO_VERSION ?? "unknown",
    schema_version: getSchemaVersion(),
    trigger: label,
    files: manifestFiles,
    restorable: true,
  };

  fs.writeFileSync(
    path.join(backupPath, "backup_manifest.json"),
    JSON.stringify(manifest, null, 2)
  );

  pruneOldBackups();
  return backupPath;
}

export async function restoreBackup(backupPath: string): Promise<void> {
  const manifestPath = path.join(backupPath, "backup_manifest.json");
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Manifest não encontrado em ${backupPath}`);
  }

  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));

  for (const entry of manifest.files as { path: string }[]) {
    const src = path.join(backupPath, entry.path);
    const dst = entry.path;
    if (fs.existsSync(src)) {
      fs.mkdirSync(path.dirname(dst), { recursive: true });
      fs.copyFileSync(src, dst);
    }
  }

  console.log(`[backup] Restaurado de ${backupPath}`);
}

export function listBackups(): object[] {
  if (!fs.existsSync(BACKUP_DIR)) return [];
  return fs.readdirSync(BACKUP_DIR)
    .map(d => path.join(BACKUP_DIR, d, "backup_manifest.json"))
    .filter(f => fs.existsSync(f))
    .map(f => JSON.parse(fs.readFileSync(f, "utf-8")))
    .sort((a: any, b: any) => b.created_at.localeCompare(a.created_at));
}

function pruneOldBackups(): void {
  if (!fs.existsSync(BACKUP_DIR)) return;
  const dirs = fs.readdirSync(BACKUP_DIR)
    .map(d => path.join(BACKUP_DIR, d))
    .filter(d => fs.statSync(d).isDirectory())
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);

  for (const old of dirs.slice(MAX_BACKUPS)) {
    fs.rmSync(old, { recursive: true, force: true });
    console.log(`[backup] Backup antigo removido: ${path.basename(old)}`);
  }
}

function getSchemaVersion(): number {
  try {
    const db = new Database(DB_PATH, { readonly: true });
    const row = db.prepare("SELECT MAX(version) as v FROM schema_version").get() as { v: number | null };
    db.close();
    return row?.v ?? 0;
  } catch {
    return 0;
  }
}
```

---

## 5. Política de Compatibilidade de Dados

### 5.1 Regras para arquivos JSON de estado

```
PERMITIDO em qualquer update:
  ✅ Adicionar novo campo com valor default
  ✅ Adicionar novo arquivo JSON de estado
  ✅ Alterar valor default de campo existente

PROIBIDO sem migration explícita:
  ❌ Remover campo existente
  ❌ Renomear campo existente
  ❌ Alterar tipo de campo existente
  ❌ Alterar estrutura aninhada de campo existente
```

### 5.2 Regras para arquivos Markdown (Open Slap!)

Arquivos Markdown são formato livre — não têm schema. A única regra é:

```
O agente NUNCA modifica brain/SOUL.md e brain/SECURITY.md.
Outros arquivos MD podem ser atualizados pelo agente somente
mediante confirmação explícita do usuário.
```

### 5.3 CHANGELOG obrigatório por release

Todo release com mudança de dados deve incluir:

```markdown
## Dados e Memória

### Migrations aplicadas
- Migration 003: Adiciona tabela friction_events (retrocompatível)

### Compatibilidade
- state/user.json: adicionado campo `timezone` com default `"UTC"`
- Backup automático gerado antes da atualização

### Ação necessária do usuário
- Nenhuma
```

---

## 6. Variáveis de Ambiente

### Open Slap!

```env
# Banco de dados
SLAP_DB_PATH=data/auth.db

# Backups
SLAP_BACKUP_DIR=data/backups
SLAP_BACKUP_MAX_RETAIN=10

# Migrations
SLAP_MIGRATIONS_DIR=src/backend/migrations

# Versão do produto (injetada no build)
SLAP_VERSION=0.8.1
```

### Slap! GO

```env
# Banco de dados
SLAPGO_DB_PATH=data/openslapgo.db

# Backups
SLAPGO_BACKUP_DIR=data/backups
SLAPGO_BACKUP_MAX_RETAIN=10

# Migrations
SLAPGO_MIGRATIONS_DIR=src/migrations

# Versão do produto (injetada no build)
SLAPGO_VERSION=0.6.0
```

---

## 7. API REST de Backups (ambos os produtos)

Para exposição via UI e integração com o NEXUS:

```
GET  /api/backups
     → lista todos os backups com metadados do manifest

POST /api/backups
     Body: { "label": "manual" }
     → cria backup manual imediatamente
     → requer autenticação JWT

POST /api/backups/restore
     Body: { "backup_id": "2026-03-11T14-32-00_pre_migration_003" }
     → restaura backup específico
     → requer autenticação JWT + confirmação (campo "confirm": true)

DELETE /api/backups/:id
     → remove backup específico
     → requer autenticação JWT
```

---

## 8. Definition of Done

O módulo está corretamente implementado quando:

1. Produto inicializa sem erro com banco novo (migration 001 aplicada automaticamente)
2. Produto inicializa sem erro com banco existente na versão mais recente (zero migrations pendentes)
3. Migrations pendentes são aplicadas em ordem, uma por vez, com backup antes de cada uma
4. Produto valida checksums das migrations já aplicadas; divergência = abort com alerta crítico
5. Falha em qualquer migration aciona rollback automático (restore clean) e interrompe a inicialização com mensagem clara
5. Smoke test falha se qualquer tabela esperada não existir após migration
6. Backup contém todas as fontes listadas na Seção 4.1 com manifest válido
7. `pruneOldBackups` nunca apaga backups além do limite `MAX_BACKUPS`
8. API REST de backups requer autenticação JWT para operações de escrita/restore
9. Restore a partir do manifest reconstrói o estado exato dos arquivos incluídos
10. CHANGELOG de cada release descreve explicitamente todas as migrations e impacto em dados do usuário

---

*Slap! Ecosystem — Especificação Técnica Interna — Março 2026*
