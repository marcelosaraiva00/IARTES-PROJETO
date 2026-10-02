#!/usr/bin/env python3
"""Responde o questionário do professor (Perguntas_Banca_Simulação.pdf) e gera PDF."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

FONT_NAME = "BancaFont"
for fp in [
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\calibri.ttf"),
]:
    if fp.exists():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(fp)))
        break
else:
    FONT_NAME = "Helvetica"


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Heading1"], fontName=FONT_NAME,
            fontSize=15, leading=19, spaceAfter=10, textColor=colors.HexColor("#1a1a2e"),
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName=FONT_NAME,
            fontSize=9.5, leading=13, textColor=colors.HexColor("#555555"), spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Heading2"], fontName=FONT_NAME,
            fontSize=11, leading=14, spaceBefore=12, spaceAfter=6,
            textColor=colors.HexColor("#16213e"),
        ),
        "qa": ParagraphStyle(
            "qa", parent=base["Normal"], fontName=FONT_NAME,
            fontSize=10, leading=14, spaceBefore=8, spaceAfter=4,
        ),
        "ans": ParagraphStyle(
            "ans", parent=base["Normal"], fontName=FONT_NAME,
            fontSize=10, leading=14, spaceAfter=10, leftIndent=12,
            alignment=TA_JUSTIFY, textColor=colors.HexColor("#222222"),
        ),
    }


QA = [
    ("Capítulo 1 — Introdução", [
        (
            "Vocês afirmam que existe uma lacuna na literatura sobre ordenação de testes manuais. "
            "Como chegaram a essa conclusão? Existe algum estudo que mostre explicitamente essa lacuna?",
            "A conclusão foi construída em três movimentos. Primeiro, pela revisão orientada do "
            "estado da arte (Capítulo 3): revisões sistemáticas e surveys recentes — como Yoo e Harman "
            "(2012) e Fernandes e Martins (2025) — concentram-se em regressão automatizada e na "
            "granularidade do caso de teste, não na consolidação de passos em suítes manuais. Segundo, "
            "pela distinção conceitual com TSP/TSR (§1.1): as abordagens clássicas pressupõem executor "
            "automatizado, independência entre casos e métricas como APFD, o que não cobre redundância "
            "operacional entre passos nem o papel do testador como decisor. Terceiro, pela síntese em "
            "três evidências convergentes no §1.2. Não há um único artigo que declare literalmente "
            "\"lacuna em ordenação manual por passos com trie/DAG\"; a lacuna é inferida pelo conjunto "
            "da literatura e explicitada no posicionamento (§3.7). Fernandes e Martins (2025), por "
            "exemplo, indicam indiretamente que quase todas as técnicas avaliadas pressupõem ambiente "
            "automatizado — o que reforça, mas não nomeia com as mesmas palavras, o nicho do IARTES."
        ),
        (
            "Por que optar por atuar na ordenação de casos de teste manuais em vez de investir "
            "diretamente na automação dos testes?",
            "Porque automação plena não é viável nem economicamente favorável em diversos cenários "
            "(usabilidade, inspeção visual, fluxos subjetivos, testes exploratórios iniciais), conforme "
            "§1.1 e §2.2. O problema tratado não substitui a automação: complementa a execução manual "
            "onde o humano permanece central. Investir só em automação deixaria sem suporte as suítes "
            "mantidas em texto livre (planilhas, documentos, ferramentas de gestão) e o esforço cognitivo "
            "da reorganização tácita que testadores experientes já fazem. O IARTES formaliza e automatiza "
            "a análise estrutural e a recomendação da ordem; a execução física continua manual (HITL)."
        ),
        (
            "Qual foi o principal problema científico investigado e por que ele ainda não havia sido "
            "resolvido pelas abordagens tradicionais?",
            "Problema central (§1.2): como projetar um sistema que receba suíte manual em texto livre, "
            "identifique passos semanticamente equivalentes, avalie impacto de cada passo no contexto e "
            "produza sequência otimizada que reduza redundância operacional, sem substituir o testador nem "
            "exigir modelos formais prévios. As abordagens tradicionais não resolvem porque: (i) operam "
            "sobre casos inteiros, não passos; (ii) otimizam detecção precoce de falhas (APFD), não "
            "redução de repetição estrutural; (iii) ignoram dependências de contexto e re-setups na execução "
            "manual; (iv) não integram normalização semântica textual com estruturas de prefixos e avaliação "
            "HITL de forma sistemática."
        ),
        (
            "Se tivessem que resumir a contribuição deste trabalho em apenas uma frase, qual seria?",
            "Propomos e avaliamos um sistema de recomendação human-in-the-loop que consolida passos "
            "semanticamente equivalentes em suítes de teste manuais por meio de trie/DAG, reduzindo "
            "redundância estrutural na execução sem substituir o testador — com evidências de ganho "
            "estrutural (até 19,6% de passos), equivalência do modo heurístico local ao LLM remoto com "
            "custo muito menor, e redução média de 54% no tempo e 45% na carga cognitiva percebida em "
            "estudo com cinco testadores."
        ),
    ]),
    ("Capítulo 2 — Fundamentação Teórica", [
        (
            "Qual a diferença entre priorização, redução e ordenação de casos de teste? "
            "Por que essa distinção é importante para este trabalho?",
            "Priorização (TSP): reordenar casos inteiros para detectar falhas mais cedo em regressão. "
            "Redução (TSR): selecionar subconjunto de casos redundantes, eliminando casos inteiros. "
            "Ordenação/consolidação (este trabalho): produzir uma sequência linear de passos, fundindo "
            "prefixos comuns entre casos sem necessariamente eliminar casos — preserva validações por caso. "
            "A distinção é crucial porque usar o vocabulário da TSP/TSR sem qualificar levaria o avaliador "
            "a esperar APFD e automação; o IARTES trata passos, contexto destrutivo e esforço humano, "
            "não apenas ordem de casos para falhas precoces (§1.1, §2.3, Quadro 2)."
        ),
        (
            "Por que escolher Trie e DAG ao invés de outras estruturas de dados como grafos "
            "ponderados ou árvores de decisão?",
            "Trie captura naturalmente prefixos compartilhados entre sequências de passos — propriedade "
            "central do problema. O merge em DAG compacta subárvores equivalentes após normalização "
            "semântica, expondo oportunidades de consolidação que uma lista de casos ou um grafo genérico "
            "ponderado não modelam diretamente. Árvores de decisão representam ramificações de critérios "
            "de teste, não reuso de trechos executáveis entre casos. Grafos ponderados poderiam representar "
            "dependências, mas exigiriam modelagem e pesos ad hoc; trie/DAG alinha-se à operação de "
            "prefixo comum + validação por caso + DFS com heurísticas de destrutividade (§2.4, §4.3)."
        ),
        (
            "Como a carga cognitiva influencia diretamente a execução de testes manuais?",
            "O testador executa ciclos repetidos de ler, localizar, agir, observar e decidir (§2.2). "
            "Sweller: carga extrínseca aumenta quando a tarefa é mal organizada — passos redundantes, "
            "alternância de contexto e reexecução de prefixos equivalentes elevam memória de trabalho e "
            "fadiga, especialmente em testadores menos experientes. Reduzir repetição estrutural e oferecer "
            "roteiro consolidado diminui carga extrínseca sem remover o julgamento do testador. O NASA-TLX "
            "no estudo humano operationaliza essa relação (redução média de 44,9% em C3 vs C1)."
        ),
        (
            "Qual a relação entre Human-in-the-Loop e a proposta apresentada?",
            "O sistema produz recomendações transparentes (sequência, métricas, árvore trie/DAG), mas "
            "não executa testes nem impõe decisões irrevogáveis. O testador executa fisicamente, pode "
            "inspecionar o raciocínio estrutural e permanece responsável pelas validações. A base de "
            "conhecimento adaptativa permite refinamento entre sessões, mas o loop humano é mantido "
            "por design — adequado a contextos que exigem julgamento subjetivo e responsabilidade "
            "operacional (§2.6, §4.3.1)."
        ),
    ]),
    ("Capítulo 3 — Trabalhos Relacionados", [
        (
            "Qual trabalho da literatura mais se aproxima da proposta desenvolvida?",
            "Nenhum trabalho cobre integralmente a interseção passo + manual + trie/DAG + HITL. "
            "Os mais próximos por dimensão são: Yoo e Harman (2012) e Fernandes e Martins (2025) "
            "no panorama de priorização (mas automatizada e ao nível do caso); Khan et al. (2024) e "
            "Garg e Shekhar (2024) em ML/otimização multiobjetivo (mas com APFD e regressão); "
            "trabalhos de PLN/LLM em teste (§3.5) na dimensão semântica, sem consolidação estrutural "
            "para execução manual. O Quadro comparativo (§3.6) sintetiza que o nicho do IARTES é a "
            "combinação das três dimensões, não um único paper predecessor."
        ),
        (
            "Qual é exatamente o diferencial científico do trabalho de vocês em relação aos trabalhos relacionados?",
            "Quatro diferenciais explícitos (§3.7): (1) granularidade no passo normalizado, não no caso; "
            "(2) foco em execução manual roteirizada com texto livre, sem instrumentação de código; "
            "(3) combinação integrada de normalização semântica + trie/DAG sensível a contexto destrutivo; "
            "(4) paradigma HITL com métricas explicativas e avaliação empírica estrutural e humana. "
            "O objetivo é reduzir redundância operacional, não maximizar APFD."
        ),
        (
            "Existe alguma abordagem encontrada na literatura que vocês descartaram? Por quê?",
            "Sim, implicitamente: priorização pura por cobertura/APFD, redução de casos inteiros sem "
            "consolidação de passos, priorização dinâmica ML em regressão automatizada (Rao e Nandal, 2026), "
            "e model-based testing formal (Utting e Legeard) — descartadas ou não adotadas por exigirem "
            "código instrumentado, histórico de falhas, modelos formais ou executor automatizado, incompatíveis "
            "com suítes manuais em texto livre. Na implementação, o provedor OpenAI foi mantido como opção, "
            "mas o benchmark mostrou que o modo local é preferível no protocolo sem cache (§5.3)."
        ),
        (
            "Caso um pesquisador utilize outra técnica de priorização juntamente com a proposta de vocês, "
            "isso seria possível?",
            "Sim, de forma complementar. O IARTES pode atuar após ou antes de outras técnicas: por exemplo, "
            "uma TSP clássica poderia reordenar casos antes da consolidação de passos, ou a sequência "
            "consolidada poderia ser entrada para execução em pipeline com priorização por risco. "
            "A arquitetura modular (API REST, pipeline em etapas) e a separação entre reordenação de "
            "casos (etapa 4) e merge estrutural (etapas 5–6) permitem integração. O trabalho não avaliou "
            "essa combinação empiricamente — seria extensão futura."
        ),
    ]),
    ("Capítulo 4 — Materiais e Métodos", [
        (
            "Por que escolheram a Design Science Research como metodologia da pesquisa?",
            "Porque o objetivo é construir e avaliar rigorosamente um artefato (sistema de recomendação) "
            "para um problema prático bem delimitado, com métricas objetivas de eficácia. A DSR articula "
            "identificação do problema, projeto, desenvolvimento, demonstração, avaliação e comunicação "
            "(Quadro 4, Peffers et al., 2007), adequada quando a contribuição central é o artefato e não "
            "apenas a observação de fenômenos. Engenharia de software como pesquisa (Garousi et al., 2019) "
            "corrobora essa escolha."
        ),
        (
            "Quais evidências demonstram que o artefato realmente resolve o problema proposto?",
            "Três frentes (Capítulo 5): (1) QP1 — redução estrutural mensurável em S1–S4 (2,6% a 19,6%, "
            "136 passos economizados); (2) QP2 — modo local equivalente ao remoto com latência 373–493× "
            "menor; (3) QP3 — estudo com cinco testadores: tempo médio 51,7→24,4 min (−54,1%), NASA-TLX "
            "3,57→1,97 (−44,9%), convergência entre passos eliminados pelo sistema (34) e pelo testador "
            "em C2 (34,8 em média), e intenção declarada de adoção por todos. Limitações de n e suítes "
            "sintéticas qualificam o alcance, mas sustentam viabilidade no escopo avaliado."
        ),
        (
            "Como foi realizada a normalização semântica dos passos?",
            "Na etapa 2 do pipeline (§4.4.2, Quadro 5): cada descrição textual de passo é enviada ao "
            "provedor de inferência selecionado (heurístico local ou OpenAI gpt-4o-mini), que atribui um "
            "identificador canônico agrupando passos semanticamente equivalentes. O modo local usa regras "
            "determinísticas (normalização lexical, padrões de verbos, prefixos); o remoto usa LLM. "
            "Resultados podem ser cacheados na base de conhecimento SQLite (§4.4.4). O texto original "
            "é preservado para exibição ao testador."
        ),
        (
            "Como o sistema identifica quando dois passos são semanticamente equivalentes?",
            "Via provedor de inferência na normalização: o heurístico compara formas normalizadas "
            "(lowercase, remoção de ruído, padrões configurados); o LLM infere equivalência contextual "
            "entre paráfrases (ex.: \"Clicar em Entrar\" vs \"Selecionar botão de login\"). Passos "
            "com mesmo identificador canônico são tratados como um único nó na trie. A qualidade depende "
            "do modo escolhido; o benchmark mostrou convergência estrutural entre local e OpenAI em "
            "S1–S3. O testador pode auditar pelo texto original associado a cada nó."
        ),
        (
            "Como foram classificadas as ações destrutivas e não destrutivas?",
            "Na etapa 3 do pipeline, cada passo normalizado recebe tipo (verificação vs ação) e "
            "destrutividade binária (destrutivo vs não destrutivo) pelo mesmo provedor intercambiável. "
            "Destrutivo: passo que invalida contexto útil para passos posteriores (ex.: excluir cadastro "
            "necessário a casos seguintes), exigindo re-setup. Heurísticas e LLM aplicam regras/prompts "
            "definidos no protótipo (§4.3.3, §4.4.3). Classificação binária é simplificação deliberada; "
            "graus intermediários são trabalho futuro (F5)."
        ),
        (
            "Por que utilizar apenas cinco participantes no estudo experimental? Esse número é suficiente?",
            "Por viabilidade logística de sessão presencial (~3 h por participante, três condições em "
            "dispositivo real) e natureza piloto exploratória do estudo humano. Com n=5, testes "
            "inferenciais formais têm poder insuficiente; adotou-se análise descritiva (§4.5.6.6). "
            "O número não é suficiente para generalização estatística robusta — o texto afirma isso "
            "explicitamente (§5.6, §6.3). É suficiente para indicar tendência favorável e alimentar "
            "replicação futura (F1: n>5). Contrabalanceamento e métricas convergentes (tempo, NASA-TLX, "
            "qualitativo) fortalecem a leitura qualitativa, não inferência populacional."
        ),
        (
            "Quais ameaças à validade experimental vocês consideram mais críticas?",
            "As mais críticas: (1) validade externa — suítes sintéticas, um dispositivo, n=5, português "
            "(§5.6.2); (2) validade de conclusão — sem significância estatística no estudo humano (§5.6.4); "
            "(3) validade de construção — NASA-TLX em escala adaptada 1–5, reduction_percent como proxy "
            "de esforço real (§5.6.3); (4) validade interna — diferença de protocolo entre tela local e "
            "benchmark (cache/KB), variabilidade de P5 (§5.6.1)."
        ),
        (
            "Como evitar que o efeito de aprendizagem dos participantes tenha influenciado os resultados?",
            "Medidas adotadas (§4.5.6): ordem das condições C1/C2/C3 contrabalanceada entre participantes "
            "para distribuir aprendizado e fadiga; sessão piloto para calibrar instruções (dados excluídos); "
            "roteiro padronizado de preparação do aparelho entre condições; intervalos de descanso; "
            "treinamento inicial uniforme. C1 e C3 permitem comparar ordem original vs recomendada no "
            "mesmo nível de familiaridade relativa com a suíte ao longo da sessão. Não elimina totalmente "
            "o aprendizado — reconhecido em §4.5.7 e §5.6.1 — mas mitiga confundir ordem do efeito com "
            "familiaridade crescente de forma sistemática."
        ),
    ]),
    ("Capítulo 5 — Resultados", [
        (
            "A redução de aproximadamente 54% no tempo de execução é expressiva. Como vocês garantem "
            "que esse ganho decorre da abordagem proposta e não apenas da familiaridade crescente do "
            "participante com a suíte?",
            "Argumentos do texto: (1) contrabalanceamento da ordem das condições — se fosse só "
            "aprendizado, o ganho não seria consistentemente associado a C3 independentemente da ordem; "
            "(2) C2 isola o custo da reorganização humana — C3 ainda supera C2 em custo total em 56,7%, "
            "mostrando valor além de \"já conhecer a suíte\"; (3) convergência quantitativa: passos "
            "eliminados pelo pipeline (34) ≈ passos eliminados manualmente em C2 (34,8), ligando ganho "
            "de tempo à consolidação estrutural, não só prática; (4) P5 teve menor ganho apesar de maior "
            "familiaridade com eliminação manual — atribuído ao dispositivo, não à ordem. Ressalva honesta: "
            "com n=5 não há prova causal definitiva; é evidência forte e coerente, não randomização em "
            "grande escala."
        ),
        (
            "O benchmark mostrou que o GPT-4o-mini foi centenas de vezes mais lento. Em quais situações, "
            "mesmo assim, faria sentido utilizá-lo?",
            "Situações plausíveis: (1) uso esporádico com use_cache=true e KB populada — latência "
            "amortizada em sessões longas; (2) suítes com linguagem muito variada/paráfrases onde o "
            "heurístico falha e a divergência estrutural cresceria (não observado consistentemente em "
            "S1–S3, mas possível em domínios lexicamente heterogêneos); (3) prototipação ou auditoria "
            "pontual quando o custo de API é aceitável; (4) futuras versões com modelos mais rápidos "
            "ou batch. No protocolo avaliado (sem cache, comparação justa), o local é a escolha racional "
            "para otimização frequente."
        ),
        (
            "Houve algum resultado inesperado durante os experimentos?",
            "Sim, alguns: (1) convergência estrutural quase total local×OpenAI, quando poderia haver "
            "divergência semântica maior; (2) diferença de context_switches entre tela local e benchmark "
            "pelo efeito de cache/KB — exigiu explicação metodológica (§5.3); (3) P5 como outlier — maior "
            "tempo em C3 e menor ganho NASA-TLX apesar de eliminar mais passos em C2, atribuído ao "
            "aparelho Android; (4) S4 com redução estrutural (12,9%) menor que S3 (19,6%) apesar de "
            "grande suíte — perfil de redundância da suíte importa mais que tamanho bruto."
        ),
        (
            "Caso a suíte possuísse milhares de casos de teste, vocês acreditam que a abordagem continuaria "
            "escalável? Por quê?",
            "Parcialmente. Complexidade do pipeline é linearitmica na prática sobre passos e estrutura "
            "da trie/DAG (DFS O(V+E)); suítes muito grandes aumentam tempo de inferência por passo se "
            "cache desabilitado — gargalo principal no modo remoto. O merge de prefixos tende a escalar "
            "bem quando há alta redundância (ganhos crescem com oportunidade de reuso, como S3). "
            "Desafios: visualização/legibilidade da árvore, memória, tempo de normalização/classificação "
            "inicial, e necessidade de particionar suítes ou processamento incremental (trabalho futuro F4). "
            "A estrutura algorítmica escala; a operação ponta a ponta depende de provedor, cache e "
            "engenharia de produto para milhares de casos."
        ),
    ]),
]


def build_pdf():
    path = DOCS / "Perguntas_Banca_Simulacao_RESPOSTAS.pdf"
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    )
    st = styles()
    story = []
    story.append(Paragraph("Questionário de Simulação de Banca — Respostas", st["title"]))
    story.append(Paragraph(
        "Trabalho: <i>IARTES</i> — Sistema de recomendação para ordenação e consolidação "
        "de casos de teste manuais (trie/DAG, HITL)<br/>"
        "Baseado no TCC e no questionário enviado pelo professor (24 questões)",
        st["subtitle"],
    ))

    n = 0
    for section, items in QA:
        story.append(Paragraph(section, st["section"]))
        for q, a in items:
            n += 1
            story.append(Paragraph(f"<b>{n}. {q}</b>", st["qa"]))
            story.append(Paragraph(f"<b>R:</b> {a}", st["ans"]))

    doc.build(story)
    return path, n


if __name__ == "__main__":
    p, n = build_pdf()
    print(f"Gerado: {p} ({n} respostas)")
