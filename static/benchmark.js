document.addEventListener("DOMContentLoaded", () => {
    const btnBenchmark = document.getElementById("btn-benchmark");
    const loading = document.getElementById("loading");

    btnBenchmark.addEventListener("click", async () => {
        const text = document.getElementById("raw-text").value.trim();
        if (!text) {
            showError("Cole os casos de teste para executar o benchmark.");
            return;
        }

        try {
            btnBenchmark.disabled = true;
            loading.style.display = "flex";
            hideError();

            const response = await fetch("/api/benchmark", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ input_type: "text", data: text }),
            });

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            renderBenchmark(data);
            if (Array.isArray(data.warnings) && data.warnings.length) {
                showError("Benchmark concluído com alertas: " + data.warnings.join(" | "));
            }
        } catch (err) {
            showError(err.message);
        } finally {
            btnBenchmark.disabled = false;
            loading.style.display = "none";
        }
    });

    function renderBenchmark(data) {
        const section = document.getElementById("result-section");
        section.style.display = "block";

        renderComparisonTable(data);
        renderSideBySide(data);
        renderBenchmarkExport(data);

        section.scrollIntoView({ behavior: "smooth" });
    }

    function renderBenchmarkExport(data) {
        let container = document.getElementById("benchmark-export");
        if (!container) {
            container = document.createElement("div");
            container.id = "benchmark-export";
            container.className = "export-buttons";
            document.getElementById("result-section").appendChild(container);
        }

        const jsonBlob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const jsonUrl = URL.createObjectURL(jsonBlob);

        const providers = data.providers || [];
        let csvContent = "Métrica," + providers.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(",") + "\n";
        for (const [key, row] of Object.entries(data.comparison_table || {})) {
            csvContent += `"${row.label}"`;
            providers.forEach(p => { csvContent += `,${row[p]}`; });
            csvContent += "\n";
        }
        const csvBlob = new Blob([csvContent], { type: "text/csv" });
        const csvUrl = URL.createObjectURL(csvBlob);

        container.innerHTML = `
            <a href="${jsonUrl}" download="benchmark.json" class="btn-export">Exportar JSON Completo</a>
            <a href="${csvUrl}" download="benchmark_comparativo.csv" class="btn-export">Exportar Tabela CSV</a>
        `;
    }

    function renderComparisonTable(data) {
        const table = document.getElementById("comparison-table");
        const providers = data.providers;

        let html = "<thead><tr><th>Métrica</th>";
        providers.forEach(p => { html += `<th>${p.charAt(0).toUpperCase() + p.slice(1)}</th>`; });
        html += "</tr></thead><tbody>";

        const higherIsBetter = new Set(["steps_eliminated", "reduction_percent", "merge_depth_max", "merge_depth_avg"]);
        const lowerIsBetter = new Set(["total_optimized_steps", "resetup_count", "context_switches", "elapsed_ms"]);

        for (const [key, row] of Object.entries(data.comparison_table)) {
            html += `<tr><td>${row.label}</td>`;
            const vals = providers.map(p => row[p]);
            const numVals = vals.map(Number);

            providers.forEach((p, i) => {
                let cls = "";
                if (providers.length > 1) {
                    if (higherIsBetter.has(key) && numVals[i] === Math.max(...numVals) && numVals[i] !== numVals[1 - i]) {
                        cls = ' class="cell-best"';
                    } else if (lowerIsBetter.has(key) && numVals[i] === Math.min(...numVals) && numVals[i] !== numVals[1 - i]) {
                        cls = ' class="cell-best"';
                    }
                }
                html += `<td${cls}>${row[p]}</td>`;
            });
            html += "</tr>";
        }

        html += "</tbody>";
        table.innerHTML = html;
    }

    function renderSideBySide(data) {
        const container = document.getElementById("side-by-side");
        container.innerHTML = "";

        data.runs.forEach(run => {
            const panel = document.createElement("div");
            panel.className = "side-panel";

            let stepsHtml = "";
            run.result.optimized_sequence.forEach(item => {
                const classes = ["opt-step"];
                if (item.validates_tests.length) classes.push("validates");
                if (item.step_type === "verification") classes.push("is-verification");
                if (item.is_destructive) classes.push("is-destructive");
                if (item.is_resetup) classes.push("is-resetup");

                let badges = "";
                item.validates_tests.forEach(tid => {
                    badges += `<span class="badge badge-pass">PASSA ${tid}</span>`;
                });
                if (item.is_resetup) badges += `<span class="badge badge-resetup">Re-setup</span>`;
                if (item.step_type === "verification") badges += `<span class="badge badge-type">Verificação</span>`;
                else badges += `<span class="badge badge-action">Ação</span>`;
                if (item.is_destructive) badges += `<span class="badge badge-destructive">Destrutivo</span>`;

                stepsHtml += `
                    <div class="${classes.join(" ")}">
                        <span class="opt-step-num">${item.position}.</span>
                        <span class="opt-step-text">${item.step_text}</span>
                        <div class="opt-step-badges">${badges}</div>
                    </div>`;
            });

            const stats = run.result.stats;
            let treeBlock = "";
            if (run.result.trie_tree && typeof appendTrieTree === "function") {
                const treeId = `bm-tree-${run.provider.replace(/\W/g, "")}`;
                treeBlock = `
                    <details class="tree-panel bm-tree-panel">
                        <summary>Árvore de prefixos</summary>
                        <p class="tree-panel-hint">Mesma estrutura da página principal: ramos compartilhados e ordem dos filhos alinhada ao otimizador.</p>
                        <div class="tree-scroll" id="${treeId}"></div>
                    </details>`;
                container.appendChild(panel);
                panel.innerHTML = `
                    <h3>${run.provider.charAt(0).toUpperCase() + run.provider.slice(1)} (${stats.reduction_percent}% redução, ${Math.round(run.elapsed_ms)}ms)</h3>
                    ${treeBlock}
                    ${stepsHtml}
                `;
                const treeEl = document.getElementById(treeId);
                if (treeEl) appendTrieTree(treeEl, run.result.trie_tree);
                return;
            }
            panel.innerHTML = `
                <h3>${run.provider.charAt(0).toUpperCase() + run.provider.slice(1)} (${stats.reduction_percent}% redução, ${Math.round(run.elapsed_ms)}ms)</h3>
                ${stepsHtml}
            `;
            container.appendChild(panel);
        });
    }

    function showError(msg) {
        const banner = document.getElementById("error-banner");
        document.getElementById("error-message").textContent = msg;
        banner.style.display = "flex";
    }

    function hideError() {
        document.getElementById("error-banner").style.display = "none";
    }

    document.getElementById("btn-close-error").addEventListener("click", hideError);
});
