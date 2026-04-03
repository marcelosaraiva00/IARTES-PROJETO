import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.llm.factory import create_llm_provider

llm = create_llm_provider("openai")
print("Provider criado:", llm.provider_name)
print("Testando chamada simples...")
try:
    result = llm.complete_json('Return this JSON: {"test": "ok"}')
    print("Resposta:", result)
    print("API funcionando!")
except Exception as e:
    print("ERRO:", type(e).__name__, str(e))
