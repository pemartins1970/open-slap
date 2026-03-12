# TODO - Open Slap!

- [ ] Configurar ambiente de desenvolvimento (Node.js, Python)
- [ ] Inicializar repositório Git
- [ ] Criar estrutura base do Frontend (React/Vue)
- [ ] Criar estrutura base do Backend (Node/Python)
- [ ] Implementar sistema de Agentes (MoE)
- [ ] Configurar RAG e Storage local

## TODO - Segurança (família Slap)

- [ ] Padronizar separação Control Plane vs Execution Plane
- [ ] Extrair SecurityProfile único (env vars + políticas + allowlists)
- [ ] Isolar execução de tools em worker sandbox (WSL2/Docker/VM)
- [ ] Forçar execução com permissões mínimas e workspace dedicado
- [ ] Padronizar autenticação em todos endpoints expostos publicamente
- [ ] Padronizar modo local-only e bind seguro (localhost por padrão)
- [ ] Implementar/centralizar rate-limit e ban por IP no gateway local
- [ ] Registrar eventos com timestamp e IP (logs e retenção definida)
- [ ] Exibir alertas de segurança na UI (painel/indicador visível)
- [ ] Definir modelo de secrets (substituir Rubin) para toda família
- [ ] Proibir import externo de skills por padrão (supply chain)
- [ ] Criar biblioteca interna curada de skills (assinada/validada)
- [ ] Implementar skill-creator (fluxo guiado + validação de schema)
- [ ] Revisar todos endpoints de filesystem (somente workspace, sem traversal)
- [ ] Definir política de rede do execution plane (egress allowlist)
- [ ] Endurecer logs: nunca registrar tokens/chaves/segredos em claro
- [ ] Criar checklist de release para GitHub (sem segredos no repo)
