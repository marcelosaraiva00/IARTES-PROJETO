import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from src.parser.input_parser import parse_free_text
from src.engine.benchmark import run_benchmark

text = """
TEST-001 - Conexão WiFi Básica
Abra o aplicativo Configurações
Navegue até as configurações de WiFi
Ative o WiFi
Selecione a rede "TestNetwork_5G"
Digite a senha "secure123"
Toque em Conectar
Verifique que o ícone de WiFi conectado aparece na barra de status
Verifique que o nome da rede mostra "TestNetwork_5G"

TEST-002 - Intensidade do Sinal WiFi
Abra o aplicativo Configurações
Navegue até as configurações de WiFi
Ative o WiFi
Selecione a rede "TestNetwork_5G"
Digite a senha "secure123"
Toque em Conectar
Verifique que o ícone de WiFi conectado aparece na barra de status
Abra a cortina de notificações
Verifique que o indicador de sinal mostra pelo menos 3 barras

TEST-003 - Desconexão e Reconexão WiFi
Abra o aplicativo Configurações
Navegue até as configurações de WiFi
Ative o WiFi
Selecione a rede "TestNetwork_5G"
Digite a senha "secure123"
Toque em Conectar
Verifique que o ícone de WiFi conectado aparece na barra de status
Toque em Desconectar
Verifique que a mensagem de WiFi desconectado aparece
Selecione a rede "TestNetwork_5G"
Verifique que o WiFi reconecta automaticamente sem pedir a senha

TEST-004 - Esquecer Rede WiFi
Abra o aplicativo Configurações
Navegue até as configurações de WiFi
Ative o WiFi
Selecione a rede "TestNetwork_5G"
Digite a senha "secure123"
Toque em Conectar
Verifique que o ícone de WiFi conectado aparece na barra de status
Pressione e segure na rede conectada
Toque em Esquecer Rede
Verifique que a rede foi removida da lista de redes salvas

TEST-005 - Pareamento Bluetooth com Fone
Abra o aplicativo Configurações
Navegue até as configurações de Bluetooth
Ative o Bluetooth
Verifique que o dispositivo está buscando aparelhos próximos
Selecione "WH-1000XM5" na lista de dispositivos disponíveis
Confirme o código de pareamento em ambos os dispositivos
Verifique que "WH-1000XM5" aparece como Conectado

TEST-006 - Roteamento de Áudio Bluetooth
Abra o aplicativo Configurações
Navegue até as configurações de Bluetooth
Ative o Bluetooth
Selecione "WH-1000XM5" na lista de dispositivos disponíveis
Confirme o código de pareamento em ambos os dispositivos
Verifique que "WH-1000XM5" aparece como Conectado
Abra o aplicativo de Música
Reproduza uma música
Verifique que o áudio está sendo enviado para o fone Bluetooth
Verifique que os controles de mídia aparecem no fone

TEST-007 - Desconexão Bluetooth Durante Chamada
Abra o aplicativo Configurações
Navegue até as configurações de Bluetooth
Ative o Bluetooth
Selecione "WH-1000XM5" na lista de dispositivos disponíveis
Confirme o código de pareamento em ambos os dispositivos
Verifique que "WH-1000XM5" aparece como Conectado
Abra o aplicativo Telefone
Disque o número "+1-555-0199"
Verifique que a chamada está conectada
Verifique que o áudio está sendo transmitido pelo fone Bluetooth
Desative o Bluetooth
Verifique que o áudio da chamada muda para o alto-falante
Verifique que a chamada permanece conectada

TEST-008 - Captura de Foto
Abra o aplicativo Câmera
Mude para o modo Foto
Verifique que o visor está ativo
Toque no botão de captura
Verifique que a animação do obturador é exibida
Verifique que a notificação de foto salva aparece
Abra o aplicativo Fotos (Google Fotos)
Verifique que a última foto aparece nas fotos recentes

TEST-009 - Gravação de Vídeo
Abra o aplicativo Câmera
Mude para o modo Vídeo
Verifique que o visor está ativo
Toque no botão de gravar
Aguarde 10 segundos
Toque no botão de parar gravação
Verifique que a notificação de vídeo salvo aparece
Abra o aplicativo Fotos (Google Fotos)
Verifique que o último vídeo aparece na mídia recente
Reproduza o vídeo gravado
Verifique que a reprodução do vídeo funciona corretamente

TEST-010 - Câmera Frontal
Abra o aplicativo Câmera
Mude para o modo Foto
Verifique que o visor está ativo
Toque no botão de trocar câmera
Verifique que a câmera frontal está ativa
Verifique que o indicador de detecção facial aparece
Toque no botão de captura
Verifique que a selfie foi salva
"""

test_cases = parse_free_text(text)
total = sum(len(tc.steps) for tc in test_cases)
print(f"Suite: {len(test_cases)} testes, {total} steps")
print()
print("Executando benchmark Local vs OpenAI...")

start = time.time()
comparison = run_benchmark(test_cases, provider_names=["local", "openai"])
elapsed = time.time() - start
print(f"Benchmark total: {elapsed:.1f}s")
print()

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
for run in data["runs"]:
    p = run["provider"]
    seq = run["result"]["optimized_sequence"]
    print(f"=== SEQUENCIA {p.upper()} ({len(seq)} steps) ===")
    for item in seq:
        badges = ""
        if item["validates_tests"]:
            badges += " [PASSA: " + ", ".join(item["validates_tests"]) + "]"
        if item["is_resetup"]:
            badges += " [RE-SETUP]"
        print(f"  {item['position']:3d}. {item['step_text']}{badges}")
    print()
