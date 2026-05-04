const API = "http://localhost:8000/api";

// ──────────────────────────────── UTILS ────────────────────────────────

const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function toast(msg, type = "ok") {
  const c = $("#toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type === "ok" ? "" : type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

async function api(method, path, body) {
  try {
    const res = await fetch(API + path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.erro || "Erro desconhecido");
    return data;
  } catch (e) {
    toast(e.message, "error");
    throw e;
  }
}

function fmt(n) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(n);
}

function statusBadge(qtd, min) {
  if (qtd === 0)  return `<span class="badge badge-danger">Zerado</span>`;
  if (qtd <= min) return `<span class="badge badge-warn">Baixo</span>`;
  return `<span class="badge badge-ok">Normal</span>`;
}

// ──────────────────────────────── NAV ────────────────────────────────

$$(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    $$(".nav-btn").forEach(b => b.classList.remove("active"));
    $$(".section").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    const sec = btn.dataset.section;
    $(`#sec-${sec}`).classList.add("active");
    if (sec === "dashboard") loadDashboard();
    if (sec === "produtos")  loadProdutos();
    if (sec === "movs")      loadMovimentacoes();
  });
});

// ──────────────────────────────── DASHBOARD ────────────────────────────────

async function loadDashboard() {
  const d = await api("GET", "/dashboard");
  $("#stat-total").textContent   = d.total_produtos;
  $("#stat-baixo").textContent   = d.estoque_baixo;
  $("#stat-valor").textContent   = fmt(d.valor_total);
  const entradas = d.movimentacoes_semana.entrada || 0;
  const saidas   = d.movimentacoes_semana.saida   || 0;
  $("#stat-movs").textContent    = entradas + saidas;

  const catGrid = $("#cat-grid");
  catGrid.innerHTML = d.categorias.map(c => `
    <div class="cat-card">
      <div class="cat-name">${c.categoria}</div>
      <div class="cat-count">${c.qtd}</div>
      <div style="font-size:.75rem;color:var(--muted)">${c.total_itens} unidades</div>
    </div>
  `).join("");
}

// ──────────────────────────────── PRODUTOS ────────────────────────────────

let todosProdutos = [];

async function loadProdutos(filtros = {}) {
  const params = new URLSearchParams(filtros).toString();
  todosProdutos = await api("GET", "/produtos" + (params ? `?${params}` : ""));
  renderTabela(todosProdutos);
}

function renderTabela(produtos) {
  const tbody = $("#tbody-produtos");
  if (!produtos.length) {
    tbody.innerHTML = `<tr><td colspan="7">
      <div class="empty-state"><div class="icon">📦</div>Nenhum produto encontrado</div>
    </td></tr>`;
    return;
  }
  tbody.innerHTML = produtos.map(p => `
    <tr>
      <td><span style="font-family:var(--mono);color:var(--muted)">#${p.id}</span></td>
      <td style="font-weight:500">${p.nome}</td>
      <td><span class="badge" style="background:var(--surface2);color:var(--text);border:1px solid var(--border)">${p.categoria}</span></td>
      <td style="font-family:var(--mono)">${p.quantidade}</td>
      <td style="font-family:var(--mono)">${fmt(p.preco)}</td>
      <td>${statusBadge(p.quantidade, p.estoque_minimo)}</td>
      <td>
        <div style="display:flex;gap:.4rem">
          <button class="btn btn-sm btn-ghost btn-icon" onclick="abrirMovimentacao(${p.id}, '${p.nome.replace(/'/g,"\\'")}', ${p.quantidade})" title="Movimentar">↕</button>
          <button class="btn btn-sm btn-secondary" onclick="editarProduto(${p.id})">Editar</button>
          <button class="btn btn-sm btn-danger" onclick="deletarProduto(${p.id}, '${p.nome.replace(/'/g,"\\'")}')">✕</button>
        </div>
      </td>
    </tr>
  `).join("");
}

// ── Filtros ao vivo
$("#search-input").addEventListener("input", aplicarFiltros);
$("#filter-cat").addEventListener("change", aplicarFiltros);

function aplicarFiltros() {
  const busca = $("#search-input").value.toLowerCase();
  const cat   = $("#filter-cat").value;
  let lista = todosProdutos;
  if (busca) lista = lista.filter(p => p.nome.toLowerCase().includes(busca) || p.categoria.toLowerCase().includes(busca));
  if (cat)   lista = lista.filter(p => p.categoria === cat);
  renderTabela(lista);
}

function preencherSelectCategorias(produtos) {
  const cats = [...new Set(produtos.map(p => p.categoria))].sort();
  const sel  = $("#filter-cat");
  sel.innerHTML = `<option value="">Todas as categorias</option>` +
    cats.map(c => `<option>${c}</option>`).join("");
}

let editandoId = null;

$("#btn-novo-produto").addEventListener("click", () => abrirModalProduto(null));

function abrirModalProduto(produto) {
  editandoId = produto ? produto.id : null;
  $("#modal-produto-title").textContent = produto ? "Editar Produto" : "Novo Produto";
  $("#campo-nome").value          = produto?.nome          ?? "";
  $("#campo-categoria").value     = produto?.categoria     ?? "";
  $("#campo-quantidade").value    = produto?.quantidade    ?? 0;
  $("#campo-preco").value         = produto?.preco         ?? "";
  $("#campo-estoque-min").value   = produto?.estoque_minimo?? 5;
  $("#modal-produto").classList.add("open");
  $("#campo-nome").focus();
}

async function editarProduto(id) {
  const p = todosProdutos.find(x => x.id === id);
  if (p) abrirModalProduto(p);
}

$("#form-produto").addEventListener("submit", async e => {
  e.preventDefault();
  const body = {
    nome:           $("#campo-nome").value.trim(),
    categoria:      $("#campo-categoria").value.trim(),
    quantidade:     parseInt($("#campo-quantidade").value),
    preco:          parseFloat($("#campo-preco").value),
    estoque_minimo: parseInt($("#campo-estoque-min").value),
  };
  if (!body.nome || !body.categoria) return toast("Preencha nome e categoria", "warn");
  if (editandoId) {
    await api("PUT", `/produtos/${editandoId}`, body);
    toast("Produto atualizado ✓");
  } else {
    await api("POST", "/produtos", body);
    toast("Produto criado ✓");
  }
  fecharModal("modal-produto");
  loadProdutos();
});

async function deletarProduto(id, nome) {
  if (!confirm(`Remover "${nome}"?`)) return;
  await api("DELETE", `/produtos/${id}`);
  toast(`"${nome}" removido`, "warn");
  loadProdutos();
}

function abrirMovimentacao(id, nome, qtdAtual) {
  $("#mov-produto-info").textContent = `${nome} — estoque atual: ${qtdAtual}`;
  $("#mov-produto-id").value  = id;
  $("#mov-tipo").value        = "entrada";
  $("#mov-quantidade").value  = 1;
  $("#mov-obs").value         = "";
  $("#modal-movimentacao").classList.add("open");
  $("#mov-quantidade").focus();
}

$("#form-movimentacao").addEventListener("submit", async e => {
  e.preventDefault();
  const body = {
    produto_id: parseInt($("#mov-produto-id").value),
    tipo:       $("#mov-tipo").value,
    quantidade: parseInt($("#mov-quantidade").value),
    observacao: $("#mov-obs").value.trim() || null,
  };
  await api("POST", "/movimentacoes", body);
  toast(`Movimentação registrada ✓`);
  fecharModal("modal-movimentacao");
  loadProdutos();
  // Se aba de movimentações estiver aberta, atualiza
  if ($("#sec-movs").classList.contains("active")) loadMovimentacoes();
});

async function loadMovimentacoes() {
  const movs = await api("GET", "/movimentacoes");
  const tbody = $("#tbody-movs");
  if (!movs.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="icon">📋</div>Sem movimentações ainda</div></td></tr>`;
    return;
  }
  tbody.innerHTML = movs.map(m => {
    const cor = m.tipo === "entrada" ? "badge-entrada" : "badge-danger";
    const sinal = m.tipo === "entrada" ? "+" : "-";
    return `
    <tr>
      <td><span style="font-family:var(--mono);color:var(--muted)">#${m.id}</span></td>
      <td style="font-weight:500">${m.produto_nome || "-"}</td>
      <td><span class="badge ${cor}">${m.tipo}</span></td>
      <td style="font-family:var(--mono);color:${m.tipo==="entrada"?"var(--accent2)":"var(--danger)"}">${sinal}${m.quantidade}</td>
      <td style="color:var(--muted);font-size:.82rem">${m.observacao || "-"}</td>
      <td style="font-family:var(--mono);font-size:.78rem;color:var(--muted)">${new Date(m.criado_em).toLocaleString("pt-BR")}</td>
    </tr>`;
  }).join("");
}

function fecharModal(id) {
  $(`#${id}`).classList.remove("open");
}

$$(".modal-overlay").forEach(m => {
  m.addEventListener("click", e => {
    if (e.target === m) m.classList.remove("open");
  });
});

$$(".modal-close").forEach(btn => {
  btn.addEventListener("click", () => {
    btn.closest(".modal-overlay").classList.remove("open");
  });
});

(async () => {
  await loadDashboard();
  const prods = await api("GET", "/produtos");
  todosProdutos = prods;
  preencherSelectCategorias(prods);
  renderTabela(prods);
})();
