/**
 * Renderiza a trie de prefixos retornada pela API (campo trie_tree).
 */
(function (global) {
    function esc(s) {
        if (s == null || s === "") return "";
        const d = document.createElement("div");
        d.textContent = String(s);
        return d.innerHTML;
    }

    function appendNode(container, node) {
        const wrap = document.createElement("div");
        wrap.className = "tree-node";

        const line = document.createElement("div");
        line.className = "tree-node-line";

        if (node.normalized_id === "ROOT") {
            const n = (node.children && node.children.length) || 0;
            line.innerHTML =
                '<span class="tree-root-label">Início da suíte</span>' +
                `<span class="tree-meta">${n} ramo(s) a partir da raiz</span>`;
        } else {
            const badges = [];
            if (node.step_type === "verification") {
                badges.push('<span class="badge badge-type">Verificação</span>');
            } else {
                badges.push('<span class="badge badge-action">Ação</span>');
            }
            if (node.is_destructive) {
                badges.push('<span class="badge badge-destructive">Destrutivo</span>');
            }
            let pass = "";
            if (node.validates_tests && node.validates_tests.length) {
                pass = node.validates_tests
                    .map((t) => `<span class="badge badge-pass">PASSA ${esc(t)}</span>`)
                    .join(" ");
            }
            const text = node.step_text || node.normalized_id || "";
            line.innerHTML =
                `<span class="tree-step-text">${esc(text)}</span>` +
                `<code class="tree-nid">${esc(node.normalized_id)}</code>` +
                `<span class="tree-badges">${badges.join(" ")} ${pass}</span>`;
        }

        wrap.appendChild(line);

        if (node.children && node.children.length) {
            const kids = document.createElement("div");
            kids.className = "tree-children";
            node.children.forEach((ch) => appendNode(kids, ch));
            wrap.appendChild(kids);
        }

        container.appendChild(wrap);
    }

    global.appendTrieTree = function (containerEl, trieRoot) {
        if (!containerEl) return;
        containerEl.innerHTML = "";
        if (!trieRoot) return;
        appendNode(containerEl, trieRoot);
    };
})(window);
