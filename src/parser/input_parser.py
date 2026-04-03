from __future__ import annotations

import csv
import io
import json
import re
from typing import Optional

import pandas as pd

from src.models.test_case import Step, TestCase


def parse_form_data(tests_data: list[dict]) -> list[TestCase]:
    """Parseia dados vindos do formulário web.

    Formato esperado:
    [
        {"id": "TEST-001", "name": "...", "steps": ["step1", "step2", ...]},
        ...
    ]
    """
    test_cases = []
    for item in tests_data:
        tc = TestCase(
            id=item.get("id", ""),
            name=item.get("name", ""),
            steps=[Step(original_text=s.strip()) for s in item.get("steps", []) if s.strip()],
        )
        if tc.id and tc.steps:
            test_cases.append(tc)
    return test_cases


def parse_free_text(text: str) -> list[TestCase]:
    """Parseia texto livre colado pelo usuário.

    Formato esperado (flexível):
        TEST-001  ou  TESTE-001  ou  # Test Name
        step 1
        step 2
        ...

        TEST-002
        step 1
        ...
    """
    test_cases = []
    current_test: Optional[TestCase] = None
    test_counter = 0

    header_pattern = re.compile(
        r"^(?:"
        r"(?:TESTE?|TC|CASO)[\s\-_]*(\d+)"
        r"|#{1,3}\s*(.+)"
        r")"
        r"(?:\s*[-–:]\s*(.+))?",
        re.IGNORECASE,
    )

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = header_pattern.match(line)
        if match:
            test_counter += 1
            num = match.group(1)
            heading = match.group(2)
            suffix = match.group(3) or ""

            if num:
                test_id = f"TEST-{num.zfill(3)}"
                test_name = suffix.strip() if suffix.strip() else line
            else:
                test_id = f"TEST-{test_counter:03d}"
                test_name = heading.strip()

            current_test = TestCase(id=test_id, name=test_name, steps=[])
            test_cases.append(current_test)
        elif current_test is not None:
            cleaned = re.sub(r"^\d+[\.\)\-]\s*", "", line)
            if cleaned:
                current_test.steps.append(Step(original_text=cleaned))

    return [tc for tc in test_cases if tc.steps]


def parse_csv(file_content: bytes | str, filename: str = "") -> list[TestCase]:
    """Parseia CSV ou Excel.

    Formato esperado: colunas test_id, test_name, step_order, step_text
    """
    ext = filename.rsplit(".", 1)[-1].lower() if filename else "csv"

    if ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_content) if isinstance(file_content, bytes) else file_content)
    else:
        text = file_content.decode("utf-8") if isinstance(file_content, bytes) else file_content
        df = pd.read_csv(io.StringIO(text))

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    col_map = _detect_columns(df.columns.tolist())
    if not col_map.get("test_id") or not col_map.get("step_text"):
        raise ValueError(
            "O arquivo precisa ter pelo menos colunas para ID do teste e texto do step. "
            "Colunas encontradas: " + ", ".join(df.columns.tolist())
        )

    tests: dict[str, TestCase] = {}
    for _, row in df.iterrows():
        tid = str(row[col_map["test_id"]]).strip()
        if not tid:
            continue
        step_text = str(row[col_map["step_text"]]).strip()
        if not step_text:
            continue

        if tid not in tests:
            name = str(row.get(col_map.get("test_name", ""), tid)).strip() if col_map.get("test_name") else tid
            tests[tid] = TestCase(id=tid, name=name, steps=[])

        tests[tid].steps.append(Step(original_text=step_text))

    return list(tests.values())


def parse_json(file_content: bytes | str) -> list[TestCase]:
    """Parseia JSON.

    Aceita:
      - Lista de objetos com id/name/steps
      - Objeto com chave "tests" contendo a lista acima
    """
    text = file_content.decode("utf-8") if isinstance(file_content, bytes) else file_content
    data = json.loads(text)

    if isinstance(data, dict) and "tests" in data:
        data = data["tests"]

    if not isinstance(data, list):
        raise ValueError("JSON deve conter uma lista de testes ou um objeto com chave 'tests'.")

    return parse_form_data(data)


def _detect_columns(columns: list[str]) -> dict[str, str]:
    """Tenta mapear colunas do DataFrame para os campos esperados."""
    mapping: dict[str, str] = {}

    id_candidates = ["test_id", "id", "caso_id", "teste_id", "test", "caso", "teste"]
    name_candidates = ["test_name", "name", "nome", "nome_teste", "descricao"]
    step_candidates = ["step_text", "step", "passo", "texto", "descricao_passo", "step_description"]
    order_candidates = ["step_order", "order", "ordem", "sequencia"]

    for candidates, key in [
        (id_candidates, "test_id"),
        (name_candidates, "test_name"),
        (step_candidates, "step_text"),
        (order_candidates, "step_order"),
    ]:
        for c in candidates:
            if c in columns:
                mapping[key] = c
                break

    return mapping
