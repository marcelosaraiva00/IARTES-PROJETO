import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.parser.input_parser import parse_free_text
from src.engine.benchmark import run_benchmark

with open("test_suites/suite_grande_portugues.txt", encoding="utf-8") as f:
    text = f.read()

test_cases = parse_free_text(text)
print(f"Suite: {len(test_cases)} testes, {sum(len(tc.steps) for tc in test_cases)} steps")
print()

print("Executando benchmark Local vs OpenAI...")
print("(Local deve levar ~3s, OpenAI pode levar 30-90s)")
print()

comparison = run_benchmark(test_cases, provider_names=["local", "openai"])
data = comparison.to_dict()

print("=" * 65)
print(f"{'METRICA':<40} {'LOCAL':>10} {'OPENAI':>10}")
print("=" * 65)

for key, row in data["comparison_table"].items():
    label = row["label"]
    local_val = row.get("local", "N/A")
    openai_val = row.get("openai", "N/A")
    print(f"{label:<40} {str(local_val):>10} {str(openai_val):>10}")

print("=" * 65)

print()
print("=== SEQUENCIA LOCAL ===")
local_run = data["runs"][0]
for item in local_run["result"]["optimized_sequence"]:
    badges = ""
    if item["validates_tests"]:
        badges += " [PASSA: " + ", ".join(item["validates_tests"]) + "]"
    if item["is_resetup"]:
        badges += " [RE-SETUP]"
    print(f"  {item['position']:3d}. {item['step_text']}{badges}")

print()
print("=== SEQUENCIA OPENAI ===")
openai_run = data["runs"][1]
for item in openai_run["result"]["optimized_sequence"]:
    badges = ""
    if item["validates_tests"]:
        badges += " [PASSA: " + ", ".join(item["validates_tests"]) + "]"
    if item["is_resetup"]:
        badges += " [RE-SETUP]"
    print(f"  {item['position']:3d}. {item['step_text']}{badges}")
