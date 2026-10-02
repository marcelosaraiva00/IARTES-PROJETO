#!/usr/bin/env python3
"""Gera PDFs com perguntas de banca para defesa do TCC IARTES."""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

# Fonte com suporte a acentuação (Windows)
FONT_PATHS = [
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\calibri.ttf"),
]
FONT_NAME = "BancaFont"
for fp in FONT_PATHS:
    if fp.exists():
        pdfmetrics.registerFont(TTFont(FONT_NAME, str(fp)))
        break
else:
    FONT_NAME = "Helvetica"


def build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title",
            parent=base["Heading1"],
            fontName=FONT_NAME,
            fontSize=16,
            leading=20,
            spaceAfter=12,
            textColor=colors.HexColor("#1a1a2e"),
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#444444"),
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontName=FONT_NAME,
            fontSize=12,
            leading=16,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#16213e"),
        ),
        "question": ParagraphStyle(
            "question",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=14,
            spaceBefore=6,
            spaceAfter=4,
            leftIndent=0,
        ),
        "answer": ParagraphStyle(
            "answer",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=10,
            leading=14,
            spaceBefore=2,
            spaceAfter=10,
            leftIndent=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#222222"),
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName=FONT_NAME,
            fontSize=8,
            textColor=colors.grey,
        ),
    }
    return styles


QUESTIONS = [
    {
        "section": "Capítulo 1 — Introdução (§1.1–§1.6)",
        "items": [
            {
                "q": "Qual lacuna científica este trabalho afirma preencher em relação à priorização clássica (TSP/TSR) e por que a literatura existente não resolve o cenário manual?",
                "a": (
                    "A lacuna está na execução manual com forte sobreposição entre casos: a TSP/TSR "
                    "trata casos inteiros em regressão automatizada, sem modelar (i) redundância semântica "
                    "entre passos, (ii) impacto destrutivo sobre o contexto e (iii) o testador como decisor "
                    "final (HITL). O texto sintetiza isso em três evidências literárias (§1.2) e distingue "
                    "explicitamente o problema de maximizar APFD/detecção precoce de falhas do objetivo aqui, "
                    "que é reduzir redundância operacional estrutural na execução manual roteirizada."
                ),
            },
            {
                "q": "Por que a unidade de análise é o passo normalizado e não o caso de teste inteiro?",
                "a": (
                    "Porque a redundância que onera o testador ocorre no nível dos passos repetidos entre "
                    "casos (login, navegação, configuração), não necessariamente entre casos completos. "
                    "Modelar ao nível do caso oculta prefixos compartilhados e oportunidades de consolidação. "
                    "A trie/DAG sobre passos permite reuso explícito de prefixos, merge semântico e "
                    "marcação de validação por caso (§1.1, §4.3.2)."
                ),
            },
            {
                "q": "Como as três questões de pesquisa (QP1–QP3) se articulam com os objetivos específicos?",
                "a": (
                    "A Tabela 1 encadeia cada QP aos OEs: QP1 liga-se a caracterizar lacunas (OE1), "
                    "especificar trie/DAG (OE2), métricas estruturais (OE4) e avaliação empírica (OE5); "
                    "QP2 a provedores intercambiáveis (OE2), benchmark (OE3), custo computacional (OE4) "
                    "e comparação local×OpenAI (OE5); QP3 ao protótipo utilizável (OE3), métricas operacionais "
                    "e NASA-TLX (OE4), estudo com testadores (OE7) e ameaças à validade (OE5). "
                    "As QPs são complementares: estrutura (QP1), custo de inferência (QP2) e efeito humano (QP3)."
                ),
            },
            {
                "q": "O que significa operar como sistema human-in-the-loop (HITL) neste trabalho?",
                "a": (
                    "O sistema recomenda a sequência consolidada e apresenta métricas/árvore explicativas, "
                    "mas não executa os testes nem substitui o julgamento do testador. A automação limita-se "
                    "à análise estrutural (normalização, classificação, trie/DAG, geração da sequência); "
                    "a execução física e a decisão final permanecem humanas (§1.1, §2.6, §4.3.1)."
                ),
            },
            {
                "q": "A justificativa prática e científica do trabalho é convincente para um contexto industrial real?",
                "a": (
                    "A justificativa aponta custo cognitivo, fadiga e reorganização tácita por testadores "
                    "experientes (§1.5). Os ganhos no estudo humano (54,1% tempo, 44,9% NASA-TLX) sustentam "
                    "relevância prática em laboratório, mas o próprio texto reconhece limitação de validade "
                    "externa: suítes sintéticas, n=5 e um dispositivo. A adoção industrial depende dos "
                    "trabalhos futuros F1 e F2 (§6.3–§6.4)."
                ),
            },
        ],
    },
    {
        "section": "Capítulo 2 — Fundamentação Teórica (§2.1–§2.8)",
        "items": [
            {
                "q": "Por que trie e DAG são adequadas para consolidar suítes de teste manuais?",
                "a": (
                    "A trie representa prefixos compartilhados entre casos; o merge em DAG compacta sufixos "
                    "equivalentes após normalização semântica. Isso captura reuso estrutural que uma lista "
                    "linear de casos não expõe. A DFS com heurísticas (verificações antes de ramos destrutivos) "
                    "gera sequência linear com pontos de validação por caso (§2.4, §4.3.4)."
                ),
            },
            {
                "q": "O que é a classificação binária de impacto no contexto e quais suas limitações?",
                "a": (
                    "Cada passo é classificado como verificação ou ação e como destrutivo ou não destrutivo "
                    "em relação ao contexto de execução. Passos destrutivos invalidam estados úteis e exigem "
                    "re-setups. A simplificação binária é deliberada para tratabilidade e interpretabilidade, "
                    "mas não captura graus intermediários de destrutividade — limitação reconhecida em §4.3.3 "
                    "e trabalho futuro F5."
                ),
            },
            {
                "q": "Qual o trade-off entre provedor heurístico local e LLM remoto (OpenAI)?",
                "a": (
                    "O heurístico local tem latência baixa e custo desprezível, com cobertura semântica "
                    "limitada a padrões explícitos. O LLM pode lidar melhor com paráfrases, mas impõe "
                    "custo, latência de rede e menor auditabilidade. O benchmark com use_cache=false mostrou "
                    "equivalência estrutural aproximada com o remoto 373–493× mais lento (§2.5, §5.3)."
                ),
            },
            {
                "q": "Por que Design Science Research (DSR) é o arcabouço metodológico escolhido?",
                "a": (
                    "Porque o núcleo do trabalho é construir e avaliar um artefato (sistema de recomendação) "
                    "para um problema prático, com evidências empíricas de eficácia. A DSR articula problema, "
                    "projeto, demonstração, avaliação e comunicação (Quadro 4, Peffers et al.). Pesquisa "
                    "puramente empírica sem artefato ou desenvolvimento sem avaliação rigorosa seriam "
                    "insuficientes para o objetivo declarado."
                ),
            },
        ],
    },
    {
        "section": "Capítulo 3 — Trabalhos Relacionados (§3.1–§3.8)",
        "items": [
            {
                "q": "A revisão da literatura é sistemática (SLR)? Como responder à criticidade desse ponto?",
                "a": (
                    "Não é SLR formal. É revisão orientada com critérios explícitos de busca, inclusão e "
                    "exclusão (§3.1), bases ACM/IEEE/Scopus/Google Scholar, período 2018–2026 complementado "
                    "por referências seminais e surveys (Yoo & Harman; Fernandes & Martins; Hou et al.). "
                    "A defesa deve enfatizar rastreabilidade e foco no nicho (passo, manual, HITL), não "
                    "exaustividade global do tema TCP."
                ),
            },
            {
                "q": "Em que o IARTES difere das abordagens baseadas em aprendizado de máquina citadas (ex.: Khan et al., 2024)?",
                "a": (
                    "As abordagens ML priorizam casos inteiros em regressão automatizada, otimizando APFD "
                    "com histórico de falhas/cobertura. O IARTES consolida passos em texto livre para execução "
                    "manual, sem pressupor instrumentação de código nem histórico de defeitos. O objetivo "
                    "não é detectar falhas mais cedo, e sim reduzir passos redundantes preservando validações "
                    "(§3.3, §3.7, Quadro comparativo)."
                ),
            },
            {
                "q": "Trabalhos com LLM em teste já não fazem normalização semântica? Qual a novidade aqui?",
                "a": (
                    "Trabalhos correlatos usam PLN/LLM em tarefas pontuais de teste; a novidade declarada "
                    "é a integração sistemática: normalização + classificação de contexto + trie/DAG + "
                    "sequência HITL com métricas explicativas e avaliação empírica em suítes e com testadores. "
                    "A interseção das três dimensões (passo, manual, estrutura+semântica) é o nicho do §3.7."
                ),
            },
            {
                "q": "Por que comparar com APFD se o IARTES não mede detecção de falhas?",
                "a": (
                    "A comparação em §5.5.5 é qualificada: métricas não são diretamente comparáveis. "
                    "APFD mede detecção precoce em regressão automatizada; o IARTES mede redução estrutural "
                    "de passos e esforço humano. A menção à literatura serve apenas para contextualizar magnitude "
                    "e deixar claro que o problema e a métrica de sucesso são distintos."
                ),
            },
        ],
    },
    {
        "section": "Capítulo 4 — Materiais e Métodos (§4.1–§4.7)",
        "items": [
            {
                "q": "Por que usar suítes sintéticas (S1–S4) em vez de suítes industriais?",
                "a": (
                    "Para controle reprodutível do conteúdo, eliminar confidencialidade e isolar o mecanismo "
                    "do pipeline sem ruído de terminologia inconsistente ou passos parcialmente automatizados. "
                    "S4 foi escolhida para o estudo humano por equilibrar tamanho e duração de sessão. "
                    "O texto reconhece isso como ameaça à validade externa (§4.5.1, §4.5.7, §5.6.2)."
                ),
            },
            {
                "q": "O estudo é quali-quantitativo? Justifique com base no protocolo.",
                "a": (
                    "Sim. Vertente quantitativa: métricas estruturais (reduction_percent, steps_eliminated, "
                    "elapsed_ms), benchmark S1–S3/S4 e, no estudo humano, tempos e NASA-TLX. Vertente "
                    "qualitativa: análise temática do questionário aberto, inspeção de sequências e padrões "
                    "nos relatos (§4.1). Ambas subsidiam a interpretação nos Capítulos 5 e 6."
                ),
            },
            {
                "q": "Por que n=5 participantes e análise descritiva sem testes inferenciais?",
                "a": (
                    "O desenho é piloto em laboratório com medidas repetidas (C1, C2, C3). Com n=5, testes "
                    "como Wilcoxon ou ANOVA teriam poder estatístico insuficiente e pressupostos frágeis. "
                    "Adotou-se médias, medianas, desvios-padrão e reduções percentuais (§4.5.6.6). "
                    "Inferência formal é trabalho futuro F1/F7."
                ),
            },
            {
                "q": "Explique o desenho experimental das condições C1, C2 e C3 e o contrabalanceamento.",
                "a": (
                    "C1: ordem original da documentação. C2: testador planeja e executa livremente "
                    "(tempos separados). C3: sequência do protótipo. Todos executam as três condições "
                    "(medidas repetidas); a ordem foi contrabalanceada entre participantes para mitigar "
                    "aprendizado e fadiga (§4.5.6.1–§4.5.6.4). Não houve randomização entre grupos porque "
                    "não há grupos distintos."
                ),
            },
            {
                "q": "O que é use_cache=false no benchmark e por que isso importa para a QP2?",
                "a": (
                    "Com use_cache=false, normalizações e classificações não reutilizam a base de conhecimento "
                    "persistente; cada execução refaz inferências. No benchmark também se executa kb_clear() "
                    "antes das campanhas. Isso permite comparar local×OpenAI em condição 'a frio', sem "
                    "vantagem de cache para o remoto (§4.5.4, §5.3)."
                ),
            },
            {
                "q": "Descreva sucintamente as sete etapas do pipeline de otimização.",
                "a": (
                    "(1) Entrada da suíte; (2) Normalização semântica de passos; (3) Classificação "
                    "(verificação/ação, destrutivo/não destrutivo); (4) Reordenação de casos; "
                    "(5) Construção trie/DAG com merge; (6) DFS gerando sequência linear com validações; "
                    "(7) Cálculo de métricas (Quadro 5, §4.4.2)."
                ),
            },
            {
                "q": "Quais as principais ameaças metodológicas antecipadas no Capítulo 4?",
                "a": (
                    "Validade interna: aprendizado/fadiga (mitigados por contrabalanceamento e piloto); "
                    "validade externa: suítes sintéticas e amostra pequena; validade de construção: "
                    "NASA-TLX adaptado e métricas como proxy de esforço; validade de conclusão: "
                    "sem significância estatística no estudo humano (§4.5.7, detalhado em §5.6)."
                ),
            },
        ],
    },
    {
        "section": "Capítulo 5 — Resultados e Discussão (§5.1–§5.6)",
        "items": [
            {
                "q": "A QP1 foi respondida positivamente? Os ganhos de 2,6% a 19,6% são expressivos?",
                "a": (
                    "Sim, no plano estrutural: redução crescente com redundância da suíte (S3: 19,6%; "
                    "136 passos economizados no total). S4 (12,9%) é menor que S3 por perfil da suíte "
                    "(menos oportunidade de merge). O ganho percentual sozinho pode parecer modesto em S1/S2, "
                    "mas escala com suítes maiores; o estudo humano mostra tradução em tempo (QP3)."
                ),
            },
            {
                "q": "Por que o OpenAI não justifica o custo no benchmark (QP2)?",
                "a": (
                    "Convergência estrutural em S1–S2 e diferença mínima em S3 (1 passo, 0,22 p.p.), "
                    "enquanto o tempo foi 373–493× maior. Sem ganho estrutural consistente, o custo "
                    "computacional e de API não se paga no protocolo avaliado (use_cache=false). "
                    "O modo local é recomendado para laços frequentes de otimização."
                ),
            },
            {
                "q": "Por que context_switches difere entre a tela local (§5.2) e o benchmark (§5.3)?",
                "a": (
                    "Protocolos distintos: a tela de otimização pode usar cache/KB populada (use_cache=true); "
                    "o benchmark usa kb_clear() e use_cache=false, podendo alterar classificações destrutivas "
                    "e, em cascata, contagens de contexto. Para local×OpenAI prevalece Tabela 6; para "
                    "caracterização da tela local, Figuras §5.2 e Tabela 5."
                ),
            },
            {
                "q": "Como interpretar a redução de 54,1% no tempo e 44,9% no NASA-TLX (QP3)?",
                "a": (
                    "C3 (sequência do protótipo) vs C1 (ordem original): tempo médio 51,7→24,4 min; "
                    "carga NASA-TLX global 3,57→1,97. Também superou C2 em custo total (planejamento+execução) "
                    "em 56,7%. Todos declararam intenção de adoção. Ressalva: n=5, um dispositivo, análise "
                    "descritiva — tendência forte, generalização limitada."
                ),
            },
            {
                "q": "Como explicar o participante P5 como outlier?",
                "a": (
                    "P5 teve maior tempo em C3 (40,8 min), menor redução temporal (36,5%) e menor queda "
                    "no NASA-TLX (28,6%), apesar de eliminar mais passos manualmente em C2 (49). "
                    "Nas respostas abertas, atribuiu dificuldade ao desconhecimento do aparelho Android, "
                    "não à sequência em si (§5.4.3, §5.6.1)."
                ),
            },
            {
                "q": "A consolidação de passos pode prejudicar a detecção de defeitos?",
                "a": (
                    "O trabalho não mediu taxa de detecção de falhas antes/depois da consolidação — "
                    "limitação explícita. O pipeline preserva pontos de validação por caso (PASSA TEST-XXX) "
                    "e re-setups quando o contexto é invalidado. O trade-off consolidação×cobertura de falhas "
                    "é reconhecido no Resumo e em trabalhos futuros. A defesa deve ser honesta: ganho de "
                    "eficiência operacional, não evidência de manutenção de efetividade em detecção."
                ),
            },
            {
                "q": "A comparação quantitativa com a literatura (§5.5.5) é metodologicamente válida?",
                "a": (
                    "Parcialmente. O texto admite que APFD e redução de passos/tempo manual não são "
                    "diretamente comparáveis. A seção contextualiza magnitudes e reforça diferença de "
                    "objetivo (detecção precoce vs redundância operacional). Serve para posicionamento, "
                    "não para afirmar superioridade absoluta sobre técnicas clássicas."
                ),
            },
        ],
    },
    {
        "section": "Capítulo 6 — Considerações Finais e questões transversais",
        "items": [
            {
                "q": "Quais as três contribuições mais sólidas e qual a mais frágil diante da banca?",
                "a": (
                    "Sólidas: (1) modelo trie/DAG ao nível do passo com validações; (2) protótipo reprodutível "
                    "com benchmark e métricas; (3) evidência humana convergente (tempo, NASA-TLX, adoção "
                    "declarada). Mais frágil: generalização industrial e inferência estatística robusta — "
                    "dependem de suítes reais e n maior (§6.2, §6.3)."
                ),
            },
            {
                "q": "Quais trabalhos futuros são prioritários e por quê?",
                "a": (
                    "F1 (replicação com n>5 e múltiplos dispositivos) e F2 (suítes industriais anonimizadas) "
                    "são Alta/Alto na Tabela 11 — atacam as duas principais ressalvas: amostra pequena e "
                    "validade externa. F3 (ablação por etapa) e F8 (integração com ferramentas de QA) "
                    "têm alto impacto técnico/prático em seguida."
                ),
            },
            {
                "q": "O artefato está disponível para reprodução? O que um replicador precisaria?",
                "a": (
                    "Sim: protótipo em Python/Flask, commit c0d5ed6, suítes no Apêndice A e repositório, "
                    "schema SQLite no Apêndice C, exemplo S1 no Apêndice B. Para replicar o estudo humano: "
                    "mesmo dispositivo (Pixel 5a), suíte S4, protocolo §4.5.6 e formulários. Benchmark: "
                    "ambiente documentado em §4.5.4 (Ryzen 5 PRO, 16 GB, Python 3.13.3)."
                ),
            },
        ],
    },
]


def build_story(styles, include_answers: bool):
    story = []
    story.append(Paragraph("TCC IARTES — Simulado de Perguntas de Banca", styles["title"]))
    subtitle = (
        "Trabalho: <i>Sistema de recomendação para ordenação e consolidação de casos de teste "
        "manuais (trie/DAG, HITL)</i><br/>"
        "UFAC — Especialização em IA para Engenharia de Testes de Software<br/>"
        f"Documento: {'Perguntas e Respostas' if include_answers else 'Apenas Perguntas'} "
        f"({sum(len(s['items']) for s in QUESTIONS)} questões)"
    )
    story.append(Paragraph(subtitle, styles["subtitle"]))
    story.append(Spacer(1, 0.3 * cm))

    n = 0
    for block in QUESTIONS:
        story.append(Paragraph(block["section"], styles["section"]))
        for item in block["items"]:
            n += 1
            story.append(
                Paragraph(f"<b>{n}.</b> {item['q']}", styles["question"])
            )
            if include_answers:
                story.append(
                    Paragraph(f"<b>Resposta sugerida:</b> {item['a']}", styles["answer"])
                )
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "Elaborado com base no TCC IARTES (versão atual). "
            "Use as respostas como roteiro — adapte à sua fala e aos dados exatos do seu PDF.",
            styles["footer"],
        )
    )
    return story


def generate_pdf(filename: str, include_answers: bool):
    path = DOCS / filename
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Simulado Banca TCC IARTES",
    )
    styles = build_styles()
    story = build_story(styles, include_answers)
    doc.build(story)
    return path


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    p1 = generate_pdf("TCC_IARTES_Simulado_Banca_PERGUNTAS.pdf", include_answers=False)
    p2 = generate_pdf("TCC_IARTES_Simulado_Banca_PERGUNTAS_E_RESPOSTAS.pdf", include_answers=True)
    print(f"Gerado: {p1}")
    print(f"Gerado: {p2}")


if __name__ == "__main__":
    main()
