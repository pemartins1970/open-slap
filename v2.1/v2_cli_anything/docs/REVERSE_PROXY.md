# Reverse Proxy / Hosting (IIS, Nginx, Apache)

Open Slap! é um serviço desktop-local, mas pode ser exposto em rede (LAN) ou “publicado” atrás de um servidor web via reverse proxy.

## Conceito

- Backend (FastAPI) roda como processo separado (ex.: `127.0.0.1:5150`).
- Frontend pode ser:
  - Dev (Vite) para desenvolvimento, ou
  - Build estático (`src/frontend/dist`) para servir via IIS/Nginx/Apache.
- O proxy deve encaminhar:
  - HTTP: `/api`, `/auth`, `/health` → backend
  - WebSocket: `/ws` → backend (precisa de suporte a WebSockets no proxy)

## IIS (Windows)

Opção recomendada: IIS como reverse proxy para o backend e servidor de arquivos estáticos para o frontend buildado.

Pré-requisitos:
- URL Rewrite + ARR (Application Request Routing) com Proxy habilitado
- WebSocket Protocol habilitado no IIS

Passos (alto nível):
- Servir arquivos do frontend buildado (pasta `src/frontend/dist`) como site no IIS.
- Criar regras de rewrite/proxy:
  - `/api/*` → `http://127.0.0.1:5150/api/{R:1}`
  - `/auth/*` → `http://127.0.0.1:5150/auth/{R:1}`
  - `/health` → `http://127.0.0.1:5150/health`
  - `/ws/*` → proxy para `ws://127.0.0.1:5150/ws/{R:1}` (WebSocket)

Notas:
- Se usar HTTPS no IIS, o backend pode continuar em HTTP local.
- Garanta que o header `Host` e `X-Forwarded-*` estejam corretos se você usar lógica baseada em host.

## Nginx (Linux/macOS/WSL)

Exemplo (conceitual):

```nginx
server {
  listen 80;
  server_name open-slap.local;

  root /path/to/src/frontend/dist;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://127.0.0.1:5150/api/;
  }

  location /auth/ {
    proxy_pass http://127.0.0.1:5150/auth/;
  }

  location /health {
    proxy_pass http://127.0.0.1:5150/health;
  }

  location /ws/ {
    proxy_pass http://127.0.0.1:5150/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
  }
}
```

## Apache (mod_proxy)

Você precisa de `mod_proxy`, `mod_proxy_http` e `mod_proxy_wstunnel` (para `/ws`).

## Laravel / outros servidores “de app”

Laravel, Rails, etc. não servem o Open Slap diretamente. O que funciona é:
- seu servidor web (Nginx/Apache/IIS) serve o build do frontend como arquivos estáticos
- e faz reverse proxy para o backend FastAPI nos paths `/api`, `/auth`, `/health`, `/ws`

## Segurança mínima ao expor em rede

- Preferir LAN (rede local) antes de expor publicamente.
- Se expor fora da LAN, colocar autenticação/HTTPS no proxy e restringir IP.
- Não publicar com permissões de OS commands habilitadas sem hardening e controle.

