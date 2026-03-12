# Sistema RAG e Armazenamento Local

## Arquitetura RAG

### Componentes Principais
- **Vector Database:** ChromaDB/Pinecone local
- **Document Store:** PostgreSQL + pgvector
- **Embedding Models:** Sentence Transformers
- **Retrieval Engine:** Hybrid search (semantic + keyword)
- **Context Manager:** MCP integration

### Fluxo RAG
```
Query → Embedding → Vector Search → Document Retrieval → Context Assembly → LLM Generation
```

## Armazenamento Local

### Estrutura de Dados
```
storage/
├── documents/          # Documentos indexados
├── vectors/           # Embeddings
├── cache/             # Cache de respostas
├── models/            # Modelos locais
└── logs/              # Logs do sistema
```

### Tecnologias
- PostgreSQL + pgvector (vetores)
- Redis (cache)
- MinIO (objetos)
- SQLite (configurações)

### Performance
- Indexação: < 1s por documento
- Retrieval: < 100ms
- Storage: 100GB base
- Backup: Automático diário
