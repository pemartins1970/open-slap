# Manifesto — Open Slap!

## O que é

Open Slap! é um motor agêntico de código aberto, pensado para o ambiente maker.

É uma base funcional para quem quer entender, experimentar e customizar como agentes de IA operam localmente — sem depender de cloud, sem precisar de hardware caro, sem precisar de uma empresa por trás. É um ambiente de estudo, aprendizado e construção.

Roda em hardware comum. Rodo em um core i5 de 2010. Foi feito nele. Aceita LLMs locais e remotas. Chaves comerciais e gratuitas. O código está exposto porque deve estar.

---

## O que não é

Open Slap! não é um produto comercial.

Não tem SLA. Não tem suporte, nem mesmo pago. Não tem roadmap orientado por mercado. O produto segue documentado. E é isso.

Não é uma plataforma completa, dentro do que você espera comercialmente de um produto. Não tem interface para usuário final não-técnico. Não vai ter, nesta versão.

Open Slap! é um motor agêntico. O que você constrói em cima dele é responsabilidade sua — e isso é proposital.

---

## Para quem é

Para o desenvolvedor que quer entender o que acontece por baixo.

Para o maker que quer um ponto de partida honesto, sem camadas de abstração escondendo a lógica.

Para quem tem hardware de 2015 e quer rodar IA local de verdade.

Para quem quer estudar arquitetura agêntica sem pagar por isso.

Para escolas de ensino — especialmente as da rede pública — terem um ambiente de laboratório agêntico para prepararem uma nova geração de pessoas prontas para lidar, aprender os fundamentos, e pensar e trabalhar junto com as IAs. Precisamos de pessoas boas e éticas, bem formadas e preparadas para os novos desafios. O Open Slap! é um ponto de partida. Para professores, para estudantes, para quem quiser construir algo neste sentido — gratuitamente, livremente.

---

## O que você encontra aqui (v2.0)

- Motor agêntico com tool execution loop e orquestração autônoma
- 14 skills built-in com prompts estruturados (CTO, Arquiteto, Backend, Frontend, DevOps, e mais)
- Loop plan→build: CTO emite planos estruturados, orquestrador executa cada task com a skill correta
- Suporte a múltiplos providers de LLM (Gemini, Groq, OpenAI, Ollama)
- Memória persistente em SQLite com RAG e 4 fases: escrita, momentum, decay, consolidação
- Conectores ativos: GitHub (repos + issues), Google Calendar, Gmail, Google Drive
- Feedback 👍/👎 que retroalimenta cache, RAG e aprendizado do router
- MoE Router com seleção por keywords + histórico de aprovações por expert
- Projetos compartilhados entre tarefas
- Interface em 5 idiomas (PT, EN, ES, AR, ZH) com 8 temas de cor
- Onboarding para novos usuários
- 50 testes automatizados
- Código legível, comentado, sem magia negra

---

## O que não encontra aqui

- Interface polida para usuário final não-técnico
- Conectores proprietários (Salesforce, ERPs, CRMs)
- Garantias de estabilidade em produção
- Suporte técnico de qualquer tipo
- Vector search
- Multi-tenant com isolamento entre organizações

Essas camadas existem. Estão sendo construídas. Mas não aqui.

Para o seu uso pessoal, o céu é o limite. Construa o seu assistente pessoal. Existem dezenas de milhares de projetos, bons projetos, no GitHub que você pode integrar. O que quiser, como quiser.

---

## Sobre o ecossistema

Open Slap! é o motor base de uma família de soluções e produtos em desenvolvimento. Eu poderia não dividir nada dele.

Produtos comerciais derivados dele existem e existirão. Eles herdam do processo e dos conhecimentos do desenvolvimento deste core, e adicionam outras diversas camadas que não pertencem a um projeto open source — integrações proprietárias, supervisão avançada, suporte, SLA.

A existência desses produtos financia a continuidade deste.

O Open Slap! não compete com eles. Ele os fundamentou. Foi o nosso ambiente de pesquisa e testes. Que seja o de todos agora.

---

## Contribuições

São bem-vindas, com critério.

Este projeto tem uma direção. Pull requests que adicionam complexidade sem propósito claro, que introduzem dependências desnecessárias, ou que desviam do foco de motor agêntico básico serão recusados sem cerimônia.

Issues com bugs, melhorias de documentação e casos de uso reais têm prioridade.

---

## Licença

Apache 2.0.

Use, fork, estude, comercialize derivados. Só não retire os créditos.

---

## Uma nota pessoal

Este projeto nasceu de um problema real: querer construir com IA sem ser reféns de plataformas, hardware caro ou modelos fechados.

Não é o caminho mais fácil. Mas é um caminho honesto.

Se você chegou até aqui, provavelmente entende o que isso significa.

— Pê Martins

---
---

# Manifesto — Open Slap!

## What it is

Open Slap! is an open source agentic engine, built for the maker environment.

It is a functional foundation for anyone who wants to understand, experiment with, and customize how AI agents operate locally — without depending on the cloud, without needing expensive hardware, without needing a company behind it. It is an environment for study, learning, and building.

It runs on common hardware. I run it on a 2010 core i5. It was built on one. It accepts local and remote LLMs. Commercial and free API keys alike. The code is exposed because it should be.

---

## What it is not

Open Slap! is not a commercial product.

It has no SLA. No support — not even paid support. No market-driven roadmap. The project stays documented. That's it.

It is not a complete platform in the commercial sense. It has no interface for non-technical end users. It won't have one in this version.

Open Slap! is an agentic engine. What you build on top of it is your responsibility — and that is intentional.

---

## Who it's for

For the developer who wants to understand what happens underneath.

For the maker who wants an honest starting point, without layers of abstraction hiding the logic.

For anyone running 2015 hardware who wants to run local AI for real.

For anyone who wants to study agentic architecture without paying for it.

For schools — especially public schools — to have an agentic laboratory environment to prepare a new generation of people ready to engage with, learn the fundamentals of, and think and work alongside AI. We need good, ethical people, well-formed and prepared for the new challenges. Open Slap! is a starting point. For teachers, for students, for anyone who wants to build something in this direction — freely, at no cost.

---

## What you'll find here (v2.0)

- Agentic engine with tool execution loop and autonomous orchestration
- 14 built-in skills with structured prompts (CTO, Architect, Backend, Frontend, DevOps, and more)
- Plan→build loop: CTO emits structured plans, orchestrator executes each task with the right skill
- Multi-provider LLM support (Gemini, Groq, OpenAI, Ollama)
- Persistent SQLite memory with RAG and 4 phases: write, momentum, decay, consolidation
- Active connectors: GitHub (repos + issues), Google Calendar, Gmail, Google Drive
- 👍/👎 feedback that retrofeeds cache, RAG, and router learning
- MoE Router with keyword selection + per-expert approval history
- Projects shared across tasks
- Interface in 5 languages (PT, EN, ES, AR, ZH) with 8 colour themes
- Onboarding for new users
- 50 automated tests
- Readable, commented code — no black magic

---

## What you won't find here

- Polished interface for non-technical end users
- Proprietary connectors (Salesforce, ERPs, CRMs)
- Production stability guarantees
- Technical support of any kind
- Vector search 
- Multi-tenant with organisation-level data isolation

These layers exist. They are being built. Just not here.

For personal use, the sky is the limit. Build your own personal assistant. There are tens of thousands of good projects on GitHub you can integrate. Whatever you want, however you want.

---

## About the ecosystem

Open Slap! is the base engine of a family of solutions and products in development. I could have kept all of it to myself.

Commercial products derived from it exist and will exist. They inherit from the process and knowledge developed in this core, and add other layers that don't belong in an open source project — proprietary integrations, advanced supervision, support, SLA.

The existence of those products funds the continuity of this one.

Open Slap! does not compete with them. It founded them. It was our research and testing environment. Now let it be everyone's.

---

## Contributions

Welcome, with criteria.

This project has a direction. Pull requests that add complexity without clear purpose, that introduce unnecessary dependencies, or that deviate from the focus of a basic agentic engine will be declined without ceremony.

Issues with bugs, documentation improvements, and real use cases take priority.

---

## License

Apache 2.0.

Use it, fork it, study it, commercialize derivatives. Just don't remove the credits.

---

## A personal note

This project was born from a real problem: wanting to build with AI without being held hostage by platforms, expensive hardware, or closed models.

It's not the easiest path. But it's an honest one.

If you've made it this far, you probably understand what that means.

— Pê Martins
