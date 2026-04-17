# IARTES — Interactive Adaptive Recommendation for Test Execution Sequencing

Sistema de apoio à **ordenação e consolidação de casos de teste manuais**. O núcleo combina **LLM** (ou heurísticas locais) com **estruturas de prefixo** (trie) para sugerir uma **sequência única de passos** que reutiliza trabalho comum entre testes, marca **onde cada caso é validado** e calcula **métricas** de redução de passos e de “custo” operacional (re-setups, troca de contexto, etc.).

Desenvolvido no contexto de pesquisa acadêmica em recomendação adaptativa para execução de testes.

---

## O que o sistema faz

1. **Entrada**: suíte de casos de teste, cada um com uma lista ordenada de passos (texto livre).
2. **Normalização**: agrupa passos semanticamente equivalentes (via LLM ou provedor local), com **cache persistente** no banco.
3. **Classificação**: identifica tipo de passo (verificação vs. ação) e se é **destrutivo** ao estado, também com cache.
4. **Reordenação dos casos**: reorganiza a ordem dos testes para **maximizar prefixos compartilhados** antes do merge.
5. **Grafo / trie**: constrói estrutura de prefixos e **merge** de sufixos compartilhados.
6. **Otimização**: gera a **sequência linear otimizada** (DFS) e marca **pontos de validação** por caso de teste.
7. **Métricas**: redução percentual, passos eliminados, re-setups, trocas de contexto, profundidade de merge, entre outras.

O resultado pode ser inspecionado na **interface web**, exportado (JSON/CSV) e comparado entre **provedores de LLM** no modo benchmark.

---

## Arquitetura do repositório

```
NOVO-PROJETO-IARTES/
├── app.py                 # Aplicação Flask (API + páginas HTML)
├── config.py              # Carrega variáveis de ambiente (.env)
├── requirements.txt
├── .env.example           # Modelo de configuração (copiar para .env)
├── data/
│   └── iartes.db          # SQLite (criado automaticamente)
├── templates/             # index, benchmark, knowledge_base
├── static/                # CSS/JS da interface
├── test_suites/           # Exemplos de texto para scripts CLI
├── src/
│   ├── models/
│   │   └── test_case.py   # TestCase, Step, OptimizationResult, …
│   ├── parser/
│   │   └── input_parser.py  # JSON, CSV/XLSX, formulário, texto livre
│   ├── database/
│   │   └── db.py          # SQLite: suítes, runs, cache/KB
│   ├── engine/
│   │   ├── pipeline.py    # Orquestra o fluxo completo
│   │   ├── normalizer.py
│   │   ├── classifier.py
│   │   ├── reorder.py
│   │   ├── graph_builder.py
│   │   ├── optimizer.py
│   │   ├── marker.py
│   │   ├── metrics.py
│   │   ├── cache.py       # StepCache → tabelas de KB no SQLite
│   │   ├── benchmark.py
│   │   └── export.py
│   └── llm/
│       ├── factory.py     # create_llm_provider()
│       ├── base.py
│       ├── local_provider.py   # Heurísticas sem API externa
│       ├── openai_provider.py
│       └── gemini_provider.py
├── run_test.py            # Exemplo: pipeline em arquivo .txt
├── run_test_pt.py         # Variante PT
├── run_benchmark.py       # Compara providers na linha de comando
├── run_benchmark_mini.py
└── test_api.py            # Testes da API (se aplicável)
```

---

## Pré-requisitos

- **Python 3.10+** recomendado (o projeto roda em ambientes com 3.8+, desde que dependências instalem).
- **pip**

---

## Instalação

```bash
cd NOVO-PROJETO-IARTES
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Dependências principais: `flask`, `openai`, `google-generativeai`, `pandas`, `openpyxl`, `python-dotenv`.

---

## Configuração

1. Copie o modelo de ambiente:

   ```bash
   copy .env.example .env
   ```
   (Em Linux/macOS: `cp .env.example .env`.)

2. Edite `.env`:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `LLM_PROVIDER` | `local`, `openai` ou `gemini` (também aceita `google` como alias de Gemini) | `local` |
| `OPENAI_API_KEY` | Chave da API OpenAI | vazio |
| `OPENAI_MODEL` | Modelo OpenAI | `gpt-4o-mini` |
| `GEMINI_API_KEY` | Chave Google AI (Gemini) | vazio |
| `GEMINI_MODEL` | Modelo Gemini | `gemini-2.5-flash` |
| `LLM_TIMEOUT_S` | Timeout (segundos) para cada chamada de LLM | `45` |
| `FLASK_DEBUG` | `true` / `false` | `true` |
| `FLASK_PORT` | Porta HTTP | `5000` |

**Segurança:** não commite o arquivo `.env` nem chaves em repositório público. Use apenas `.env.example` como referência.

### Provedores

- **`local`**: não exige API; usa heurísticas (verbos, similaridade de texto, etc.) — útil para desenvolvimento e testes rápidos.
- **`openai`** e **`gemini`**: exigem chave configurada; melhor qualidade semântica na normalização/classificação.

No **benchmark** automático (sem lista explícita de providers), entram `local` e todos os provedores para os quais existir API key configurada.

---

## Como executar

### Interface web (forma recomendada)

```bash
python app.py
```

Abra no navegador:

- **`http://127.0.0.1:5000/`** — envio de casos de teste e visualização do resultado otimizado.
- **`http://127.0.0.1:5000/benchmark`** — comparação entre provedores na mesma suíte.
- **`http://127.0.0.1:5000/knowledge-base`** — inspeção da base de conhecimento (normalizações e classificações em cache).

A porta segue `FLASK_PORT` no `.env`.

### Scripts de linha de comando

Exemplos incluídos no repositório:

```bash
python run_test.py              # Pipeline com suite em test_suites/suite_grande_avaliacao.txt
python run_test_pt.py           # Variante em português
python run_benchmark.py         # Benchmark local vs OpenAI (requer chave OpenAI)
```

---

## API HTTP (resumo)

Base: `http://127.0.0.1:5000` (ajuste a porta se necessário).

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Página principal |
| GET | `/benchmark` | Página de benchmark |
| GET | `/knowledge-base` | Página da base de conhecimento |
| POST | `/api/optimize` | Executa o pipeline com o `LLM_PROVIDER` do `.env` |
| POST | `/api/benchmark` | Mesma entrada que optimize; corpo JSON opcional: `"providers": ["local", "openai", "gemini"]` |
| GET | `/api/history` | Histórico de execuções |
| GET | `/api/suites` | Lista de suítes salvas |
| GET | `/api/export/result/<run_id>?format=json\|csv` | Exporta resultado de uma execução |
| GET | `/api/export/metrics/<run_id>` | Exporta métricas em CSV |
| GET | `/api/export/benchmark/<suite_id>` | CSV comparativo de um benchmark por suíte |
| GET | `/api/knowledge-base` | JSON com normalizações e classificações (limite interno) |
| GET | `/api/knowledge-base/stats` | Estatísticas da KB |
| DELETE | `/api/knowledge-base` | Limpa toda a base de conhecimento (cache LLM no SQLite) |

### Formatos de entrada (`POST` optimize / benchmark)

O corpo pode ser **JSON** ou **multipart/form-data** (upload de arquivo).

**Campo `input_type`:**

- **`form`** (padrão em JSON): `data` = lista de objetos `{ "id", "name", "steps": ["...", ...] }`.
- **`text`**: `data` = string em texto livre; cabeçalhos de caso reconhecidos por padrões como `TEST-001`, `TESTE-1`, `TC-01`, `# Título`, etc. (ver `parse_free_text` em `src/parser/input_parser.py`).
- **`file`**: envio de arquivo `.json`, `.csv`, `.xlsx`/`.xls` ou texto; o parser deduz o formato pela extensão.

Para **multipart**, use `input_type=file` e o campo de arquivo `file`.

---

## Banco de dados (SQLite)

Arquivo: **`data/iartes.db`** (pasta `data/` criada automaticamente).

Tabelas principais:

- **`suites`**: suítes de teste salvas (metadados + JSON dos casos).
- **`optimization_runs`**: cada execução (provedor, resultado, métricas, tempo em ms).
- **`normalization_cache`** / **`classification_cache`**: cache de normalização e classificação por provedor, reutilizado entre execuções (**knowledge base**). A UI e a API permitem inspecionar e limpar esses dados.

Modo WAL e chaves estrangeiras estão habilitados em `src/database/db.py`.

---

## Pipeline (referência rápida)

Implementado em `src/engine/pipeline.py` — função `run_optimization_pipeline`:

1. Normalizar passos (LLM + cache)  
2. Classificar passos (LLM + cache)  
3. Reordenar casos para merge de prefixo  
4. Construir trie  
5. Otimizar sequência  
6. Construir resultado e árvore para visualização  
7. Calcular métricas  

---

## Métricas (visão geral)

Entre os indicadores expostos no JSON de resultado (e nas exportações) estão, por exemplo:

- passos originais vs. otimizados, eliminados e **redução %**  
- verificações e ações detectadas, passos destrutivos  
- **re-setups** e **trocas de contexto**  
- profundidade de merge (máxima e média)  
- identificadores normalizados e grupos de equivalência  

Rótulos amigáveis em português aparecem nas exportações de benchmark.

---

## Testes

Se existir `test_api.py` ou outros testes no projeto, execute conforme a ferramenta que você usar, por exemplo:

```bash
pytest test_api.py
```

(Instale `pytest` se ainda não estiver no ambiente.)

---

## Solução de problemas

- **Erro de provider**: confira `LLM_PROVIDER` e se a API key do provedor está definida para `openai` / `gemini`.
- **Porta em uso**: altere `FLASK_PORT` no `.env`.
- **Entrada vazia**: verifique `input_type` e se casos têm `id` e pelo menos um passo (regras do parser).
- **Benchmark sem providers**: é necessário pelo menos um provedor válido; com chaves ausentes, só `local` pode estar disponível.

---

## Licença e autoria

Projeto de pesquisa acadêmica — **IARTES**.

**Autor:** Marcelo dos Santos Saraiva Junior

---

## Referências sugeridas (contexto de testes e priorização)

- Myers, S. et al. — *The Art of Software Testing*  
- Yoo, S. & Harman, M. — *Regression Testing Minimization*  
- Itkonen, J. et al. — *How do testers do it?*

---

*README alinhado à implementação atual (`app.py`, `src/engine`, `src/llm`, SQLite em `data/`). Atualize este arquivo se rotas, variáveis de ambiente ou o pipeline mudarem.*
