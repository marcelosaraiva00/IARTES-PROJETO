import time

from flask import Flask, Response, jsonify, render_template, request

import config
from src.database.db import (
    get_history,
    get_runs_for_suite,
    init_db,
    kb_clear,
    kb_get_all_classifications,
    kb_get_all_normalizations,
    kb_get_stats,
    list_suites,
    save_optimization_run,
    save_suite,
)
from src.engine.benchmark import run_benchmark
from src.engine.export import (
    export_benchmark_csv,
    export_metrics_csv,
    export_result_csv,
    export_result_json,
)
from src.llm.factory import create_llm_provider
from src.parser.input_parser import (
    parse_csv,
    parse_form_data,
    parse_free_text,
    parse_json,
)
from src.engine.pipeline import run_optimization_pipeline

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/optimize", methods=["POST"])
def optimize():
    """Endpoint principal de otimização."""
    try:
        test_cases = _parse_request_test_cases()
        if not test_cases:
            return jsonify({"error": "Nenhum caso de teste válido encontrado na entrada."}), 400

        llm = create_llm_provider()

        start = time.perf_counter()
        result = run_optimization_pipeline(test_cases, llm)
        elapsed = (time.perf_counter() - start) * 1000

        result_dict = result.to_dict()

        suite_data = [
            {"id": tc.id, "name": tc.name, "steps": [s.original_text for s in tc.steps]}
            for tc in test_cases
        ]
        suite_id = save_suite("Otimização via web", suite_data)
        save_optimization_run(
            suite_id=suite_id,
            provider=llm.provider_name,
            result_json=result_dict,
            metrics_json=result_dict.get("metrics"),
            elapsed_ms=elapsed,
        )

        return jsonify(result_dict)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@app.route("/benchmark")
def benchmark_page():
    return render_template("benchmark.html")


@app.route("/api/benchmark", methods=["POST"])
def benchmark():
    """Executa benchmark comparando providers.

    Aceita os mesmos formatos do /api/optimize.
    Parâmetro opcional 'providers' como lista de nomes.
    """
    try:
        test_cases = _parse_request_test_cases()
        if not test_cases:
            return jsonify({"error": "Nenhum caso de teste válido encontrado."}), 400

        providers = None
        if request.content_type and "application/json" in request.content_type:
            providers = (request.json or {}).get("providers")

        comparison = run_benchmark(test_cases, provider_names=providers)

        if not comparison.runs:
            return jsonify({"error": "Nenhum provider disponível para benchmark."}), 400

        suite_data = [
            {"id": tc.id, "name": tc.name, "steps": [s.original_text for s in tc.steps]}
            for tc in test_cases
        ]
        suite_id = save_suite("Benchmark comparativo", suite_data)
        for run in comparison.runs:
            save_optimization_run(
                suite_id=suite_id,
                provider=run.provider_name,
                result_json=run.result.to_dict(),
                metrics_json=run.metrics.to_dict(),
                elapsed_ms=run.elapsed_ms,
            )

        return jsonify(comparison.to_dict())

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@app.route("/api/history")
def history():
    """Retorna histórico de execuções."""
    return jsonify(get_history())


@app.route("/api/suites")
def suites():
    """Retorna lista de suites salvas."""
    return jsonify(list_suites())


@app.route("/api/export/result/<int:run_id>")
def export_result(run_id: int):
    """Exporta resultado de uma execução específica como JSON ou CSV."""
    fmt = request.args.get("format", "json")
    from src.database.db import get_connection
    with get_connection() as conn:
        row = conn.execute(
            "SELECT result_json, metrics_json FROM optimization_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    if row is None:
        return jsonify({"error": "Execução não encontrada."}), 404

    import json
    result_dict = json.loads(row["result_json"])

    if fmt == "csv":
        csv_data = export_result_csv(result_dict)
        return Response(
            csv_data,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=resultado_{run_id}.csv"},
        )
    return Response(
        export_result_json(result_dict),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=resultado_{run_id}.json"},
    )


@app.route("/api/export/metrics/<int:run_id>")
def export_metrics(run_id: int):
    """Exporta métricas de uma execução como CSV."""
    from src.database.db import get_connection
    import json
    with get_connection() as conn:
        row = conn.execute(
            "SELECT metrics_json FROM optimization_runs WHERE id = ?",
            (run_id,),
        ).fetchone()
    if row is None or row["metrics_json"] is None:
        return jsonify({"error": "Métricas não encontradas."}), 404

    metrics_dict = json.loads(row["metrics_json"])
    csv_data = export_metrics_csv(metrics_dict)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=metricas_{run_id}.csv"},
    )


@app.route("/api/export/benchmark/<int:suite_id>")
def export_benchmark_data(suite_id: int):
    """Exporta dados comparativos de benchmark de uma suite como CSV."""
    runs = get_runs_for_suite(suite_id)
    if not runs:
        return jsonify({"error": "Nenhuma execução encontrada para esta suite."}), 404

    import json
    from src.engine.export import export_benchmark_csv as _export_bm

    providers = [r["provider"] for r in runs]
    comparison_table: dict[str, dict] = {}

    metric_labels = {
        "unique_normalized_ids": "Steps Únicos Detectados",
        "normalized_groups": "Grupos Normalizados",
        "verifications_detected": "Verificações Detectadas",
        "actions_detected": "Ações Detectadas",
        "destructive_steps": "Steps Destrutivos",
        "total_optimized_steps": "Steps Otimizados",
        "steps_eliminated": "Steps Eliminados",
        "reduction_percent": "Redução %",
        "resetup_count": "Re-setups",
        "context_switches": "Trocas de Contexto",
        "merge_depth_max": "Prof. Merge (máx)",
        "merge_depth_avg": "Prof. Merge (média)",
    }

    for key, label in metric_labels.items():
        row: dict = {"label": label}
        for run in runs:
            m = run.get("metrics_json") or {}
            row[run["provider"]] = m.get(key, "N/A")
        comparison_table[key] = row

    timing_row: dict = {"label": "Tempo (ms)"}
    for run in runs:
        timing_row[run["provider"]] = round(run.get("elapsed_ms", 0) or 0, 1)
    comparison_table["elapsed_ms"] = timing_row

    benchmark_dict = {"providers": providers, "comparison_table": comparison_table}
    csv_data = _export_bm(benchmark_dict)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=benchmark_suite_{suite_id}.csv"},
    )


@app.route("/knowledge-base")
def knowledge_base_page():
    return render_template("knowledge_base.html")


@app.route("/api/knowledge-base")
def knowledge_base_data():
    """Retorna normalizações e classificações da KB."""
    try:
        normalizations = kb_get_all_normalizations(limit=1000)
        classifications = kb_get_all_classifications(limit=1000)
        return jsonify({
            "normalizations": normalizations,
            "classifications": classifications,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/knowledge-base/stats")
def knowledge_base_stats():
    """Retorna estatísticas da KB."""
    try:
        return jsonify(kb_get_stats())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/knowledge-base", methods=["DELETE"])
def knowledge_base_clear():
    """Limpa toda a base de conhecimento."""
    try:
        kb_clear()
        return jsonify({"status": "ok", "message": "Base de conhecimento limpa com sucesso."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _parse_request_test_cases() -> list:
    """Extrai test cases do request (compartilhado entre /optimize e /benchmark)."""
    if request.content_type and "multipart/form-data" in request.content_type:
        input_type = request.form.get("input_type", "file")
    else:
        input_type = request.json.get("input_type", "form") if request.json else "form"

    if input_type == "form":
        data = request.json.get("data", [])
        return parse_form_data(data)
    elif input_type == "text":
        raw_text = request.json.get("data", "")
        return parse_free_text(raw_text)
    elif input_type == "file":
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            return []
        content = uploaded.read()
        filename = uploaded.filename.lower()
        if filename.endswith(".json"):
            return parse_json(content)
        elif filename.endswith((".csv", ".xlsx", ".xls")):
            return parse_csv(content, filename)
        else:
            text = content.decode("utf-8", errors="replace")
            return parse_free_text(text)
    return []


if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG, port=config.FLASK_PORT)
