# Módulo de Update Checker — Open Slap! + Slap! GO
**Especificação Técnica v1.0 — Março 2026**

---

## Princípio Central

O produto **nunca atualiza silenciosamente**. O usuário é informado, vê o changelog, decide quando atualizar e tem seus dados protegidos por backup automático antes de qualquer mudança. Em ambientes Enterprise ou air-gapped, o módulo pode ser desabilitado completamente via variável de ambiente, sem efeito colateral.

---

## 1. Escopo por Produto

| Componente | Open Slap! | Slap! GO |
|---|---|---|
| Check de versão via GitHub Releases API | ✅ | ✅ |
| Exibição de changelog antes de atualizar | ✅ UI | ✅ log + API |
| Download do release asset | ✅ | ✅ |
| Verificação de hash SHA256 | ✅ | ✅ |
| Backup automático pré-update | ✅ | ✅ |
| Migrations automáticas pós-update | ✅ | ✅ |
| Smoke test pós-update | ✅ | ✅ |
| Rollback em falha | ✅ | ✅ |
| Desabilitação por env | ✅ | ✅ |
| Token separado do friction token | ✅ | ✅ |

---

## 2. Fluxo Completo de Update

```
Inicialização do produto (ou trigger manual "Verificar atualizações")
        ↓
SLAP_UPDATE_CHECK_ENABLED=false? → encerrar silenciosamente
        ↓
Passou SLAP_UPDATE_CHECK_INTERVAL_HOURS desde o último check? → se não, encerrar
        ↓
GET https://api.github.com/repos/{SLAP_UPDATE_GITHUB_REPO}/releases/latest
(sem autenticação — API pública)
        ↓
Falha de rede? → logar aviso + continuar inicialização normalmente
        ↓
versão remota > versão local?
    └── Não → atualizar timestamp do último check + encerrar
        ↓ Sim
Notificação ao usuário:
"Nova versão disponível: {local} → {remota}  [Ver novidades] [Atualizar] [Ignorar]"
        ↓ usuário clica "Atualizar"
Exibir changelog da nova versão (body do release do GitHub)
        ↓ usuário confirma
Backup automático (label: "pre_update_{versão_remota}")
        ↓
Download do release asset (binário ou pacote)
        ↓
Verificar proveniência do release (assinatura) + integridade (SHA256)
    ├── Hash diverge? → deletar arquivo baixado + ABORT + alerta ao usuário
    └── Hash confere → continuar
        ↓
Instalar nova versão
        ↓
Executar migrations automáticas (módulo de migration)
        ↓
Smoke test
    ├── Falha? → rollback (restaurar backup) + ABORT + alerta
    └── OK → produto reinicia na nova versão
        ↓
Log e notificação: "Atualizado com sucesso para v{remota}"
```

---

## 3. GitHub Releases API — Contrato Esperado

### 3.1 Endpoint

```
GET https://api.github.com/repos/{owner}/{repo}/releases/latest
```

Sem autenticação. Rate limit padrão da API pública: 60 requests/hora por IP — suficiente para checks a cada 24h.

### 3.2 Campos utilizados da resposta

```json
{
  "tag_name": "v0.9.0",
  "name": "Open Slap! v0.9.0",
  "body": "## Novidades\n- Friction Report...\n\n## Dados\n- Migration 004 aplicada...",
  "published_at": "2026-03-11T14:00:00Z",
  "assets": [
    {
      "name": "open-slap-v0.9.0-linux-x64.tar.gz",
      "browser_download_url": "https://github.com/...",
      "size": 45678901
    },
    {
      "name": "open-slap-v0.9.0-linux-x64.tar.gz.sha256",
      "browser_download_url": "https://github.com/..."
    }
  ]
}
```

### 3.3 Convenção de nomenclatura de assets

```
{produto}-v{versão}-{os}-{arch}.{ext}
{produto}-v{versão}-{os}-{arch}.{ext}.sha256

Exemplos:
  open-slap-v0.9.0-linux-x64.tar.gz
  open-slap-v0.9.0-linux-x64.tar.gz.sha256
  open-slap-v0.9.0-win-x64.zip
  open-slap-v0.9.0-win-x64.zip.sha256
  slap-go-v0.7.0-linux-x64.tar.gz
  slap-go-v0.7.0-linux-x64.tar.gz.sha256
```

O produto detecta automaticamente OS e arch em runtime para selecionar o asset correto.

---

## 4. Verificação de Integridade (SHA256)

### 4.1 Publicação (responsabilidade do mantenedor no release)

Para cada asset publicado no GitHub Release, publicar também o arquivo `.sha256` correspondente:

```bash
# Gerar hash (Linux/Mac)
sha256sum open-slap-v0.9.0-linux-x64.tar.gz > open-slap-v0.9.0-linux-x64.tar.gz.sha256

# Conteúdo do arquivo .sha256:
# abc123...def456  open-slap-v0.9.0-linux-x64.tar.gz
```

### 4.2 Verificação em runtime (produto)

```python
# Open Slap! (Python)
import hashlib

def verify_sha256(file_path: str, expected_hash: str) -> bool:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    return actual.lower() == expected_hash.lower().split()[0]
```

```typescript
// Slap! GO (TypeScript)
import * as crypto from "crypto";
import * as fs from "fs";

function verifySHA256(filePath: string, expectedHash: string): boolean {
  const hash = crypto.createHash("sha256");
  const data = fs.readFileSync(filePath);
  hash.update(data);
  const actual = hash.digest("hex");
  return actual.toLowerCase() === expectedHash.toLowerCase().split(/\s/)[0];
}
```

**Política de falha:** se o hash divergir, o arquivo baixado é deletado imediatamente e o update é abortado com alerta explícito ao usuário. Nunca instalar arquivo com hash não verificado.

---

## 4.3 Hardenings obrigatórios (segurança de update)

As regras abaixo são obrigatórias. Elas existem para evitar falhas reais (não preferências).

### 4.3.1 Extração segura de arquivos (anti ZipSlip/TarSlip)

Ao instalar assets `.zip`/`.tar.gz`, o produto deve validar cada entrada antes de extrair:

- Proibido path absoluto (ex.: `/etc/passwd`, `C:\Windows\...`).
- Proibido `..` e qualquer tentativa de escapar do diretório de instalação.
- Proibido symlinks/hardlinks dentro de tar/zip (tratá-los como inválidos).
- Em caso de violação: abortar instalação, manter versão atual e alertar o usuário.

### 4.3.2 Verificação de proveniência (assinatura) além de SHA256

SHA256 sozinho verifica integridade, mas não garante proveniência se um release for comprometido. Portanto, o update deve validar um artefato assinado pelo mantenedor.

Contrato recomendado (por release):

- `release.manifest.json` contendo hashes SHA256 de todos os assets.
- `release.manifest.json.sig` contendo a assinatura do manifest.

O produto deve:

- Embutir (ou carregar via configuração) uma chave pública de verificação do mantenedor.
- Verificar a assinatura antes de confiar em qualquer hash.
- Se a assinatura falhar ou não existir: abortar update com mensagem clara.

### 4.3.3 Rollback automático deve ser “restore clean”

Quando o update falhar (install/migrations/smoke test), o rollback deve restaurar o backup de forma determinística:

- Restaurar banco e diretórios de estado.
- Limpar (wipar) alvos restaurados antes de copiar os arquivos do backup, para evitar “restos” pós-update.

---

## 5. Implementação — Open Slap! (Python)

```python
# src/backend/update_checker.py

import json
import os
import platform
import sys
import tarfile
import zipfile
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

from backup_manager import create_backup
from migration_engine import run_migrations

GITHUB_API = "https://api.github.com"
REPO       = os.getenv("SLAP_UPDATE_GITHUB_REPO", "owner/open-slap")
ENABLED    = os.getenv("SLAP_UPDATE_CHECK_ENABLED", "true").lower() == "true"
INTERVAL_H = int(os.getenv("SLAP_UPDATE_CHECK_INTERVAL_HOURS", "24"))
VERSION    = os.getenv("SLAP_VERSION", "0.0.0")
STATE_FILE = Path("state/update_check.json")
DOWNLOAD_DIR = Path("data/downloads")


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_check": None, "ignored_version": None}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _version_tuple(v: str) -> tuple:
    return tuple(int(x) for x in v.lstrip("v").split("."))


def _detect_asset_suffix() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = "x64" if machine in ("x86_64", "amd64") else "arm64"
    if system == "linux":
        return f"linux-{arch}.tar.gz"
    elif system == "darwin":
        return f"mac-{arch}.tar.gz"
    elif system == "windows":
        return f"win-{arch}.zip"
    raise RuntimeError(f"Sistema não suportado: {system}/{machine}")


def check_for_updates() -> dict | None:
    """
    Retorna dict com info do release se houver update disponível.
    Retorna None se não houver update ou se o check estiver desabilitado.
    """
    if not ENABLED:
        return None

    state = _load_state()
    last_check = state.get("last_check")

    if last_check:
        last_dt = datetime.fromisoformat(last_check)
        if datetime.now(timezone.utc) - last_dt < timedelta(hours=INTERVAL_H):
            return None

    try:
        url = f"{GITHUB_API}/repos/{REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": f"open-slap/{VERSION}"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            release = json.loads(resp.read())
    except Exception as e:
        print(f"[update] Aviso: não foi possível verificar atualizações: {e}")
        return None

    state["last_check"] = datetime.now(timezone.utc).isoformat()
    _save_state(state)

    remote_version = release.get("tag_name", "").lstrip("v")
    ignored = state.get("ignored_version")

    if _version_tuple(remote_version) <= _version_tuple(VERSION):
        return None

    if ignored and _version_tuple(remote_version) <= _version_tuple(ignored):
        return None

    return {
        "version": remote_version,
        "name": release.get("name"),
        "changelog": release.get("body", ""),
        "published_at": release.get("published_at"),
        "assets": release.get("assets", []),
    }


def ignore_version(version: str) -> None:
    state = _load_state()
    state["ignored_version"] = version
    _save_state(state)


def apply_update(release_info: dict) -> None:
    version = release_info["version"]
    suffix = _detect_asset_suffix()
    product = "open-slap"

    asset_name = f"{product}-v{version}-{suffix}"
    hash_name  = f"{asset_name}.sha256"

    asset = next((a for a in release_info["assets"] if a["name"] == asset_name), None)
    asset_hash = next((a for a in release_info["assets"] if a["name"] == hash_name), None)

    if not asset or not asset_hash:
        raise RuntimeError(
            f"Asset '{asset_name}' ou hash '{hash_name}' não encontrado no release."
        )

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    asset_path = DOWNLOAD_DIR / asset_name
    hash_path  = DOWNLOAD_DIR / hash_name

    # 1. Download
    print(f"[update] Baixando {asset_name}...")
    urllib.request.urlretrieve(asset["browser_download_url"], asset_path)
    urllib.request.urlretrieve(asset_hash["browser_download_url"], hash_path)

    # 2. Verificar hash
    expected = hash_path.read_text().strip()
    if not _verify_sha256(asset_path, expected):
        asset_path.unlink(missing_ok=True)
        hash_path.unlink(missing_ok=True)
        raise RuntimeError(
            "CRÍTICO: Hash SHA256 do arquivo baixado não confere. "
            "Download abortado. Tente novamente ou reporte o incidente."
        )

    print("[update] Hash verificado ✓")

    # 3. Backup pré-update
    backup_path = create_backup(f"pre_update_v{version}")
    print(f"[update] Backup criado: {backup_path}")

    # 4. Instalar
    print("[update] Instalando...")
    _install_asset(asset_path, suffix)

    # 5. Limpar downloads
    asset_path.unlink(missing_ok=True)
    hash_path.unlink(missing_ok=True)

    # 6. Migrations
    run_migrations()

    print(f"[update] ✓ Atualizado com sucesso para v{version}")


def _verify_sha256(file_path: Path, expected: str) -> bool:
    import hashlib
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    return actual.lower() == expected.lower().split()[0]


def _install_asset(asset_path: Path, suffix: str) -> None:
    install_dir = Path(os.getenv("SLAP_INSTALL_DIR", "."))
    if suffix.endswith(".tar.gz"):
        with tarfile.open(asset_path, "r:gz") as tar:
            tar.extractall(install_dir)  # extração deve ser segura (ver Seção 4.3.1)
    elif suffix.endswith(".zip"):
        with zipfile.ZipFile(asset_path, "r") as zf:
            zf.extractall(install_dir)  # extração deve ser segura (ver Seção 4.3.1)
```

---

## 6. Implementação — Slap! GO (TypeScript)

```typescript
// src/update/updateChecker.ts

import * as fs from "fs";
import * as path from "path";
import * as https from "https";
import * as crypto from "crypto";
import * as os from "os";
import * as tar from "tar";            // npm install tar
import * as unzipper from "unzipper"; // npm install unzipper
import { createBackup } from "../backup/backupManager";
import { runMigrations } from "../migrations/migrationEngine";

const GITHUB_API  = "https://api.github.com";
const REPO        = process.env.SLAPGO_UPDATE_GITHUB_REPO ?? "owner/slap-go";
const ENABLED     = (process.env.SLAPGO_UPDATE_CHECK_ENABLED ?? "true") === "true";
const INTERVAL_H  = parseInt(process.env.SLAPGO_UPDATE_CHECK_INTERVAL_HOURS ?? "24", 10);
const VERSION     = process.env.SLAPGO_VERSION ?? "0.0.0";
const STATE_FILE  = "state/update_check.json";
const DOWNLOAD_DIR = "data/downloads";

interface UpdateState {
  last_check: string | null;
  ignored_version: string | null;
}

interface ReleaseInfo {
  version: string;
  name: string;
  changelog: string;
  published_at: string;
  assets: { name: string; browser_download_url: string }[];
}

function loadState(): UpdateState {
  if (fs.existsSync(STATE_FILE)) {
    return JSON.parse(fs.readFileSync(STATE_FILE, "utf-8"));
  }
  return { last_check: null, ignored_version: null };
}

function saveState(state: UpdateState): void {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

function versionTuple(v: string): number[] {
  return v.replace(/^v/, "").split(".").map(Number);
}

function compareVersions(a: string, b: string): number {
  const ta = versionTuple(a);
  const tb = versionTuple(b);
  for (let i = 0; i < Math.max(ta.length, tb.length); i++) {
    const diff = (ta[i] ?? 0) - (tb[i] ?? 0);
    if (diff !== 0) return diff;
  }
  return 0;
}

function detectAssetSuffix(): string {
  const platform = os.platform();
  const arch = os.arch() === "x64" ? "x64" : "arm64";
  if (platform === "linux")  return `linux-${arch}.tar.gz`;
  if (platform === "darwin") return `mac-${arch}.tar.gz`;
  if (platform === "win32")  return `win-${arch}.zip`;
  throw new Error(`Plataforma não suportada: ${platform}/${arch}`);
}

function httpsGet(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const req = https.get(url, {
      headers: { "User-Agent": `slap-go/${VERSION}` }
    }, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        return httpsGet(res.headers.location!).then(resolve).catch(reject);
      }
      let data = "";
      res.on("data", chunk => data += chunk);
      res.on("end", () => resolve(data));
    });
    req.on("error", reject);
    req.setTimeout(10000, () => { req.destroy(); reject(new Error("Timeout")); });
  });
}

function httpsDownload(url: string, dest: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    const req = https.get(url, { headers: { "User-Agent": `slap-go/${VERSION}` } }, (res) => {
      if (res.statusCode === 302 || res.statusCode === 301) {
        file.close();
        return httpsDownload(res.headers.location!, dest).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on("finish", () => file.close(() => resolve()));
    });
    req.on("error", reject);
  });
}

export async function checkForUpdates(): Promise<ReleaseInfo | null> {
  if (!ENABLED) return null;

  const state = loadState();

  if (state.last_check) {
    const lastDt = new Date(state.last_check).getTime();
    const elapsed = (Date.now() - lastDt) / 3600000;
    if (elapsed < INTERVAL_H) return null;
  }

  let release: any;
  try {
    const body = await httpsGet(`${GITHUB_API}/repos/${REPO}/releases/latest`);
    release = JSON.parse(body);
  } catch (err) {
    console.warn(`[update] Aviso: não foi possível verificar atualizações: ${err}`);
    return null;
  }

  state.last_check = new Date().toISOString();
  saveState(state);

  const remoteVersion = (release.tag_name as string).replace(/^v/, "");

  if (compareVersions(remoteVersion, VERSION) <= 0) return null;

  if (state.ignored_version && compareVersions(remoteVersion, state.ignored_version) <= 0) {
    return null;
  }

  return {
    version: remoteVersion,
    name: release.name,
    changelog: release.body ?? "",
    published_at: release.published_at,
    assets: release.assets ?? [],
  };
}

export function ignoreVersion(version: string): void {
  const state = loadState();
  state.ignored_version = version;
  saveState(state);
}

export async function applyUpdate(releaseInfo: ReleaseInfo): Promise<void> {
  const { version, assets } = releaseInfo;
  const suffix  = detectAssetSuffix();
  const product = "slap-go";
  const assetName = `${product}-v${version}-${suffix}`;
  const hashName  = `${assetName}.sha256`;

  const asset     = assets.find(a => a.name === assetName);
  const assetHash = assets.find(a => a.name === hashName);

  if (!asset || !assetHash) {
    throw new Error(`Asset '${assetName}' ou hash '${hashName}' não encontrado no release.`);
  }

  fs.mkdirSync(DOWNLOAD_DIR, { recursive: true });
  const assetPath = path.join(DOWNLOAD_DIR, assetName);
  const hashPath  = path.join(DOWNLOAD_DIR, hashName);

  // 1. Download
  console.log(`[update] Baixando ${assetName}...`);
  await httpsDownload(asset.browser_download_url, assetPath);
  await httpsDownload(assetHash.browser_download_url, hashPath);

  // 2. Verificar hash
  const expected = fs.readFileSync(hashPath, "utf-8").trim();
  if (!verifySHA256(assetPath, expected)) {
    fs.unlinkSync(assetPath);
    fs.unlinkSync(hashPath);
    throw new Error(
      "CRÍTICO: Hash SHA256 do arquivo baixado não confere. " +
      "Download abortado. Tente novamente ou reporte o incidente."
    );
  }

  console.log("[update] Hash verificado ✓");

  // 3. Backup pré-update
  const backupPath = await createBackup(`pre_update_v${version}`);
  console.log(`[update] Backup criado: ${backupPath}`);

  // 4. Instalar
  console.log("[update] Instalando...");
  const installDir = process.env.SLAPGO_INSTALL_DIR ?? ".";

  if (suffix.endsWith(".tar.gz")) {
    await tar.extract({ file: assetPath, cwd: installDir });
  } else if (suffix.endsWith(".zip")) {
    await fs.createReadStream(assetPath)
      .pipe(unzipper.Extract({ path: installDir }))
      .promise();
  }

  // 5. Limpar downloads
  fs.unlinkSync(assetPath);
  fs.unlinkSync(hashPath);

  // 6. Migrations
  await runMigrations();

  console.log(`[update] ✓ Atualizado com sucesso para v${version}`);
}

function verifySHA256(filePath: string, expected: string): boolean {
  const hash = crypto.createHash("sha256");
  const data = fs.readFileSync(filePath);
  hash.update(data);
  const actual = hash.digest("hex");
  return actual.toLowerCase() === expected.toLowerCase().split(/\s/)[0];
}
```

---

## 7. API REST do Update Checker (ambos os produtos)

```
GET  /api/update/status
     → retorna versão atual, última verificação e se há update disponível
     Resposta: {
       "current_version": "0.8.1",
       "remote_version": "0.9.0",    // null se sem update
       "update_available": true,
       "last_check": "2026-03-11T14:00:00Z",
       "changelog": "## Novidades..."
     }

POST /api/update/check
     → força verificação imediata (ignora intervalo)
     → requer autenticação JWT

POST /api/update/ignore
     Body: { "version": "0.9.0" }
     → ignora esta versão específica até que haja uma mais nova
     → requer autenticação JWT

POST /api/update/apply
     Body: { "version": "0.9.0", "confirm": true }
     → inicia processo de update (download → hash → backup → install → migrate)
     → requer autenticação JWT + campo "confirm": true obrigatório
     → streaming de log via SSE ou WebSocket durante o processo
```

---

## 8. Notificação ao Usuário

### Open Slap! (UI)

Banner discreto no topo da interface, não-bloqueante:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🔔 Nova versão disponível: v0.8.1 → v0.9.0  [Ver novidades]  [Atualizar]  [Ignorar]  │
└─────────────────────────────────────────────────────────────────────────┘
```

- "Ver novidades" → abre modal com o `changelog` do release
- "Atualizar" → solicita confirmação → inicia `POST /api/update/apply`
- "Ignorar" → chama `POST /api/update/ignore` para esta versão

### Slap! GO (log + API)

```
[update] Nova versão disponível: v0.6.0 → v0.7.0
[update] Changelog: https://github.com/{repo}/releases/tag/v0.7.0
[update] Para atualizar: POST /api/update/apply { "version": "0.7.0", "confirm": true }
[update] Para ignorar: POST /api/update/ignore { "version": "0.7.0" }
```

---

## 9. Variáveis de Ambiente

### Open Slap!

```env
# Habilitar verificação de updates
SLAP_UPDATE_CHECK_ENABLED=true

# Intervalo entre checks (horas)
SLAP_UPDATE_CHECK_INTERVAL_HOURS=24

# Repositório de releases no GitHub
SLAP_UPDATE_GITHUB_REPO=owner/open-slap

# Diretório de instalação (para extração do asset)
SLAP_INSTALL_DIR=.

# Versão atual (injetada no build)
SLAP_VERSION=0.8.1
```

### Slap! GO

```env
# Habilitar verificação de updates
SLAPGO_UPDATE_CHECK_ENABLED=true

# Intervalo entre checks (horas)
SLAPGO_UPDATE_CHECK_INTERVAL_HOURS=24

# Repositório de releases no GitHub
SLAPGO_UPDATE_GITHUB_REPO=owner/slap-go

# Diretório de instalação
SLAPGO_INSTALL_DIR=.

# Versão atual (injetada no build)
SLAPGO_VERSION=0.6.0
```

**Nota Enterprise / air-gapped:**

```env
# Desabilitar completamente — sem efeito colateral
SLAP_UPDATE_CHECK_ENABLED=false
SLAPGO_UPDATE_CHECK_ENABLED=false
```

---

## 10. Checklist de Release (responsabilidade do mantenedor)

Para cada release publicado no GitHub, verificar antes de publicar:

- [ ] Tag segue o padrão `v{major}.{minor}.{patch}`
- [ ] Assets compilados para todas as plataformas: `linux-x64`, `mac-x64`, `win-x64`
- [ ] Hash SHA256 gerado e publicado para cada asset (`.sha256`)
- [ ] Manifest assinado publicado (`release.manifest.json` + `release.manifest.json.sig`)
- [ ] `body` do release contém CHANGELOG legível pelo usuário
- [ ] CHANGELOG inclui seção "Dados e Memória" descrevendo migrations e impacto
- [ ] Versão atualizada em `.env.example`, `package.json` ou equivalente
- [ ] Migration scripts adicionados ao diretório correto

---

## 11. Definition of Done

O módulo está corretamente implementado quando:

1. `SLAP_UPDATE_CHECK_ENABLED=false` desabilita completamente o módulo — sem requests, sem logs, sem efeito colateral
2. Check com rede indisponível não interrompe a inicialização do produto — apenas loga aviso
3. Versão remota igual ou menor que local não gera notificação
4. Versão ignorada via `POST /api/update/ignore` não gera notificação para aquela versão
5. "Atualizar" exige confirmação explícita do usuário antes de iniciar o processo
6. Asset com hash divergente é deletado imediatamente e update é abortado com mensagem clara
7. Extração de assets é segura contra path traversal e links (ZipSlip/TarSlip)
8. Update valida proveniência via manifest assinado antes de confiar em hashes
9. Backup é criado antes de qualquer instalação — sem exceção
10. Falha em install/migration pós-update aciona rollback com restore clean
11. Smoke test falha = produto não completa o update e reverte
12. API REST exige autenticação JWT para todas as operações de escrita (`/apply`, `/ignore`, `/check`)
13. Changelog do release é exibido/logado antes de qualquer ação do usuário
14. Intervalo entre checks é respeitado — sem requests desnecessários à API do GitHub

---

*Slap! Ecosystem — Especificação Técnica Interna — Março 2026*
