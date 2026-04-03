# Explicação Completa: Como a IA do IARTES Funciona

**Documento de Referência Técnica e Conceitual**

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Linguagem e Tecnologias Utilizadas](#2-linguagem-e-tecnologias-utilizadas)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Comportamento da IA](#4-comportamento-da-ia)
5. [O que a IA Aprende e Como](#5-o-que-a-ia-aprende-e-como)
6. [O que a IA Precisa para Aprender](#6-o-que-a-ia-precisa-para-aprender)
7. [Modelos de Aprendizado de Máquina](#7-modelos-de-aprendizado-de-máquina)
8. [Extração de Features](#8-extração-de-features)
9. [Fluxo de Recomendação Completo](#9-fluxo-de-recomendação-completo)
10. [Explicabilidade e Auditoria](#10-explicabilidade-e-auditoria)
11. [Detecção de Anomalias](#11-detecção-de-anomalias)
12. [Persistência e Banco de Dados](#12-persistência-e-banco-de-dados)
13. [Glossário de Termos](#13-glossário-de-termos)

---

## 1. Visão Geral

O **IARTES** (Sistema de Recomendação Inteligente para Ordenação de Testes) é uma aplicação que utiliza **Inteligência Artificial** para recomendar a **ordem ideal de execução** de casos de teste em dispositivos móveis (como Motorola). O objetivo principal é:

- **Minimizar reinicializações** do dispositivo durante os testes
- **Respeitar dependências** entre testes (ex.: cadastrar impressão digital antes de testar desbloqueio)
- **Maximizar eficiência** (tempo total, agrupamento por módulo)
- **Priorizar testes de maior risco** de falha para executá-los quando o contexto está estável
- **Personalizar recomendações** para cada testador com base em seu histórico

A IA **não executa** os testes. Ela **ordena** os testes selecionados pelo usuário de forma otimizada e explica o raciocínio por trás dessa ordenação.

---

## 2. Linguagem e Tecnologias Utilizadas

### Linguagem Principal
- **Python 3** — linguagem de programação utilizada em todo o backend e lógica de IA

### Bibliotecas de Machine Learning
- **scikit-learn** — Random Forest, Gradient Boosting, Isolation Forest
- **numpy** — operações numéricas e vetoriais
- **pandas** — manipulação de dados

### Web e Persistência
- **Flask** — framework web para a interface e APIs
- **SQLite** — banco de dados para usuários, feedbacks, modelos personalizados

### Outras Tecnologias
- **pickle** — serialização de modelos treinados
- **HTML/CSS/JavaScript** — interface do usuário (frontend)
- **vis.js** — visualização em árvore das dependências

---

## 3. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USUÁRIO (Testador)                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTERFACE WEB (Flask + Frontend)                  │
│  - Seleção de testes  - Visualização da ordem  - Envio de feedback   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│              RECOMENDADOR PERSONALIZADO (PersonalizedMLRecommender)  │
│  - Modelo Global (compartilhado)  - Modelo por Usuário (individual)  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
           ┌────────────────────────┼────────────────────────┐
           ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Ordenação Base   │    │ Contexto +       │    │ Repair Lógico    │
│ Heurística ou ML │    │ Risco de Falha   │    │ (Topological     │
│                  │    │ (Bayesiano)      │    │  Sort)           │
└──────────────────┘    └──────────────────┘    └──────────────────┘
           │                        │                        │
           └────────────────────────┼────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│           EXPLICABILIDADE (RecommendationExplainer)                  │
│  - Fatores  - Importância de features  - Explicação textual          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BANCO DE DADOS (SQLite)  +  MODELOS (pickle)                        │
│  - Usuários  - Feedbacks  - Modelos por usuário  - Estatísticas      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Comportamento da IA

### 4.1 Quando o Modelo NÃO Está Treinado (ou uso de heurísticas)

Neste caso, a IA usa **apenas regras lógicas (heurísticas)**:

1. **Resolve dependências** — só coloca um teste na ordem quando todos os testes dos quais ele depende já foram incluídos
2. **Entre testes elegíveis**, ordena por:
   - **Prioridade** (maior primeiro)
   - **Módulo** (agrupa testes do mesmo módulo)
   - **Não destrutivo antes de destrutivo** (testes que não alteram estado vêm primeiro)
   - **Tempo estimado** (mais rápidos antes)

### 4.2 Quando o Modelo Está Treinado

1. **Ordenação base** — usa as mesmas heurísticas acima
2. **Refinamento por ML** — aplica uma **busca local** trocando pares de testes adjacentes e avaliando o score previsto pelo modelo. Se o score melhorar, mantém a troca
3. **Reordenação contextual** — aplica risco de falha e afinidade do usuário para ajustar a ordem
4. **Repair lógico** — garante que a ordem final sempre respeita dependências (ordenação topológica)
5. **Hierarquia** — quando existem testes pai/filho (`parent_test_id`, `child_test_ids`), usa uma ordenação hierárquica especial que agrupa testes com caminho compartilhado

### 4.3 Personalização por Usuário

O sistema mantém:
- **Modelo global** — treinado com feedbacks de todos os usuários
- **Modelo por usuário** — treinado apenas com feedbacks daquele usuário

O **peso de personalização** varia com o nível de experiência cadastrado:
- **Iniciante:** 20% personalizado, 80% global
- **Intermediário:** 50% / 50%
- **Avançado:** 70% personalizado, 30% global
- **Expert:** 85% personalizado, 15% global

Se o modelo do usuário não estiver treinado (< 5 amostras), usa apenas o modelo global.

---

## 5. O que a IA Aprende e Como

### 5.1 Objetivo do Aprendizado

A IA **não** classifica testes individualmente. Ela aprende a **avaliar a qualidade de uma ordenação completa**. Ou seja, dado um conjunto de testes numa certa ordem, o modelo prevê um **score** (quanto maior, melhor a ordem).

### 5.2 Tipo de Aprendizado

- **Aprendizado supervisionado** — cada amostra de treinamento é uma ordenação executada + feedback humano (sucesso/falha, reset, rating, etc.)
- **Target (y):** score de qualidade calculado por uma **função objetivo fixa**
- **Features (X):** estatísticas agregadas da ordenação (número de testes, tempo total, transições compatíveis, etc.)

### 5.3 Função Objetivo (Cálculo do Score)

O score é calculado deterministicamente e usado como "resposta correta" no treinamento:

- **Base:** 100 pontos
- **Penalidades:**
  - Quebra de dependência: -20 por quebra
  - Teste destrutivo seguido de não destrutivo no mesmo módulo: -5
  - Reset necessário no feedback: -15
  - Falha no feedback: -10
- **Bônus:**
  - Transição compatível de estado (pós do teste i satisfaz pré do teste i+1): +10 × proporção
  - Mesmo módulo consecutivo: +3
  - Sucesso no feedback: +10
  - Seguiu a recomendação: +5
  - Rating (1–5): (rating - 3) × 5

O score final é limitado a ≥ 0. O modelo aprende a **prever esse score** a partir das features da ordem.

### 5.4 Como o Treinamento Ocorre

1. Usuário executa testes e envia **feedback** (sucesso/falha, tempo real, rating, reset, se seguiu a ordem)
2. O sistema calcula o **score da ordem executada** usando a função objetivo acima
3. Gera uma **amostra de treinamento** (features da ordem + score)
4. Acumula no `training_data` (listas X e y)
5. **Retreinamento automático:**
   - Modelo global: a cada 10 novos feedbacks
   - Modelo do usuário: quando atinge 5+ amostras

---

## 6. O que a IA Precisa para Aprender

### 6.1 Requisitos Mínimos

- **Mínimo 5 amostras** — para treinar o modelo do usuário
- **Feedback humano** — após cada execução (ou conjunto de execuções):
  - Sucesso ou falha
  - Tempo real de execução
  - Rating (1–5)
  - Se precisou de reset
  - Se seguiu a ordem recomendada

### 6.2 Dados que Alimentam o Aprendizado

- **Ordem efetivamente executada** — quais testes e em qual ordem
- **Resultado da execução** — sucesso/falha por teste
- **Tempo real** — quanto tempo cada teste levou
- **Reset** — se foi necessário reiniciar o dispositivo
- **Rating** — avaliação do testador (1–5)
- **Seguiu recomendação** — se o usuário executou na ordem sugerida

Quanto **mais feedbacks** o sistema recebe, **melhor** a IA se torna nas recomendações futuras.

---

## 7. Modelos de Aprendizado de Máquina

### 7.1 Recomendador Base (MLTestRecommender)

- **Algoritmos:** Random Forest ou Gradient Boosting (regressão)
- **Random Forest:** 100 árvores, profundidade máxima 10
- **Gradient Boosting:** 100 estimadores, profundidade 5, learning rate 0,1
- **Pré-processamento:** StandardScaler (normalização das features)
- **Saída:** valor contínuo (score previsto para a ordenação)

### 7.2 Ensemble Recommender (opcional)

- Combina Random Forest, Gradient Boosting e opcionalmente MLP (Rede Neural)
- Usa `VotingRegressor` para combinar as previsões
- Pesos típicos: 0,4 / 0,4 / 0,2

### 7.3 Predição de Falha (Risco)

- **Modelo Bayesiano** com prior Beta
- Fórmula: P(falha) ≈ (falhas + α) / (total + α + β)
- Combina estatísticas do **usuário** e **globais**
- Resultado: `risk_map` (test_id → probabilidade de falha)
- Uso: priorizar testes de maior risco no início da execução

---

## 8. Extração de Features

### 8.1 Features por Teste (individuais)

- Prioridade, número de ações, tempo estimado
- Taxa de sucesso, vezes executado
- Contagem por tipo de ação (destrutivas, criação, verificação, etc.)
- Número de pré/pós-condições
- Número de dependências
- Nível hierárquico (tree_level), contexto preservador, teardown

### 8.2 Features para Score de Ordenação (treinamento)

As amostras usam **estatísticas da sequência completa**:

- Número de testes
- Tempo total estimado
- Prioridade média
- Número de testes destrutivos
- Número de **transições compatíveis** (pós do teste i intersecta pré do teste i+1)
- Número de **transições mesmo módulo**
- Features hierárquicas (grupos de caminho compartilhado, violações de hierarquia)

---

## 9. Fluxo de Recomendação Completo

1. **Entrada:** testes selecionados pelo usuário
2. **Recomendador base:** gera ordem inicial (heurística ou ML)
3. **Contexto e risco:** calcula `risk_map` e `affinity_map` do usuário
4. **Reordenação contextual ou hierárquica:**
   - Se há hierarquia (parent_test_id, child_test_ids): `_hierarchical_reorder`
   - Senão: `_contextual_reorder` (respeita dependências inferidas, risco, afinidade)
5. **Repair lógico:** `_repair_order_for_logic` — ordenação topológica para garantir consistência
6. **Explicabilidade:** gera fatores e explicação textual
7. **Saída:** ordem final + detalhes + explicação + tempo estimado + resets estimados

---

## 10. Explicabilidade e Auditoria

### 10.1 RecommendationExplainer

Quando o modelo está treinado:
- Usa **importância de features** do Random Forest
- Calcula **scores por teste** (bonificação por prioridade, mesmo módulo, compatibilidade)
- Gera **explicação textual** em linguagem natural
- Compara com ordens alternativas (tempo, resets)

### 10.2 Quando o Modelo Não Está Treinado

- Usa função heurística que analisa a ordem e produz fatores semânticos
- Explica: agrupamento por módulo, prioridade, destrutivos, tempo

---

## 11. Detecção de Anomalias

### 11.1 AnomalyDetector

- **Algoritmo:** Isolation Forest (scikit-learn)
- **Objetivo:** identificar execuções atípicas nos feedbacks
- **Features:** tempo real, rating, sucesso, reset, seguiu recomendação
- **Uso:** auditoria, sinalizar períodos ou testes problemáticos

---

## 12. Persistência e Banco de Dados

### 12.1 SQLite

- **Usuários** — login, nível de experiência
- **Feedbacks** — execuções, sucesso, tempo, rating, reset
- **Modelos por usuário** — serializados em pickle (blob)
- **Estatísticas** — agregações para risco e afinidade

### 12.2 Modelos

- **Modelo global:** arquivo `.pkl` (ex.: `motorola_modelo.pkl`)
- **Modelos por usuário:** armazenados no banco na tabela `user_models`

---

## 13. Glossário de Termos

| Termo | Significado |
|-------|-------------|
| **Dependência** | Um teste B depende de A se A deve ser executado antes de B |
| **Pré-condição** | Estado que um teste precisa para executar (ex.: `fingerprint_enrolled`) |
| **Pós-condição** | Estado que um teste deixa após executar (ex.: `device_locked`) |
| **Teste destrutivo** | Teste que altera significativamente o estado do sistema |
| **Reset** | Reinicialização do dispositivo (necessária quando pré-condições não são satisfeitas) |
| **parent_test_id** | ID do teste "pai" na hierarquia (ex.: MOTO_SEC_001 é pai de MOTO_SEC_002) |
| **context_preserving** | Teste que não altera o contexto para testes posteriores |
| **teardown_restores** | Teste que restaura o estado anterior ao finalizar |
| **Topological sort** | Ordenação que respeita dependências (grafo acíclico dirigido) |
| **Risk_map** | Mapa de probabilidade de falha por teste |
| **Affinity_map** | Afinidade do usuário por módulo (baseada em histórico de sucesso) |

---

## Resumo Executivo

A IA do IARTES é um **sistema híbrido** que combina:
- **Regras lógicas** (heurísticas, dependências, topological sort)
- **Machine Learning** (Random Forest / Gradient Boosting para prever qualidade de ordens)
- **Bayesianos** (predição de risco de falha)
- **Explicabilidade** (importância de features, fatores qualitativos)
- **Personalização** (modelo global + modelo por usuário)
- **Feedback contínuo** (aprendizado com cada execução)

Ela **melhora com o uso**: quanto mais o testador executa e envia feedback, melhores se tornam as recomendações futuras.
