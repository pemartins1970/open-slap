# Open Slap! — Spec B-09: "Salvar Informações" → SOUL Extract & Save
**Data:** 2026-06-09  
**Decisões de produto confirmadas:**
- Extração: heurística/regex (MVP) — LLM extraction é escopo do Chronicle
- Botão: universal em toda mensagem assistant completa (sem mudança de visibilidade)
- Feedback: silencioso — apenas "Salvo ✓" / "Saved" no botão

---

## Contexto

O botão "Salvar informações" aparece em toda mensagem assistant completa. Ao clicar, o frontend envia o texto da mensagem para `POST /api/padxml/save_message`, que retorna 501. O endpoint correto deveria extrair campos de perfil do texto e persistir no sistema SOUL (`user_soul` + `user_soul_events`). O nome da rota é legado sem relação com PadXML.

---

## Escopo da mudança

### 1. Backend — novo endpoint

**Rota nova:** `POST /api/soul/extract_and_save`  
**Rota antiga:** `POST /api/padxml/save_message` → substituir o stub 501 por redirecionamento 308 para a nova rota (preserva compatibilidade caso haja chamadas não mapeadas)

**Contrato:**

Request:
```json
{
  "conversation_id": 123,
  "local_message_id": "msg-id",
  "message_id": 456,
  "content": "texto completo da mensagem assistant"
}
```

Response (sucesso):
```json
{
  "ok": true,
  "fields_extracted": ["name", "programming_language"]
}
```

Response (nenhum campo extraído):
```json
{
  "ok": true,
  "fields_extracted": []
}
```

`ok: true` mesmo quando nada é extraído — o botão fica "Salvo" de qualquer forma. O frontend não usa `fields_extracted` agora, mas o campo é útil para debug e para o Chronicle futuramente.

Response (erro):
```json
{
  "ok": false,
  "error": "descrição"
}
```

---

### 2. Backend — extração heurística

A mensagem recebida é do **assistant** — contém o eco do que o usuário disse, não a fala direta. Os padrões devem refletir isso.

```python
import re
from typing import Optional

KNOWN_PROGRAMMING_LANGUAGES = {
    "python", "javascript", "typescript", "java", "rust", "go", "golang",
    "ruby", "php", "c++", "c#", "swift", "kotlin", "scala", "r",
    "haskell", "elixir", "clojure", "dart", "lua", "perl", "bash",
}

def extract_soul_fields(text: str) -> dict[str, str]:
    """
    Extrai campos SOUL do texto de uma mensagem assistant.
    Retorna apenas campos extraídos com confiança suficiente.
    """
    fields = {}
    text_lower = text.lower()

    # --- name ---
    # Padrões: "Olá, Pê!", "seu nome é Pê", "chamo-me Pê", "nome: Pê"
    name_patterns = [
        r"olá[,\s]+([A-ZÀ-Ÿ][a-zà-ÿ]{1,30})[\s!,\.]",
        r"seu nome é ([A-ZÀ-Ÿ][a-zà-ÿ]{1,30})",
        r"nome[:\s]+([A-ZÀ-Ÿ][a-zà-ÿ]{1,30})",
        r"hi[,\s]+([A-Z][a-z]{1,30})[\s!,\.]",     # EN
        r"your name is ([A-Z][a-z]{1,30})",          # EN
    ]
    for pattern in name_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            fields["name"] = m.group(1).strip()
            break

    # --- programming_language ---
    # Padrões: "linguagem de programação é Python", "trabalha com Python",
    #          "usa Python", "sua linguagem principal é Python"
    lang_trigger_patterns = [
        r"linguagem de programação[^é]*é\s+(\w[\w+#]*)",
        r"linguagem principal[^é]*é\s+(\w[\w+#]*)",
        r"trabalha(?:ndo)? com\s+(\w[\w+#]*)",
        r"usa\s+(\w[\w+#]*)\s+(?:como|para|em)",
        r"programando em\s+(\w[\w+#]*)",
        r"programming language[^i]*is\s+(\w[\w+#]*)",  # EN
        r"works? with\s+(\w[\w+#]*)",                   # EN
        r"uses?\s+(\w[\w+#]*)\s+(?:as|for|in)",         # EN
    ]
    for pattern in lang_trigger_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().lower().rstrip(".,;")
            if candidate in KNOWN_PROGRAMMING_LANGUAGES:
                fields["programming_language"] = m.group(1).strip().rstrip(".,;")
                break

    # Fallback: linguagem mencionada sem trigger, apenas se na whitelist
    if "programming_language" not in fields:
        for lang in KNOWN_PROGRAMMING_LANGUAGES:
            # Evitar falsos positivos: "R" sozinho, "Go" em "going", etc.
            if lang in ("r", "go"):
                pattern = rf"\b{re.escape(lang)}\b"
                if re.search(pattern, text_lower):
                    fields["programming_language"] = lang.capitalize()
                    break
            else:
                if lang in text_lower:
                    fields["programming_language"] = lang.capitalize()
                    break

    return fields
```

**Campos extraídos neste MVP:** `name`, `programming_language`  
**Campos não extraídos agora** (escopo Chronicle/LLM): `interests`, `goals`, `learning_style`, `education`, `audience`, `notes`

---

### 3. Backend — persistência no SOUL

Usar as APIs SOUL existentes (`db.py:2453-2498`):

```python
async def save_to_soul(user_id: int, fields: dict, source_content: str):
    """
    Persiste campos extraídos no SOUL do usuário.
    Cada campo extraído gera um soul_event para rastreabilidade.
    """
    if not fields:
        return

    # Upsert no perfil
    soul_update = {}
    if "name" in fields:
        soul_update["name"] = fields["name"]
    if "programming_language" in fields:
        # Chave de primeira classe no JSON soul_data
        soul_update["programming_language"] = fields["programming_language"]

    if soul_update:
        upsert_user_soul(user_id, soul_update)

    # Evento para histórico
    # NOTA: append_soul_event() aceita apenas (user_id, source, content)
    # salience/confidence/decay_rate usam defaults da tabela (0.5/0.8/0.05)
    for field, value in fields.items():
        append_soul_event(
            user_id=user_id,
            source="assistant_message_save",
            content=f"{field}: {value}",
        )

**DECISÃO:** `programming_language` é chave de primeira classe no JSON `soul_data`,
não armazenado em `notes`. Adicionar à lista `ordered_fields` em `_build_soul_markdown()`.

---

### 4. Frontend — mudança mínima

Único ajuste necessário: atualizar a URL do endpoint em `App_auth.jsx:3119-3142`:

```javascript
// DE:
const response = await fetch('/api/padxml/save_message', { ... })

// PARA:
const response = await fetch('/api/soul/extract_and_save', { ... })
```

Nenhuma outra mudança no frontend. O comportamento visual (`savedInfoLocalMsgIds`, "Salvo ✓", botão disabled) permanece idêntico.

---

## Acceptance criteria

- [ ] `POST /api/soul/extract_and_save` retorna `{ok: true}` para mensagem com nome e linguagem
- [ ] `POST /api/padxml/save_message` retorna 308 redirect para nova rota (não mais 501)
- [ ] Campo `name` extraído de "Olá, Pê!" e persistido em `user_soul`
- [ ] Campo `programming_language` extraído de "linguagem de programação principal é Python" e persistido
- [ ] Mensagem sem dados de perfil retorna `{ok: true, fields_extracted: []}` sem erro
- [ ] Botão "Salvar informações" fica "Salvo ✓" e disabled após clique bem-sucedido (comportamento anterior mantido)
- [ ] Clicar em mensagem que não contém dados de perfil não gera erro — silencioso

---

## Casos de teste formais

### Teste 1 — Extração de nome
```
Input: "Olá, Pê! É um prazer saber mais sobre você."
Esperado: fields_extracted = ["name"], user_soul.name = "Pê"
```

### Teste 2 — Extração de linguagem
```
Input: "Registrei que sua linguagem de programação principal é Python."
Esperado: fields_extracted = ["programming_language"], soul_event registrado
```

### Teste 3 — Extração de ambos
```
Input: "Olá, Pê! Registrei que você trabalha com Python."
Esperado: fields_extracted = ["name", "programming_language"]
```

### Teste 4 — Nenhum campo extraído
```
Input: "Aqui está o código que você pediu: def hello(): pass"
Esperado: {ok: true, fields_extracted: []}
Verificar: nenhum soul_event criado
```

### Teste 5 — Falso positivo de linguagem (texto em português com "R")
```
Input: "Para resolver isso, vou precisar de mais contexto."
Esperado: "r" em "resolver" e "Para" NÃO extrai "R" como linguagem
```

### Teste 6 — Idempotência
```
1. Salvar mesma mensagem duas vezes
2. Verificar: user_soul.name não duplicado
3. Verificar: soul_events registra duas entradas (rastreabilidade)
```

### Teste 7 — Rota antiga retorna 308
```
POST /api/padxml/save_message com payload válido
Esperado: HTTP 308, Location: /api/soul/extract_and_save
```

---

## Riscos

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Schema `user_soul` não tem campo para `programming_language` | Média | Verificar antes; usar `notes` como fallback documentado |
| Falso positivo: linguagens curtas ("R", "Go") em texto comum | Média | Padrão `\b` obrigatório para nomes curtos; fallback só com trigger |
| Mensagem assistant muito longa causa timeout de extração | Baixa | Regex é O(n) — não é problema; truncar input em 5000 chars como precaução |
| `upsert_user_soul` / `append_soul_event` têm assinatura diferente da esperada | Média | Verificar assinatura em `db.py:2453-2498` antes de implementar |

---

## Fora do escopo deste item

- Extração de `interests`, `goals`, `learning_style`, `education` → Chronicle/LLM
- Feedback visual mostrando o que foi extraído → melhoria futura de UX
- Visibilidade condicional do botão → melhoria futura de UX
- Revisão do perfil SOUL pelo usuário → já existe via `PUT /api/soul` em settings
