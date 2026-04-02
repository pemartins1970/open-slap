# Packaging / Release — Open Slap!

## Objetivo

Evitar vazamento de artefatos sensíveis e manter o pacote público limpo (sem sourcemaps, DBs, caches, secrets).

## Regras obrigatórias

- Não incluir `.map`, `.env`, `node_modules/`, `dist/` de dev, `__pycache__/`, bancos locais (`*.db`, `*.sqlite`) nos ZIPs públicos.
- Build frontend sem sourcemap para distribuição.
- Revisão manual do pacote antes de publicar.

## Frontend (Vite)

- Configuração já aplicada: `build.sourcemap: false` em `src/frontend/vite_auth.config.js`.
- Gerar artefatos:

```powershell
cd src\frontend
npm run build
```

- Publicar apenas `src/frontend/dist/` (quando necessário).

## Backend

- Não publicar `data/` (DB local).
- Usar `restart_backend.bat` no dev; sem `--reload` para estabilidade em demos.

## Checklist de release (ZIP)

```
[ ] dist/ está presente (se aplicável) e sem .map
[ ] src/backend/data/ não está no ZIP
[ ] nenhum .env (.env.example pode)
[ ] nenhum node_modules/
[ ] nenhum __pycache__/
[ ] nenhum *.db / *.sqlite
[ ] README.md atualizado + docs/INSTALLATION.md
[ ] docs/DEV_JOURNAL.md + docs/CHANGELOG.md presentes
```

## Verificação automática (sugerida)

- Script que inspeciona o pacote e falha se encontrar padrões proibidos:
  - tools/verify_package.ps1
- Fluxo pré-release:
  - tools/pre_release.ps1 -BuildFrontend
