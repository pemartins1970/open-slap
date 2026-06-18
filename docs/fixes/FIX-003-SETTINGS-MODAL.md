# FIX-003: Settings Modal — Correcções de Props e i18n

**Data:** 2026-06-16  
**Tipo:** Correção de fiação de props + bug de i18n  
**Executor:** Opencode  
**Pré-requisito:** FIX-001 executado  
**Pode ser paralelo a:** FIX-002 (arquivos distintos)

---

## Contexto

O modal de settings abre e navega corretamente entre tabs. Três bugs identificados por inspecção de código:

1. **JWT `current={current}`** — bug de sintaxe no locale: `{x}` em vez de `{{x}}`.
2. **`SecuritySettingsPanel` sem props de dados** — o componente é montado com apenas `styles`, sem `authSettings` nem os handlers necessários.
3. **`activeProvider` null** — LLM panel mostra "No status available" porque `fetchActiveProvider` não é chamado no mount.

---

## BUG A — i18n: interpolação quebrada no JWT

### Causa

`react-i18next` usa `{{variavel}}` (duplo) para interpolação. Os locales usam `{variavel}` (simples), que é renderizado como texto literal.

### Arquivos: `frontend/src/i18n/locales/*.json`

Localizar a chave `current_default_values` em `en.json`, `pt.json`, `es.json` (ar e zh não têm a chave — adicionar também).

**Substituir em todos os arquivos:**
```
"current_default_values": "current={current} • default={default}"
                                    ↓
"current_default_values": "atual={{current}} • padrão={{default}}"
```

Versões por locale:
```
en.json : "current_default_values": "current={{current}} • default={{default}}"
pt.json : "current_default_values": "atual={{current}} • padrão={{default}}"
es.json : "current_default_values": "actual={{current}} • por defecto={{default}}"
ar.json : "current_default_values": "الحالي={{current}} • الافتراضي={{default}}"
zh.json : "current_default_values": "当前={{current}} • 默认={{default}}"
```

**Verificar após fix:** os valores reais devem aparecer (ex: `atual=60 • padrão=60`).

---

## BUG B — `SecuritySettingsPanel` — props ausentes

### Diagnóstico

Em `App_auth_modular.jsx` linha ~608:
```jsx
{settingsTab === 'security' && <SecuritySettingsPanel styles={styles} />}
```

O componente usa internamente `authSettings`, `applyJwtExpiryChange`, `authSettingsSaving`, `settingsLoading`, `agentSettings`, `agentSettingsSaving`, `saveAgentSettings`, `autoApprovals`, `autoApprovalsLoading`, `deleteAutoApproval`, `fetchAutoApprovals`.

### Ação

**Passo 1:** Ler `App_auth.jsx` e localizar a chamada `<SecuritySettingsPanel` (em torno da linha 4750). Copiar a lista completa de props que estão sendo passadas ali.

**Passo 2:** Verificar quais dessas props já existem no `App_auth_modular.jsx`:
- `authSettings`, `applyJwtExpiryChange`, `authSettingsSaving` — provável origem: `useSettings` hook (já importado)
- `agentSettings`, `agentSettingsSaving`, `saveAgentSettings` — verificar se `useSettings` ou hook separado
- `autoApprovals`, `autoApprovalsLoading`, `deleteAutoApproval`, `fetchAutoApprovals` — verificar origem

**Passo 3:** Para cada prop ausente no destructuring do hook, adicionar ao `const { ... } = settingsHook`.

**Passo 4:** Passar as props para o componente:
```jsx
{settingsTab === 'security' && (
  <SecuritySettingsPanel
    styles={styles}
    settingsLoading={settingsLoading}
    authSettings={authSettings}
    applyJwtExpiryChange={applyJwtExpiryChange}
    authSettingsSaving={authSettingsSaving}
    agentSettings={agentSettings}
    agentSettingsSaving={agentSettingsSaving}
    saveAgentSettings={saveAgentSettings}
    autoApprovals={autoApprovals}
    autoApprovalsLoading={autoApprovalsLoading}
    deleteAutoApproval={deleteAutoApproval}
    fetchAutoApprovals={fetchAutoApprovals}
  />
)}
```

**Regra:** não adicionar props que não existam nos hooks — reportar se alguma estiver ausente.

---

## BUG C — `LlmSettingsPanel`: `activeProvider` null no mount

### Diagnóstico

`activeProvider` vem de `useSettings` e está corretamente passado para `LlmSettingsPanel`. O problema é que `fetchActiveProvider` não é chamado automaticamente — o estado inicia como `null` e só é populado após chamada explícita.

Verificar em `useSettings.js`:
- O hook faz fetch de `activeProvider` no `useEffect` de inicialização?
- Se não, `activeProvider` permanece null até o usuário abrir o modal e acionar algo.

### Ação

**Passo 1:** Ler `frontend/src/hooks/useSettings.js`. Verificar se há um `useEffect` que chama `fetchActiveProvider` no mount.

**Se não houver:** Adicionar em `App_auth_modular.jsx`, no `useEffect` de inicialização (onde `loadConversations`, `loadSettings`, etc. são chamados):
```js
fetchActiveProvider();
```

**Se já houver mas não funcionar:** Verificar se a URL da API `/api/llm/active-provider` (ou equivalente) retorna 200 com dados. Logar o resultado no console para diagnóstico.

**Também verificar:** `setActiveLlmProviderKey` e `deleteLlmProviderKey` — não aparecem no destructuring de `llmConfigHook` em `App_auth_modular.jsx`. Se a `LlmSettingsPanel` recebe essas funções como `undefined`, os botões de gestão de chaves falham silenciosamente. Adicionar ao destructuring se existirem no hook.

---

## BUG D — Tab label "llm" em minúsculo

### Diagnóstico

O array de tabs em `App_auth_modular.jsx` linha ~563:
```jsx
[['general', t('general')], ['system', t('system')], ['llm', t('llm')], ['security', t('security')]]
```

`t('llm')` retorna a própria key `'llm'` se a chave não existir nos locales, ou retorna o valor incorreto.

### Verificar nos locales:
```bash
grep '"llm"' frontend/src/i18n/locales/pt.json
```

**Se a chave retornar apenas `"llm"`** (lowercase) ou estiver ausente, substituir a label do tab por string descritiva. Opções:
- Usar chave existente: verificar se `llm_providers`, `llm_settings`, `providers` existe
- Ou alterar o array hardcoded para:
```jsx
['llm', t('llm_settings') || 'LLM & Providers']
```
  E adicionar a chave nos locales:
```
en.json : "llm_settings": "LLM & Providers"
pt.json : "llm_settings": "LLM & Provedores"
es.json : "llm_settings": "LLM & Proveedores"
ar.json : "llm_settings": "LLM والمزودون"
zh.json : "llm_settings": "LLM 与提供商"
```

---

## Checklist de validação

- [ ] JWT exibe valores reais: ex. `atual=60 • padrão=60` (não `current={current}`)
- [ ] Security tab: toggles de agente salvam e exibem estado correto
- [ ] Security tab: JWT input funciona, Reset e Apply respondem
- [ ] Security tab: Auto-approvals lista carrega (ou mostra "No auto-approvals saved" se vazia)
- [ ] LLM tab: `activeProvider` carrega no mount sem precisar clicar em nada
- [ ] LLM tab: label do tab mostra "LLM & Provedores" (ou equivalente), não "llm"
- [ ] Console: sem erros de `undefined is not a function` nos handlers do Security/LLM panel

---

## Commit (após validação)

```bash
git add frontend/src/App_auth_modular.jsx
git add frontend/src/i18n/locales/en.json
git add frontend/src/i18n/locales/pt.json
git add frontend/src/i18n/locales/es.json
git add frontend/src/i18n/locales/ar.json
git add frontend/src/i18n/locales/zh.json
git commit -m "fix(settings): wire SecuritySettingsPanel props, fix i18n interpolation, auto-fetch activeProvider

- SecuritySettingsPanel: pass authSettings, agentSettings, autoApprovals handlers
- i18n: fix current_default_values interpolation ({x} -> {{x}}) in 5 locales
- LLM: call fetchActiveProvider on mount (no more 'No status available')
- LLM tab label: use llm_settings key instead of bare 'llm'"
```
