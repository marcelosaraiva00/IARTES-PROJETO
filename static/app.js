document.addEventListener("DOMContentLoaded", () => {
    // --- Tab switching ---
    const tabs = document.querySelectorAll(".tab");
    const tabContents = document.querySelectorAll(".tab-content");

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            tabs.forEach((t) => t.classList.remove("active"));
            tabContents.forEach((tc) => tc.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
        });
    });

    // --- Form: add/remove test cases and steps ---
    let testCounter = 1;

    document.getElementById("btn-add-test").addEventListener("click", () => {
        testCounter++;
        const container = document.getElementById("test-cases-container");
        const block = document.createElement("div");
        block.className = "test-case-block";
        block.dataset.index = testCounter;
        block.innerHTML = `
            <div class="test-case-header">
                <input type="text" class="tc-id" placeholder="ID (ex: TEST-${String(testCounter).padStart(3, "0")})" value="TEST-${String(testCounter).padStart(3, "0")}">
                <input type="text" class="tc-name" placeholder="Nome do teste">
                <button class="btn-remove-tc" title="Remover teste">&times;</button>
            </div>
            <div class="steps-list">
                <div class="step-row">
                    <span class="step-num">1.</span>
                    <input type="text" class="step-input" placeholder="Descreva o step...">
                    <button class="btn-remove-step" title="Remover step">&times;</button>
                </div>
            </div>
            <button class="btn-add-step">+ Adicionar Step</button>
        `;
        container.appendChild(block);
        renumberAllSteps();
    });

    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("btn-remove-tc")) {
            const block = e.target.closest(".test-case-block");
            if (document.querySelectorAll(".test-case-block").length > 1) {
                block.remove();
            }
        }

        if (e.target.classList.contains("btn-add-step")) {
            const stepsList = e.target.previousElementSibling;
            const count = stepsList.querySelectorAll(".step-row").length + 1;
            const row = document.createElement("div");
            row.className = "step-row";
            row.innerHTML = `
                <span class="step-num">${count}.</span>
                <input type="text" class="step-input" placeholder="Descreva o step...">
                <button class="btn-remove-step" title="Remover step">&times;</button>
            `;
            stepsList.appendChild(row);
            row.querySelector(".step-input").focus();
        }

        if (e.target.classList.contains("btn-remove-step")) {
            const row = e.target.closest(".step-row");
            const list = row.closest(".steps-list");
            if (list.querySelectorAll(".step-row").length > 1) {
                row.remove();
                renumberSteps(list);
            }
        }
    });

    function renumberSteps(stepsList) {
        stepsList.querySelectorAll(".step-row").forEach((row, i) => {
            row.querySelector(".step-num").textContent = (i + 1) + ".";
        });
    }

    function renumberAllSteps() {
        document.querySelectorAll(".steps-list").forEach(renumberSteps);
    }

    // --- File upload ---
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const fileNameEl = document.getElementById("file-name");
    let selectedFile = null;

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
            selectedFile = e.dataTransfer.files[0];
            fileNameEl.textContent = selectedFile.name;
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length) {
            selectedFile = fileInput.files[0];
            fileNameEl.textContent = selectedFile.name;
        }
    });

    // --- Optimize button ---
    const btnOptimize = document.getElementById("btn-optimize");
    const loading = document.getElementById("loading");

    btnOptimize.addEventListener("click", async () => {
        const activeTab = document.querySelector(".tab.active").dataset.tab;

        try {
            btnOptimize.disabled = true;
            loading.style.display = "flex";
            hideError();

            let response;

            if (activeTab === "form") {
                const data = collectFormData();
                if (!data.length) {
                    throw new Error("Adicione pelo menos um caso de teste com steps.");
                }
                response = await fetch("/api/optimize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ input_type: "form", data }),
                });
            } else if (activeTab === "text") {
                const text = document.getElementById("raw-text").value.trim();
                if (!text) {
                    throw new Error("Cole o texto dos casos de teste.");
                }
                response = await fetch("/api/optimize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ input_type: "text", data: text }),
                });
            } else if (activeTab === "file") {
                if (!selectedFile) {
                    throw new Error("Selecione um arquivo.");
                }
                const formData = new FormData();
                formData.append("input_type", "file");
                formData.append("file", selectedFile);
                response = await fetch("/api/optimize", {
                    method: "POST",
                    body: formData,
                });
            }

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            renderResult(result);
        } catch (err) {
            showError(err.message);
        } finally {
            btnOptimize.disabled = false;
            loading.style.display = "none";
        }
    });

    function collectFormData() {
        const blocks = document.querySelectorAll(".test-case-block");
        const data = [];
        blocks.forEach((block) => {
            const id = block.querySelector(".tc-id").value.trim();
            const name = block.querySelector(".tc-name").value.trim();
            const steps = [];
            block.querySelectorAll(".step-input").forEach((inp) => {
                const v = inp.value.trim();
                if (v) steps.push(v);
            });
            if (id && steps.length) {
                data.push({ id, name: name || id, steps });
            }
        });
        return data;
    }

    // --- Render result ---
    function renderResult(data) {
        const section = document.getElementById("result-section");
        section.style.display = "block";

        const stats = data.stats;
        document.getElementById("stats-bar").innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${stats.test_count}</div>
                <div class="stat-label">Testes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.original_step_count}</div>
                <div class="stat-label">Steps Originais</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${stats.optimized_step_count}</div>
                <div class="stat-label">Steps Otimizados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:var(--success)">${stats.steps_saved}</div>
                <div class="stat-label">Steps Economizados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" style="color:var(--success)">${stats.reduction_percent}%</div>
                <div class="stat-label">Redução</div>
            </div>
        `;

        const listEl = document.getElementById("optimized-list");
        listEl.innerHTML = "";

        data.optimized_sequence.forEach((item) => {
            const classes = ["opt-step"];
            if (item.validates_tests.length) classes.push("validates");
            if (item.step_type === "verification") classes.push("is-verification");
            if (item.is_destructive) classes.push("is-destructive");
            if (item.is_resetup) classes.push("is-resetup");

            let badges = "";
            if (item.validates_tests.length) {
                item.validates_tests.forEach((tid) => {
                    badges += `<span class="badge badge-pass">PASSA ${tid}</span>`;
                });
            }
            if (item.is_resetup) {
                badges += `<span class="badge badge-resetup">Re-setup</span>`;
            }
            if (item.step_type === "verification") {
                badges += `<span class="badge badge-type">Verificação</span>`;
            }
            if (item.is_destructive) {
                badges += `<span class="badge badge-destructive">Destrutivo</span>`;
            }

            const div = document.createElement("div");
            div.className = classes.join(" ");
            div.innerHTML = `
                <span class="opt-step-num">${item.position}.</span>
                <span class="opt-step-text">${item.step_text}</span>
                <div class="opt-step-badges">${badges}</div>
            `;
            listEl.appendChild(div);
        });

        const origList = document.getElementById("original-tests-list");
        origList.innerHTML = "";
        data.original_tests.forEach((t) => {
            const div = document.createElement("div");
            div.className = "original-test-item";
            div.innerHTML = `
                <span class="original-test-id">${t.id}</span>
                <span>${t.name || ""}</span>
                <span class="original-test-steps">${t.step_count} steps</span>
            `;
            origList.appendChild(div);
        });

        section.scrollIntoView({ behavior: "smooth" });
    }

    // --- Error handling ---
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
