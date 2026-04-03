import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.parser.input_parser import parse_free_text
from src.engine.pipeline import run_optimization_pipeline
from src.llm.factory import create_llm_provider

with open("test_suites/suite_grande_portugues.txt", encoding="utf-8") as f:
    text = f.read()

test_cases = parse_free_text(text)
print("=== PARSING ===")
print(f"Testes parseados: {len(test_cases)}")
total_steps = sum(len(tc.steps) for tc in test_cases)
print(f"Total steps originais: {total_steps}")
for tc in test_cases:
    print(f"  {tc.id}: {tc.name} ({len(tc.steps)} steps)")

print()
print("=== EXECUTANDO PIPELINE (provider: local) ===")
llm = create_llm_provider("local")
result = run_optimization_pipeline(test_cases, llm)
d = result.to_dict()

stats = d["stats"]
print("=== RESULTADO ===")
print(f"Steps originais: {stats['original_step_count']}")
print(f"Steps otimizados: {stats['optimized_step_count']}")
print(f"Steps economizados: {stats['steps_saved']}")
print(f"Reducao: {stats['reduction_percent']}%")
print()

print("=== METRICAS ===")
m = d.get("metrics", {})
for k, v in m.items():
    print(f"  {k}: {v}")

print()
print("=== SEQUENCIA OTIMIZADA ===")
for item in d["optimized_sequence"]:
    badges = ""
    if item["validates_tests"]:
        badges += " [PASSA: " + ", ".join(item["validates_tests"]) + "]"
    if item["is_resetup"]:
        badges += " [RE-SETUP]"
    if item["step_type"] == "verification":
        badges += " [VERIF]"
    if item["is_destructive"]:
        badges += " [DESTRUTIVO]"
    print(f"  {item['position']:3d}. {item['step_text']}{badges}")

print()
print("=== ANALISE DE NORMALIZACAO ===")
norm_map = {}
for tc in test_cases:
    for step in tc.steps:
        nid = step.normalized_id or step.original_text
        if nid not in norm_map:
            norm_map[nid] = set()
        norm_map[nid].add(step.original_text)

groups_with_multiple = {nid: texts for nid, texts in norm_map.items() if len(texts) > 1}
print(f"Total IDs normalizados unicos: {len(norm_map)}")
print(f"Grupos com merge (>1 texto original): {len(groups_with_multiple)}")
for nid, texts in sorted(groups_with_multiple.items()):
    print(f"  {nid}:")
    for t in sorted(texts):
        print(f"    - {t}")

print()
print("=== ANALISE DE CLASSIFICACAO ===")
verif_count = 0
action_count = 0
destr_count = 0
for tc in test_cases:
    for step in tc.steps:
        if step.step_type.value == "verification":
            verif_count += 1
        else:
            action_count += 1
        if step.is_destructive:
            destr_count += 1
print(f"Verificacoes: {verif_count}")
print(f"Acoes: {action_count}")
print(f"Destrutivos: {destr_count}")
