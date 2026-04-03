# IARTES - Interactive Adaptive Recommendation for Test Execution Sequencing

Sistema de Recomendação Adaptativo para Ordenação de Casos de Teste Manuais baseado em Machine Learning.

## 📋 Sobre o Projeto

Este projeto implementa um sistema de recomendação **human-in-the-loop** que utiliza Machine Learning para ordenar casos de teste manuais de forma adaptativa, reduzindo o esforço do testador e otimizando a execução de testes.

### Principais Características

- 🤖 **Machine Learning Adaptativo**: Aprende com feedback explícito e implícito
- 🎯 **Modelagem de Estado**: Diferencia ações destrutivas de não-destrutivas
- 📊 **Grafo de Dependências**: Respeita pré e pós-condições entre testes
- 💡 **Recomendação Inteligente**: Minimiza reinicializações e tempo total
- 🔄 **Aprendizado Contínuo**: Melhora progressivamente com uso

## 🏗️ Arquitetura do Sistema

```
src/
├── models/              # Modelos de dados
│   └── test_case.py    # TestCase, Action, ExecutionFeedback, etc.
├── features/           # Extração de features
│   └── feature_extractor.py
├── recommender/        # Sistema de recomendação
│   └── ml_recommender.py
└── __init__.py

examples/               # Exemplos de uso
└── demo_basic.py

models/                # Modelos treinados salvos
```

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- pip

### Passos

1. Clone o repositório (ou extraia os arquivos)

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Crie a estrutura de diretórios:
```bash
mkdir -p models
mkdir -p src/models
mkdir -p src/features
mkdir -p src/recommender
mkdir -p examples
```

4. (Opcional) Se você já tem dados em pickle, migre para SQLite:
```bash
python migrar_pickle_para_sqlite.py
```

### 🗄️ Banco de Dados

O sistema utiliza **SQLite** para armazenar feedbacks e histórico:
- Arquivo: `iartes.db` (criado automaticamente)
- Modelo ML: continua em `models/motorola_modelo.pkl`

📘 Veja [BANCO_DE_DADOS.md](BANCO_DE_DADOS.md) para detalhes.

## 📖 Uso Básico

### 🌐 Interface Web (RECOMENDADO)

A forma mais fácil de usar o sistema é através da **interface web visual**:

```bash
python app_web.py
```

Depois acesse `http://localhost:5000` no navegador.

**Fluxo de Trabalho:**

1. **Selecione os testes** que você precisa executar hoje
2. **Solicite a recomendação** - a IA sugere a melhor ordem
3. **Aceite ou modifique** a ordem (arraste para reordenar)
4. **Execute manualmente** os testes no dispositivo
5. **Dê feedback** após cada teste (tempo, sucesso, avaliação)
6. **A IA aprende** e melhora as próximas recomendações!

📘 Veja o [GUIA_INTERFACE_WEB.md](GUIA_INTERFACE_WEB.md) para detalhes completos.

### 💻 Exemplo Programático

Execute o exemplo de demonstração:

```bash
python examples/demo_basic.py
```

### Uso Programático

```python
from src.models.test_case import TestCase, Action, ActionType, ActionImpact
from src.recommender.ml_recommender import MLTestRecommender

# 1. Criar casos de teste
test1 = TestCase(
    id="TC001",
    name="Test Login",
    description="Testa funcionalidade de login",
    priority=5,
    module="Authentication",
    actions=[
        Action(
            id="A001",
            description="Inserir credenciais",
            action_type=ActionType.CREATION,
            impact=ActionImpact.PARTIALLY_DESTRUCTIVE,
            postconditions={"user_logged_in"},
            estimated_time=5.0
        )
    ]
)

# 2. Criar recomendador
recommender = MLTestRecommender()

# 3. Obter recomendação
test_cases = [test1, test2, test3]  # Sua lista de testes
recommendation = recommender.recommend_order(test_cases)

# 4. Usar a ordem recomendada
print(f"Ordem sugerida: {recommendation.recommended_order}")
print(f"Confiança: {recommendation.confidence_score:.1%}")

# 5. Fornecer feedback após execução
from src.models.test_case import ExecutionFeedback
from datetime import datetime

feedback = ExecutionFeedback(
    test_case_id="TC001",
    executed_at=datetime.now(),
    actual_execution_time=5.2,
    success=True,
    followed_recommendation=True,
    tester_rating=5,
    required_reset=False
)

recommender.add_feedback(feedback, test_cases)

# 6. Salvar modelo treinado
recommender.save_model("models/my_recommender.pkl")
```

## 🧠 Como Funciona

### 1. Modelagem de Casos de Teste

Cada caso de teste é composto por:
- **Ações**: Passos individuais com tipo e impacto
- **Pré-condições**: Estados necessários para execução
- **Pós-condições**: Estados resultantes da execução
- **Metadados**: Prioridade, módulo, tempo estimado, etc.

### 2. Tipos de Ações

- **CREATION**: Criação de dados/estado
- **VERIFICATION**: Verificação/checagem (não destrutiva)
- **MODIFICATION**: Modificação de estado
- **DELETION**: Deleção de dados
- **NAVIGATION**: Navegação na interface

### 3. Impacto no Estado

- **NON_DESTRUCTIVE**: Não altera o estado (verificações)
- **PARTIALLY_DESTRUCTIVE**: Altera parcialmente
- **DESTRUCTIVE**: Altera completamente o estado

### 4. Sistema de Recomendação

O sistema utiliza duas estratégias:

#### Heurísticas (quando não treinado):
- Respeita dependências explícitas
- Agrupa testes do mesmo módulo
- Prioriza ações não-destrutivas
- Considera prioridades definidas

#### Machine Learning (após treinamento):
- Aprende padrões de execução bem-sucedida
- Incorpora feedback do testador
- Otimiza para minimizar tempo e reinicializações
- Adapta-se ao estilo individual do testador

### 5. Aprendizado Adaptativo

O modelo aprende através de:
- **Feedback Explícito**: Avaliações do testador (1-5 estrelas)
- **Feedback Implícito**: 
  - Tempo real vs. estimado
  - Necessidade de reinicializações
  - Se seguiu a recomendação ou não
  - Sucesso/falha da execução

## 📊 Métricas e Avaliação

O sistema rastreia:

- **Tempo Total de Execução**: Duração completa da suíte
- **Taxa de Reinicializações**: Quantas vezes o sistema precisou ser resetado
- **Taxa de Aceitação**: Percentual de recomendações seguidas
- **Carga Cognitiva**: Avaliação subjetiva do testador

## 🔧 Configuração Avançada

### Escolher Tipo de Modelo

```python
# Random Forest (padrão - bom para começar)
recommender = MLTestRecommender(model_type='random_forest')

# Gradient Boosting (mais preciso com mais dados)
recommender = MLTestRecommender(model_type='gradient_boosting')
```

### Forçar Re-treinamento

```python
# Adicionar múltiplos feedbacks
for feedback in feedback_list:
    recommender.add_feedback(feedback, test_order)

# Treinar manualmente
recommender.train()
```

## 🎯 Casos de Uso

1. **Testes de Regressão Manual**: Ordenar grandes suítes de regressão
2. **Testes Exploratórios**: Sugerir próximos testes baseado no contexto
3. **Onboarding de Testadores**: Guiar testadores iniciantes
4. **Otimização de Tempo**: Reduzir tempo total de execução

## 📈 Roadmap

- [ ] Interface web com Streamlit
- [ ] Visualização de grafos de dependências
- [ ] Suporte a testes paralelos
- [ ] Integração com ferramentas de teste (Jira, TestRail)
- [ ] Algoritmos avançados (Deep Learning, Reinforcement Learning)
- [ ] API REST para integração

## 🤝 Contribuindo

Este é um projeto de pesquisa acadêmica. Contribuições são bem-vindas!

## 📄 Licença

Este projeto foi desenvolvido como parte da pesquisa acadêmica do projeto IARTES.

## 👤 Autor

**Marcelo dos Santos Saraiva Junior**

## 🙏 Referências

- Myers et al. (2011) - The Art of Software Testing
- Yoo & Harman (2012) - Regression Testing Minimization
- Itkonen et al. (2009) - How do testers do it?

---

**Nota**: Este é um sistema em desenvolvimento ativo. Feedback e sugestões são altamente apreciados!
