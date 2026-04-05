document.addEventListener("DOMContentLoaded", () => {
    const kbTabs = document.querySelectorAll(".kb-tab");
    const kbTabContents = document.querySelectorAll(".kb-tab-content");

    kbTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            kbTabs.forEach((t) => t.classList.remove("active"));
            kbTabContents.forEach((tc) => tc.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById("kb-tab-" + tab.dataset.kbTab).classList.add("active");
        });
    });

    let allNormalizations = [];
    let allClassifications = [];

    const searchInput = document.getElementById("kb-search");
    searchInput.addEventListener("input", () => {
        const q = searchInput.value.toLowerCase().trim();
        renderNormTable(filterNorms(q));
        renderClassTable(filterClasses(q));
    });

    function filterNorms(q) {
        if (!q) return allNormalizations;
        return allNormalizations.filter(
            (n) =>
                n.original_text.toLowerCase().includes(q) ||
                n.normalized_id.toLowerCase().includes(q) ||
                n.normalized_text.toLowerCase().includes(q) ||
                n.provider.toLowerCase().includes(q)
        );
    }

    function filterClasses(q) {
        if (!q) return allClassifications;
        return allClassifications.filter(
            (c) =>
                c.normalized_id.toLowerCase().includes(q) ||
                c.step_type.toLowerCase().includes(q) ||
                c.provider.toLowerCase().includes(q)
        );
    }

    function providerBadge(provider) {
        const cls = provider === "local" ? "provider-local" : provider === "openai" ? "provider-openai" : "provider-other";
        return `<span class="provider-badge ${cls}">${provider}</span>`;
    }

    function formatDate(dateStr) {
        if (!dateStr) return "--";
        const d = new Date(dateStr + "Z");
        return d.toLocaleDateString("pt-BR") + " " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    }

    function renderNormTable(items) {
        const tbody = document.getElementById("norm-tbody");
        const empty = document.getElementById("norm-empty");
        const table = document.getElementById("norm-table");

        if (!items.length) {
            tbody.innerHTML = "";
            table.style.display = "none";
            empty.style.display = "block";
            return;
        }

        table.style.display = "table";
        empty.style.display = "none";

        tbody.innerHTML = items
            .map(
                (n) => `<tr>
                <td title="${escapeHtml(n.original_text)}">${escapeHtml(n.original_text)}</td>
                <td><code>${escapeHtml(n.normalized_id)}</code></td>
                <td title="${escapeHtml(n.normalized_text)}">${escapeHtml(n.normalized_text)}</td>
                <td>${providerBadge(n.provider)}</td>
                <td>${formatDate(n.created_at)}</td>
            </tr>`
            )
            .join("");
    }

    function renderClassTable(items) {
        const tbody = document.getElementById("class-tbody");
        const empty = document.getElementById("class-empty");
        const table = document.getElementById("class-table");

        if (!items.length) {
            tbody.innerHTML = "";
            table.style.display = "none";
            empty.style.display = "block";
            return;
        }

        table.style.display = "table";
        empty.style.display = "none";

        tbody.innerHTML = items
            .map(
                (c) => `<tr>
                <td><code>${escapeHtml(c.normalized_id)}</code></td>
                <td class="${c.step_type === "verification" ? "type-verification" : "type-action"}">${c.step_type === "verification" ? "Verificação" : "Ação"}</td>
                <td class="${c.is_destructive ? "destructive-yes" : "destructive-no"}">${c.is_destructive ? "Sim" : "Não"}</td>
                <td>${providerBadge(c.provider)}</td>
                <td>${formatDate(c.created_at)}</td>
            </tr>`
            )
            .join("");
    }

    function renderStats(stats) {
        document.getElementById("stat-norm-total").textContent = stats.normalizations_total;
        document.getElementById("stat-class-total").textContent = stats.classifications_total;

        const breakdown = document.getElementById("kb-provider-breakdown");
        const providers = new Set([
            ...Object.keys(stats.normalizations_by_provider || {}),
            ...Object.keys(stats.classifications_by_provider || {}),
        ]);

        if (!providers.size) {
            breakdown.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">Nenhum provider registrado ainda.</p>';
            return;
        }

        breakdown.innerHTML = Array.from(providers)
            .map((p) => {
                const norms = (stats.normalizations_by_provider || {})[p] || 0;
                const classes = (stats.classifications_by_provider || {})[p] || 0;
                return `<div class="kb-provider-card">
                    <div class="kb-provider-name">${escapeHtml(p)}</div>
                    <div class="kb-provider-stats"><span>${norms}</span> norm. / <span>${classes}</span> class.</div>
                </div>`;
            })
            .join("");
    }

    async function loadData() {
        const loading = document.getElementById("loading");
        loading.style.display = "flex";

        try {
            const [statsRes, dataRes] = await Promise.all([
                fetch("/api/knowledge-base/stats"),
                fetch("/api/knowledge-base"),
            ]);

            const stats = await statsRes.json();
            const data = await dataRes.json();

            renderStats(stats);

            allNormalizations = data.normalizations || [];
            allClassifications = data.classifications || [];

            const q = searchInput.value.toLowerCase().trim();
            renderNormTable(filterNorms(q));
            renderClassTable(filterClasses(q));
        } catch (err) {
            showError("Erro ao carregar dados: " + err.message);
        } finally {
            loading.style.display = "none";
        }
    }

    document.getElementById("btn-refresh").addEventListener("click", loadData);

    document.getElementById("btn-clear-kb").addEventListener("click", async () => {
        if (!confirm("Tem certeza que deseja limpar toda a base de conhecimento?\n\nIsso removerá todas as normalizações e classificações aprendidas.")) {
            return;
        }

        try {
            const res = await fetch("/api/knowledge-base", { method: "DELETE" });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            loadData();
        } catch (err) {
            showError("Erro ao limpar KB: " + err.message);
        }
    });

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function showError(msg) {
        const banner = document.getElementById("error-banner");
        document.getElementById("error-message").textContent = msg;
        banner.style.display = "flex";
    }

    document.getElementById("btn-close-error").addEventListener("click", () => {
        document.getElementById("error-banner").style.display = "none";
    });

    loadData();
});
