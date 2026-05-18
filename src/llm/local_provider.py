from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from src.llm.base import LLMProvider

# ---------------------------------------------------------------------------
# Classificação de verbos baseada em glossário de grupos verbais (BB8),
# adaptada para português e inglês.
# ---------------------------------------------------------------------------

VERB_GROUPS = {
    "verification": [
        "check", "verify", "validate",
        "verifique", "verificar", "verifica",
        "cheque", "checar", "checa",
        "valide", "validar",
        "confira", "confirme", "confirmar", "confere", "conferir",
        "observe", "observar",
        "show", "view",
        "veja", "ver", "visualize", "visualizar",
        "note", "notar",
        "assegure", "assegurar", "certifique", "certificar",
    ],
    "navigation": [
        "go", "open", "launch", "navigate",
        "va", "ir", "abra", "abrir", "inicie", "iniciar", "acesse", "acessar",
        "navegue", "navegar",
    ],
    "interaction": [
        "select", "tap", "press", "choose", "touch", "click", "long",
        "selecione", "selecionar", "toque", "tocar",
        "pressione", "pressionar", "clique", "clicar",
        "escolha", "escolher",
    ],
    "toggle": [
        "turn", "enable", "disable", "toggle", "activate", "deactivate",
        "ative", "ativar", "desative", "desativar",
        "habilite", "habilitar", "desabilite", "desabilitar",
        "ligue", "ligar", "desligue", "desligar",
    ],
    "execution": [
        "make", "run", "start", "perform", "setup", "execute", "initiate",
        "begin", "place", "create", "add", "register", "trigger",
        "faca", "fazer", "rode", "rodar", "comece", "comecar",
        "realize", "realizar", "executar",
        "crie", "criar", "configure", "configurar",
        "adicione", "adicionar", "cadastre", "cadastrar", "registre", "registrar",
    ],
    "communication": [
        "receive", "send", "answer", "dial", "call",
        "receba", "receber", "envie", "enviar",
        "atenda", "atender", "responda", "responder",
        "ligue", "disque",
    ],
    "state_change": [
        "switch", "change", "upgrade", "downgrade", "rotate", "increase",
        "decrease", "adjust",
        "troque", "trocar", "mude", "mudar", "altere", "alterar",
        "edite", "editar", "aumente", "aumentar", "diminua", "diminuir",
    ],
    "configuration": [
        "set", "define", "save",
        "defina", "definir", "ajuste", "ajustar",
        "salve", "salvar",
    ],
    "gesture": [
        "swipe", "drag", "move", "scroll", "pinch", "lift",
        "deslize", "deslizar", "arraste", "arrastar", "mova", "mover",
        "role", "rolar",
    ],
    "connection": [
        "connect", "disconnect", "pair", "unpair",
        "conecte", "conectar", "desconecte", "desconectar",
        "pareie", "parear", "emparelhe", "emparelhar",
    ],
    "input": [
        "enter", "insert", "type", "write", "fill",
        "insira", "inserir", "digite", "digitar",
        "escreva", "escrever", "preencha", "preencher",
    ],
    "termination": [
        "end", "finish", "complete", "exit", "close", "stop", "quit",
        "encerre", "encerrar", "finalize", "finalizar",
        "feche", "fechar", "saia", "sair", "pare", "parar",
        "termine", "terminar",
    ],
    "media": [
        "play", "pause", "resume", "record",
        "reproduza", "reproduzir", "pausar",
        "grave", "gravar",
    ],
    "reply": [
        "reply",
        "responda", "responder",
    ],
    "dialog": [
        "allow", "dismiss", "accept", "deny", "reject", "confirm", "cancel",
        "authenticate",
        "permita", "permitir", "aceite", "aceitar",
        "rejeite", "rejeitar",
        "cancele", "cancelar", "dispense", "dispensar",
    ],
    "security": [
        "unlock", "lock",
        "desbloqueie", "desbloquear", "bloqueie", "bloquear",
        "tranque", "trancar", "destranque", "destrancar",
    ],
    "deletion": [
        "remove", "delete", "clear", "erase", "wipe", "forget",
        "remova", "remover", "deletar",
        "apague", "apagar", "exclua", "excluir",
        "limpe", "limpar",
    ],
    "app_management": [
        "install", "uninstall", "update",
        "instale", "instalar", "desinstale", "desinstalar",
        "atualize", "atualizar",
    ],
    "system_upgrade": [
        "flash", "reboot", "restart", "reset", "factory",
        "reinicie", "reiniciar", "resete", "resetar",
        "restaure", "restaurar", "formate", "formatar",
    ],
    "return": [
        "return", "back", "volte", "voltar", "retome", "retomar",
        "retorne", "retornar",
    ],
    "wait": [
        "wait", "hold", "aguarde", "aguardar", "espere", "esperar",
    ],
}

VERIFICATION_GROUPS = {"verification"}
DESTRUCTIVE_GROUPS = {
    "toggle", "state_change", "connection", "termination",
    "security", "deletion", "app_management", "system_upgrade",
}

_VERB_INDEX: dict[str, tuple[str, bool, bool]] = {}
for _group, _verbs in VERB_GROUPS.items():
    _is_verif = _group in VERIFICATION_GROUPS
    _is_destr = _group in DESTRUCTIVE_GROUPS
    for _verb in _verbs:
        _VERB_INDEX[_verb.lower()] = (_group, _is_verif, _is_destr)

# ---------------------------------------------------------------------------
# Sinônimos de OBJETOS comuns em testes (alvo da ação)
# Cada grupo = palavras que se referem à mesma coisa.
# ---------------------------------------------------------------------------

_OBJECT_SYNONYMS = {
    "contact": {"contact", "contato", "contacts", "contatos"},
    "voice_call": {"voice call", "chamada de voz", "chamada voz", "call", "chamada",
                   "ligacao", "ligacao de voz"},
    "video_call": {"video call", "chamada de video", "chamada video",
                   "videochamada", "video"},
    "mute": {"mute", "mudo", "modo mudo", "mute button", "botao mudo"},
    "hold": {"hold", "espera", "em espera", "on hold"},
    "hd_icon": {"hd icon", "icone hd", "icone de hd", "hd"},
    "home_screen": {"home screen", "tela inicial", "home", "inicio"},
    "sms": {"sms", "message", "mensagem", "mensagens", "texto"},
    "wifi": {"wifi", "wi-fi", "wireless"},
    "bluetooth": {"bluetooth", "bt"},
    "screen": {"screen", "tela", "display"},
    "audio": {"audio", "sound", "som"},
    "volume": {"volume"},
    "notification": {"notification", "notificacao", "notificacoes"},
    "settings": {"settings", "configuracoes", "ajustes"},
    "fingerprint": {"fingerprint", "impressao digital", "biometria"},
    "password": {"password", "senha", "pin", "pattern", "padrao"},
    "app": {"app", "application", "aplicativo", "aplicacao"},
}

# Padrões de asserção (frases sem verbo que são verificações)
_ASSERTION_PATTERNS = [
    r"\bshould\b",
    r"\bmust\b",
    r"\bneeds?\s+to\b",
    r"\bhas\s+to\b",
    r"\bexpect\w*\b",
    r"\bdeveria\b",
    r"\bdeve\b",
    r"\bprecisa\b",
    r"\bnecessita\b",
    r"\bis\s+(?:visible|displayed|shown|present|active|connected|enabled|disabled)\b",
    r"\besta\s+(?:visivel|ativo|ativa|conectado|conectada|habilitado|desabilitado)\b",
    r"\baparece\b",
    r"\bappears?\b",
]
_ASSERTION_RE = re.compile("|".join(_ASSERTION_PATTERNS), re.IGNORECASE)

_NEGATION_PREFIXES = [
    ("ative", "desative"), ("ativar", "desativar"),
    ("habilite", "desabilite"), ("habilitar", "desabilitar"),
    ("ligue", "desligue"), ("ligar", "desligar"),
    ("conecte", "desconecte"), ("conectar", "desconectar"),
    ("bloqueie", "desbloqueie"), ("bloquear", "desbloquear"),
    ("instale", "desinstale"), ("instalar", "desinstalar"),
    ("enable", "disable"), ("connect", "disconnect"),
    ("lock", "unlock"), ("install", "uninstall"),
    ("activate", "deactivate"),
]

_STOPWORDS = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "por", "para", "com", "se", "que", "e", "ou",
    "the", "a", "an", "to", "of", "in", "on", "with", "for",
    "and", "or", "is", "are", "it", "its", "be", "been",
    "new", "novo", "nova", "back",
}


class LocalProvider(LLMProvider):
    """Provider local que funciona sem API, usando classificação BB8,
    normalização semântica por verbo+objeto, e Knowledge Base persistente.

    Ordem de resolução:
    1. Consulta a KB no SQLite (aprendizado de execuções anteriores)
    2. Se não encontrou, aplica heurísticas BB8
    """

    def complete(self, prompt: str, *, system_prompt: str = "") -> str:
        return ""

    def complete_json(self, prompt: str, *, system_prompt: str = "") -> dict | list:
        if "STEPS PARA NORMALIZAR" in prompt or "STEPS TO NORMALIZE" in prompt:
            return self._handle_normalization(prompt)
        if "STEPS PARA CLASSIFICAR" in prompt or "STEPS TO CLASSIFY" in prompt:
            return self._handle_classification(prompt)
        return {}

    def _handle_normalization(self, prompt: str) -> dict:
        from src.database.db import kb_get_normalization

        for marker in ("STEPS TO NORMALIZE:", "STEPS PARA NORMALIZAR:"):
            if marker in prompt:
                raw = prompt.split(marker)[-1]
                break
        else:
            raw = prompt
        lines = raw.strip().splitlines()
        steps = [line.strip().lstrip("- ").strip() for line in lines if line.strip().startswith("-")]

        mappings = {}
        unknown_steps: list[str] = []
        unknown_indices: list[int] = []

        for i, step in enumerate(steps):
            kb_hit = kb_get_normalization(step)
            if kb_hit:
                mappings[step] = {
                    "normalized_id": kb_hit["normalized_id"],
                    "normalized_text": kb_hit["normalized_text"],
                }
            else:
                unknown_steps.append(step)
                unknown_indices.append(i)

        if unknown_steps:
            heuristic_mappings = self._normalize_by_heuristics(unknown_steps)
            mappings.update(heuristic_mappings)

        return {"mappings": mappings}

    def _normalize_by_heuristics(self, steps: list[str]) -> dict:
        """Normaliza steps usando assinaturas semânticas BB8 (fallback quando KB não tem)."""
        signatures: list[tuple[str, str, str]] = []
        for step in steps:
            signatures.append(_extract_signature(step))

        groups: list[list[int]] = []
        for i, sig_i in enumerate(signatures):
            placed = False
            for group in groups:
                rep_idx = group[0]
                if _signatures_match(sig_i, signatures[rep_idx]):
                    group.append(i)
                    placed = True
                    break
            if not placed:
                sig_has_unknown = sig_i[0] == "unknown" or sig_i[1] == "unknown"
                if sig_has_unknown:
                    for group in groups:
                        rep_idx = group[0]
                        rep_sig = signatures[rep_idx]
                        rep_unknown = rep_sig[0] == "unknown" or rep_sig[1] == "unknown"
                        if rep_unknown and _are_similar_text(steps[i], steps[rep_idx]):
                            group.append(i)
                            placed = True
                            break
            if not placed:
                groups.append([i])

        mappings = {}
        for group in groups:
            rep = steps[group[0]]
            norm_id = _signature_to_id(signatures[group[0]], rep)
            for idx in group:
                mappings[steps[idx]] = {
                    "normalized_id": norm_id,
                    "normalized_text": rep,
                }

        return mappings

    def _handle_classification(self, prompt: str) -> dict:
        from src.database.db import kb_get_classification

        for marker in ("STEPS TO CLASSIFY:", "STEPS PARA CLASSIFICAR:"):
            if marker in prompt:
                raw = prompt.split(marker)[-1]
                break
        else:
            raw = prompt
        lines = raw.strip().splitlines()

        classifications = {}
        for line in lines:
            line = line.strip().lstrip("- ").strip()
            if not line:
                continue

            match = re.match(r'^(\S+):\s*"(.+)"', line)
            if not match:
                continue

            nid = match.group(1)
            text = match.group(2)

            kb_hit = kb_get_classification(nid)
            if kb_hit:
                classifications[nid] = {
                    "step_type": kb_hit["step_type"],
                    "is_destructive": kb_hit["is_destructive"],
                    "reasoning": f"KB (via {kb_hit['source_provider']})",
                }
                continue

            group_name, is_verif, is_destr = _classify_step(text)

            classifications[nid] = {
                "step_type": "verification" if is_verif else "action",
                "is_destructive": is_destr,
                "reasoning": f"BB8 grupo: {group_name}",
            }

        return {"classifications": classifications}


# ---------------------------------------------------------------------------
# Normalização por Verbo + Objeto (assinatura semântica)
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return without_accents.lower().strip()


def _extract_words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", _normalize_text(text))


_MAX_VERB_SEARCH_POS = 3


def _find_verb_group(text: str) -> str | None:
    """Encontra o grupo BB8 do primeiro verbo no texto.

    Só busca nas primeiras N palavras para evitar falsos positivos como
    "settings" → "set".
    """
    words = _extract_words(text)
    search_words = words[:_MAX_VERB_SEARCH_POS]

    for word in search_words:
        if word in _VERB_INDEX:
            return _VERB_INDEX[word][0]
    for word in search_words:
        if len(word) < 4:
            continue
        for verb, info in _VERB_INDEX.items():
            if len(verb) < 4:
                continue
            if _is_stem_match(word, verb):
                return info[0]
    return None


def _is_stem_match(word: str, verb: str) -> bool:
    """Match por radical: ambas devem compartilhar pelo menos 80% do comprimento."""
    shorter = min(len(word), len(verb))
    longer = max(len(word), len(verb))
    if longer - shorter > 3:
        return False
    common = 0
    for a, b in zip(word, verb):
        if a == b:
            common += 1
        else:
            break
    return common >= shorter * 0.8 and common >= 3


_DIRECTION_WORDS = {"in", "out", "up", "down", "on", "off"}


def _extract_object(text: str) -> str:
    """Extrai o objeto/alvo principal do step (após remover verbo e stopwords).

    Preserva modificadores direcionais (in/out/up/down) como parte do objeto
    para diferenciar 'zoom in' de 'zoom out', etc.
    """
    words = _extract_words(text)

    verb_idx = -1
    search_words = words[:_MAX_VERB_SEARCH_POS]
    for i, word in enumerate(search_words):
        if word in _VERB_INDEX:
            verb_idx = i
            break
        if len(word) >= 4:
            for verb in _VERB_INDEX:
                if len(verb) >= 4 and _is_stem_match(word, verb):
                    verb_idx = i
                    break
        if verb_idx >= 0:
            break

    content_words = words[verb_idx + 1:] if verb_idx >= 0 else words

    direction = ""
    remaining = []
    for w in content_words:
        if w in _DIRECTION_WORDS and not direction:
            direction = w
        elif w not in _STOPWORDS:
            remaining.append(w)

    normalized_obj = _canonicalize_object(" ".join(remaining))
    if direction:
        normalized_obj = normalized_obj + "_" + direction
    return normalized_obj


def _canonicalize_object(obj_text: str) -> str:
    """Mapeia sinônimos de objetos para um nome canônico.

    Preserva palavras curtas que são identificadores (A, B, 5G, etc.)
    quando aparecem após o objeto principal.
    """
    lower = obj_text.lower()
    for canonical, synonyms in _OBJECT_SYNONYMS.items():
        for syn in synonyms:
            if syn in lower:
                remaining = lower.replace(syn, "").strip()
                remaining_words = [
                    w for w in remaining.split()
                    if w not in _STOPWORDS
                ]
                remaining_words = [w for w in remaining_words if len(w) > 1 or w.isalnum()]
                if remaining_words:
                    return canonical + "_" + "_".join(remaining_words[:3])
                return canonical
    words = [w for w in lower.split() if w not in _STOPWORDS]
    words = [w for w in words if len(w) > 1 or w.isalnum()]
    return "_".join(words[:5]) if words else "unknown"


def _extract_signature(text: str) -> tuple[str, str, str]:
    """Extrai a assinatura semântica: (verb_group, object, negation_flag).

    Dois steps com a mesma assinatura representam a mesma ação.
    """
    verb_group = _find_verb_group(text) or "unknown"
    obj = _extract_object(text)

    norm = _normalize_text(text)
    has_negation = False
    for pos, neg in _NEGATION_PREFIXES:
        if neg in norm:
            has_negation = True
            break

    neg_flag = "neg" if has_negation else "pos"
    return (verb_group, obj, neg_flag)


def _signatures_match(a: tuple[str, str, str], b: tuple[str, str, str]) -> bool:
    """Verifica se duas assinaturas representam a mesma ação."""
    if a[2] != b[2]:
        return False

    if a[0] == "unknown" or b[0] == "unknown":
        return a[1] == b[1] and a[1] != "unknown"

    same_group = a[0] == b[0]
    same_object = a[1] == b[1]

    if same_group and same_object:
        return True

    if same_object and _groups_are_compatible(a[0], b[0]):
        return True

    return False


def _groups_are_compatible(g1: str, g2: str) -> bool:
    """Verifica se dois grupos BB8 são semanticamente compatíveis para a mesma ação."""
    compatible_sets = [
        {"execution", "navigation"},
        {"state_change", "execution"},
        {"interaction", "execution"},
    ]
    pair = {g1, g2}
    return any(pair <= s for s in compatible_sets)


def _signature_to_id(sig: tuple[str, str, str], fallback_text: str) -> str:
    verb_group, obj, neg = sig
    parts = []
    if neg == "neg":
        parts.append("NOT")
    parts.append(verb_group.upper())
    if obj and obj != "unknown":
        parts.append(obj.upper())
    result = "_".join(parts)
    if result and result not in ("UNKNOWN", "UNKNOWN_UNKNOWN"):
        return re.sub(r"[^A-Z0-9_]", "", result)
    return _text_to_id(fallback_text)


def _text_to_id(text: str) -> str:
    clean = _normalize_text(text)
    clean = re.sub(r"[^\w\s]", "", clean)
    parts = clean.split()[:6]
    return "_".join(parts).upper() if parts else "STEP"


# ---------------------------------------------------------------------------
# Similaridade de texto (fallback se assinatura não bater)
# ---------------------------------------------------------------------------

def _are_similar_text(a: str, b: str) -> bool:
    na = _normalize_text(a)
    nb = _normalize_text(b)
    if na == nb:
        return True
    if _has_negation_conflict(na, nb):
        return False
    ratio = SequenceMatcher(None, na, nb).ratio()
    return ratio >= 0.85


def _has_negation_conflict(a: str, b: str) -> bool:
    for pos, neg in _NEGATION_PREFIXES:
        if (pos in a and neg in b) or (neg in a and pos in b):
            return True
    return False


# ---------------------------------------------------------------------------
# Classificação (verificação / ação / destrutivo)
# ---------------------------------------------------------------------------

def _classify_step(text: str) -> tuple[str, bool, bool]:
    """Classifica um step por verbo BB8 ou por padrão de asserção."""
    group_name, is_verif, is_destr = _classify_by_verb(text)

    if not is_verif and _is_assertion(text):
        return ("assertion", True, False)

    return (group_name, is_verif, is_destr)


def _classify_by_verb(text: str) -> tuple[str, bool, bool]:
    words = _extract_words(text)
    search_words = words[:_MAX_VERB_SEARCH_POS]
    for word in search_words:
        if word in _VERB_INDEX:
            return _VERB_INDEX[word]
    for word in search_words:
        if len(word) < 4:
            continue
        for verb, info in _VERB_INDEX.items():
            if len(verb) < 4:
                continue
            if _is_stem_match(word, verb):
                return info
    return ("unknown", False, False)


def _is_assertion(text: str) -> bool:
    """Detecta frases de asserção sem verbo explícito de verificação."""
    return bool(_ASSERTION_RE.search(text))
