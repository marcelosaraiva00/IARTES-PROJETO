from flask import Flask, jsonify, render_template, request

import config
from src.llm.factory import create_llm_provider
from src.parser.input_parser import (
    parse_csv,
    parse_form_data,
    parse_free_text,
    parse_json,
)
from src.engine.pipeline import run_optimization_pipeline

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/optimize", methods=["POST"])
def optimize():
    """Endpoint principal de otimização.

    Aceita JSON com:
      - input_type: "form" | "text" | "file"
      - data: depende do input_type
    Ou multipart/form-data com arquivo + input_type="file"
    """
    try:
        test_cases = []

        if request.content_type and "multipart/form-data" in request.content_type:
            input_type = request.form.get("input_type", "file")
        else:
            input_type = request.json.get("input_type", "form") if request.json else "form"

        if input_type == "form":
            data = request.json.get("data", [])
            test_cases = parse_form_data(data)

        elif input_type == "text":
            raw_text = request.json.get("data", "")
            test_cases = parse_free_text(raw_text)

        elif input_type == "file":
            uploaded = request.files.get("file")
            if not uploaded or not uploaded.filename:
                return jsonify({"error": "Nenhum arquivo enviado."}), 400

            content = uploaded.read()
            filename = uploaded.filename.lower()

            if filename.endswith(".json"):
                test_cases = parse_json(content)
            elif filename.endswith((".csv", ".xlsx", ".xls")):
                test_cases = parse_csv(content, filename)
            else:
                text = content.decode("utf-8", errors="replace")
                test_cases = parse_free_text(text)

        if not test_cases:
            return jsonify({"error": "Nenhum caso de teste válido encontrado na entrada."}), 400

        llm = create_llm_provider()
        result = run_optimization_pipeline(test_cases, llm)

        return jsonify(result.to_dict())

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=config.FLASK_DEBUG, port=config.FLASK_PORT)
