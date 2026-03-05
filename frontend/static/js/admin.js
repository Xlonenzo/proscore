/* PASSA Admin Dashboard JS */

const ADMIN_API = '/api/admin';
let _searchTimer = null;
let _currentPageUsuarios = 1;
let _currentPageSolicitacoes = 1;

// ====== Sidebar Toggle ======

function toggleAdminSidebar() {
    document.getElementById('admin-sidebar').classList.toggle('open');
}

// ====== Dashboard ======

async function loadDashboard() {
    try {
        const data = await apiCall('/admin/analytics/overview');

        document.getElementById('kpi-usuarios').textContent = data.total_usuarios;
        document.getElementById('kpi-solicitacoes').textContent = data.total_solicitacoes;
        document.getElementById('kpi-receita').textContent = formatCurrency(data.receita_total);
        document.getElementById('kpi-avaliacao').textContent = data.avaliacao_media ? data.avaliacao_media.toFixed(1) : '—';

        document.getElementById('stat-sol-mes').textContent = data.solicitacoes_mes;
        document.getElementById('stat-taxa').textContent = data.taxa_conclusao + '%';
        document.getElementById('stat-clientes').textContent = data.total_clientes;
        document.getElementById('stat-prestadores').textContent = data.total_prestadores;

        // Activity list
        const list = document.getElementById('activity-list');
        if (data.recentes && data.recentes.length > 0) {
            list.innerHTML = data.recentes.map(s => `
                <div class="admin-activity-item">
                    <span class="admin-badge-status badge-${s.status}">${statusLabel(s.status)}</span>
                    <span class="desc">${escapeHtml(s.descricao)}</span>
                    <span class="time">${formatDate(s.criado_em)}</span>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<p class="text-muted">Nenhuma atividade recente.</p>';
        }
    } catch (e) {
        showToast('Erro ao carregar dashboard: ' + e.message, 'error');
    }
}

// ====== Usuarios ======

function debounceSearch() {
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(() => { _currentPageUsuarios = 1; loadUsuarios(); }, 400);
}

async function loadUsuarios(page) {
    if (page) _currentPageUsuarios = page;
    const busca = document.getElementById('busca-usuario')?.value || '';
    const tipo = document.getElementById('filtro-tipo')?.value || '';
    const ativo = document.getElementById('filtro-ativo')?.value || '';

    try {
        const params = new URLSearchParams({ busca, tipo, ativo, page: _currentPageUsuarios });
        const data = await apiCall('/admin/usuarios?' + params);

        const tbody = document.getElementById('usuarios-tbody');
        if (data.usuarios.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Nenhum usuario encontrado.</td></tr>';
        } else {
            tbody.innerHTML = data.usuarios.map(u => `
                <tr>
                    <td>${u.id}</td>
                    <td><strong>${escapeHtml(u.nome)}</strong>${u.is_admin ? ' <span class="admin-badge">Admin</span>' : ''}</td>
                    <td>${escapeHtml(u.email)}</td>
                    <td><span class="admin-badge-status badge-${u.tipo}">${u.tipo}</span></td>
                    <td><span class="admin-badge-status ${u.ativo ? 'badge-ativo' : 'badge-suspenso'}">${u.ativo ? 'Ativo' : 'Suspenso'}</span></td>
                    <td>${formatDate(u.criado_em)}</td>
                    <td>
                        ${u.is_admin ? '' : (u.ativo
                            ? `<button class="admin-btn admin-btn-danger" onclick="suspenderUsuario(${u.id})">Suspender</button>`
                            : `<button class="admin-btn admin-btn-success" onclick="reativarUsuario(${u.id})">Reativar</button>`
                        )}
                    </td>
                </tr>
            `).join('');
        }

        renderPagination('usuarios-pagination', data.page, data.pages, 'loadUsuarios');
    } catch (e) {
        showToast('Erro ao carregar usuarios: ' + e.message, 'error');
    }
}

async function suspenderUsuario(id) {
    if (!confirm('Suspender este usuario?')) return;
    try {
        await apiCall(`/admin/usuarios/${id}/suspender`, { method: 'POST' });
        showToast('Usuario suspenso com sucesso.', 'success');
        loadUsuarios();
    } catch (e) {
        showToast('Erro: ' + e.message, 'error');
    }
}

async function reativarUsuario(id) {
    try {
        await apiCall(`/admin/usuarios/${id}/reativar`, { method: 'POST' });
        showToast('Usuario reativado com sucesso.', 'success');
        loadUsuarios();
    } catch (e) {
        showToast('Erro: ' + e.message, 'error');
    }
}

// ====== Solicitacoes ======

async function loadSolicitacoes(page) {
    if (page) _currentPageSolicitacoes = page;
    const status = document.getElementById('filtro-status')?.value || '';
    const categoria = document.getElementById('filtro-categoria')?.value || '';

    try {
        const params = new URLSearchParams({ status, categoria, page: _currentPageSolicitacoes });
        const data = await apiCall('/admin/solicitacoes?' + params);

        const tbody = document.getElementById('solicitacoes-tbody');
        if (data.solicitacoes.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Nenhuma solicitacao encontrada.</td></tr>';
        } else {
            tbody.innerHTML = data.solicitacoes.map(s => `
                <tr>
                    <td>${s.id}</td>
                    <td title="${escapeHtml(s.descricao)}">${escapeHtml(s.descricao)}</td>
                    <td><span style="text-transform:capitalize">${s.categoria}</span></td>
                    <td><span class="admin-badge-status badge-${s.status}">${statusLabel(s.status)}</span></td>
                    <td>${s.preco_final ? formatCurrency(s.preco_final) : '—'}</td>
                    <td>${escapeHtml(s.cliente_nome)}</td>
                    <td>${escapeHtml(s.profissional_nome)}</td>
                    <td>${formatDate(s.criado_em)}</td>
                    <td>
                        ${s.status !== 'cancelado' && s.status !== 'concluido'
                            ? `<button class="admin-btn admin-btn-danger" onclick="cancelarSolicitacao(${s.id})">Cancelar</button>`
                            : ''}
                    </td>
                </tr>
            `).join('');
        }

        renderPagination('solicitacoes-pagination', data.page, data.pages, 'loadSolicitacoes');
    } catch (e) {
        showToast('Erro ao carregar solicitacoes: ' + e.message, 'error');
    }
}

async function cancelarSolicitacao(id) {
    if (!confirm('Cancelar esta solicitacao?')) return;
    try {
        await apiCall(`/admin/solicitacoes/${id}/cancelar`, { method: 'POST' });
        showToast('Solicitacao cancelada.', 'success');
        loadSolicitacoes();
    } catch (e) {
        showToast('Erro: ' + e.message, 'error');
    }
}

// ====== Prestadores (todos) ======

let _currentPagePrestadores = 1;
let _prestadorSearchTimer = null;

function debouncePrestadorSearch() {
    clearTimeout(_prestadorSearchTimer);
    _prestadorSearchTimer = setTimeout(() => { _currentPagePrestadores = 1; loadPrestadores(); }, 400);
}

async function loadPrestadores(page) {
    if (page) _currentPagePrestadores = page;
    const busca = document.getElementById('busca-prestador')?.value || '';
    const categoria = document.getElementById('filtro-cat-prest')?.value || '';
    const ativo = document.getElementById('filtro-ativo-prest')?.value || '';

    try {
        const params = new URLSearchParams({ busca, categoria, ativo, page: _currentPagePrestadores });
        const data = await apiCall('/admin/prestadores?' + params);

        const tbody = document.getElementById('prestadores-tbody');
        if (data.prestadores.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">Nenhum prestador encontrado.</td></tr>';
        } else {
            tbody.innerHTML = data.prestadores.map(p => `
                <tr>
                    <td>${p.id}</td>
                    <td>
                        <strong>${escapeHtml(p.nome)}</strong>
                        <div style="font-size:0.75rem;color:var(--text-muted)">${escapeHtml(p.email)}</div>
                    </td>
                    <td><span style="text-transform:capitalize">${p.categoria}</span></td>
                    <td>${escapeHtml(p.regiao || '—')}</td>
                    <td><strong>${p.score}</strong></td>
                    <td>${p.total_servicos}</td>
                    <td>${p.avaliacao_media ? p.avaliacao_media.toFixed(1) : '—'}</td>
                    <td>
                        <span class="${p.documento_verificado ? 'check-ok' : 'check-pending'}" title="Documento">
                            <i class="fi fi-rr-${p.documento_verificado ? 'check' : 'clock'}" aria-hidden="true"></i>
                        </span>
                        <span class="${p.antecedentes_ok ? 'check-ok' : 'check-pending'}" title="Antecedentes" style="margin-left:0.35rem">
                            <i class="fi fi-rr-${p.antecedentes_ok ? 'check' : 'clock'}" aria-hidden="true"></i>
                        </span>
                    </td>
                    <td><span class="admin-badge-status ${p.ativo ? 'badge-ativo' : 'badge-suspenso'}">${p.ativo ? 'Ativo' : 'Inativo'}</span></td>
                    <td>
                        ${!p.documento_verificado || !p.antecedentes_ok
                            ? `<button class="admin-btn admin-btn-success" onclick="aprovarPrestador(${p.id})" title="Aprovar">Aprovar</button> `
                            : ''}
                        <a href="/profissional/${p.id}" class="admin-btn admin-btn-primary" target="_blank" title="Ver perfil">Ver</a>
                    </td>
                </tr>
            `).join('');
        }

        renderPagination('prestadores-pagination', data.page, data.pages, 'loadPrestadores');
    } catch (e) {
        showToast('Erro ao carregar prestadores: ' + e.message, 'error');
    }
}

// ====== Prestadores Pendentes ======

async function loadPrestadoresPendentes() {
    try {
        const data = await apiCall('/admin/prestadores/pendentes');
        const countEl = document.getElementById('pendentes-count');
        const listEl = document.getElementById('pendentes-list');
        const emptyEl = document.getElementById('pendentes-empty');

        countEl.textContent = `${data.total} prestador(es) pendente(s) de aprovacao`;

        if (data.pendentes.length === 0) {
            listEl.style.display = 'none';
            emptyEl.style.display = 'block';
        } else {
            emptyEl.style.display = 'none';
            listEl.style.display = 'grid';
            listEl.innerHTML = data.pendentes.map(p => `
                <div class="admin-pendente-card">
                    <h4>${escapeHtml(p.nome)}</h4>
                    <div class="meta">
                        ${escapeHtml(p.email)}<br>
                        ${escapeHtml(p.telefone)}<br>
                        <strong>Categoria:</strong> <span style="text-transform:capitalize">${p.categoria}</span><br>
                        <strong>Regiao:</strong> ${escapeHtml(p.regiao || '—')}
                    </div>
                    <div class="checks">
                        <span class="${p.documento_verificado ? 'check-ok' : 'check-pending'}">
                            <i class="fi fi-rr-${p.documento_verificado ? 'check' : 'clock'}" aria-hidden="true"></i>
                            Documento
                        </span>
                        <span class="${p.antecedentes_ok ? 'check-ok' : 'check-pending'}">
                            <i class="fi fi-rr-${p.antecedentes_ok ? 'check' : 'clock'}" aria-hidden="true"></i>
                            Antecedentes
                        </span>
                    </div>
                    <button class="admin-btn admin-btn-success" onclick="aprovarPrestador(${p.id})">
                        <i class="fi fi-rr-check" aria-hidden="true"></i> Aprovar
                    </button>
                </div>
            `).join('');
        }
    } catch (e) {
        showToast('Erro ao carregar prestadores: ' + e.message, 'error');
    }
}

async function aprovarPrestador(id) {
    try {
        await apiCall(`/admin/prestadores/${id}/aprovar`, { method: 'POST' });
        showToast('Prestador aprovado com sucesso!', 'success');
        loadPrestadoresPendentes();
    } catch (e) {
        showToast('Erro: ' + e.message, 'error');
    }
}

// ====== Analytics ======

async function loadAnalytics() {
    try {
        const [overview, revenue, categorias, statusData, crescimento, topPrest, ticketData] = await Promise.all([
            apiCall('/admin/analytics/overview'),
            apiCall('/admin/analytics/revenue?meses=6'),
            apiCall('/admin/analytics/categorias'),
            apiCall('/admin/analytics/status'),
            apiCall('/admin/analytics/crescimento?meses=6'),
            apiCall('/admin/analytics/top-prestadores?limit=10'),
            apiCall('/admin/analytics/ticket-medio?meses=6'),
        ]);

        // KPIs
        const el = id => document.getElementById(id);
        if (el('ak-receita')) el('ak-receita').textContent = formatCurrency(overview.receita_total);
        if (el('ak-taxa')) el('ak-taxa').textContent = overview.taxa_conclusao + '%';
        if (el('ak-usuarios')) el('ak-usuarios').textContent = overview.total_usuarios;

        // Ticket medio global
        const ticketTotal = ticketData.meses.filter(m => m.ticket_medio > 0);
        const avgTicket = ticketTotal.length > 0
            ? ticketTotal.reduce((s, m) => s + m.ticket_medio, 0) / ticketTotal.length
            : 0;
        if (el('ak-ticket')) el('ak-ticket').textContent = formatCurrency(avgTicket);

        renderBarChart('chart-revenue', revenue.meses, 'receita', 'var(--primary)');
        renderBarChart('chart-ticket', ticketData.meses, 'ticket_medio', 'var(--accent)');
        renderDonutChart('chart-status', statusData.status);
        renderHBarChart('chart-categorias', categorias.categorias);
        renderStackedBarChart('chart-crescimento', crescimento.meses);
        renderTopPrestadores('top-prestadores', topPrest.prestadores);
    } catch (e) {
        showToast('Erro ao carregar analytics: ' + e.message, 'error');
    }
}

function renderBarChart(containerId, meses, valueKey, color) {
    const container = document.getElementById(containerId);
    if (!meses || meses.length === 0) {
        container.innerHTML = '<p class="text-muted">Sem dados.</p>';
        return;
    }

    const maxVal = Math.max(...meses.map(m => m[valueKey]), 1);

    container.innerHTML = `
        <div class="admin-bar-chart">
            ${meses.map((m, i) => {
                const val = m[valueKey];
                const h = Math.max((val / maxVal) * 180, 2);
                // Gradual opacity for visual depth
                const opacity = 0.5 + (i / meses.length) * 0.5;
                return `
                    <div class="admin-bar-col">
                        <span class="admin-bar-value">${formatCurrency(val)}</span>
                        <div class="admin-bar" style="height:${h}px; background:${color}; opacity:${opacity.toFixed(2)};"></div>
                        <span class="admin-bar-label">${m.mes}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderDonutChart(containerId, statusList) {
    const container = document.getElementById(containerId);
    if (!statusList || statusList.length === 0) {
        container.innerHTML = '<p class="text-muted">Sem dados de status.</p>';
        return;
    }

    const total = statusList.reduce((s, x) => s + x.total, 0);
    const colorMap = {
        pendente: 'var(--warning)',
        aceito: 'var(--info)',
        em_andamento: 'var(--accent)',
        concluido: 'var(--success)',
        cancelado: 'var(--danger)',
    };

    // Build conic-gradient segments
    let gradientParts = [];
    let cumulative = 0;
    statusList.forEach(s => {
        const pct = (s.total / total) * 100;
        const color = colorMap[s.status] || 'var(--text-muted)';
        gradientParts.push(`${color} ${cumulative.toFixed(1)}% ${(cumulative + pct).toFixed(1)}%`);
        cumulative += pct;
    });

    container.innerHTML = `
        <div class="analytics-donut-wrap">
            <div class="analytics-donut" style="background: conic-gradient(${gradientParts.join(', ')});">
                <div class="analytics-donut-hole">
                    <span class="analytics-donut-total">${total}</span>
                    <span class="analytics-donut-label">Total</span>
                </div>
            </div>
            <div class="analytics-donut-legend">
                ${statusList.map(s => {
                    const pct = total > 0 ? ((s.total / total) * 100).toFixed(1) : 0;
                    const color = colorMap[s.status] || 'var(--text-muted)';
                    return `
                        <div class="analytics-legend-item">
                            <span class="analytics-legend-dot" style="background:${color};"></span>
                            <span class="analytics-legend-text">${statusLabel(s.status)}</span>
                            <span class="analytics-legend-val">${s.total} (${pct}%)</span>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
}

function renderHBarChart(containerId, categorias) {
    const container = document.getElementById(containerId);
    if (!categorias || categorias.length === 0) {
        container.innerHTML = '<p class="text-muted">Sem dados de categorias.</p>';
        return;
    }

    const maxVal = Math.max(...categorias.map(c => c.total), 1);
    const colors = ['var(--primary)', 'var(--cta)', 'var(--accent)', 'var(--success)', 'var(--warning)', 'var(--primary-light)', 'var(--info)', 'var(--danger)', 'var(--pink)'];

    container.innerHTML = `
        <div class="admin-hbar-chart">
            ${categorias.map((c, i) => {
                const w = Math.max((c.total / maxVal) * 100, 5);
                return `
                    <div class="admin-hbar-row">
                        <span class="admin-hbar-label">${c.categoria}</span>
                        <div class="admin-hbar-track">
                            <div class="admin-hbar" style="width:${w}%; background:${colors[i % colors.length]};">
                                ${c.total}
                            </div>
                        </div>
                        <span style="font-size:0.75rem; color:var(--text-muted); min-width:70px;">${formatCurrency(c.receita)}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderStackedBarChart(containerId, meses) {
    const container = document.getElementById(containerId);
    if (!meses || meses.length === 0) {
        container.innerHTML = '<p class="text-muted">Sem dados de crescimento.</p>';
        return;
    }

    const maxVal = Math.max(...meses.map(m => m.total), 1);

    container.innerHTML = `
        <div class="analytics-legend-row" style="margin-bottom:0.75rem;">
            <span class="analytics-legend-item" style="font-size:0.75rem;">
                <span class="analytics-legend-dot" style="background:var(--accent);"></span> Clientes
            </span>
            <span class="analytics-legend-item" style="font-size:0.75rem;">
                <span class="analytics-legend-dot" style="background:var(--primary);"></span> Prestadores
            </span>
        </div>
        <div class="admin-bar-chart">
            ${meses.map(m => {
                const hC = Math.max((m.clientes / maxVal) * 160, 0);
                const hP = Math.max((m.prestadores / maxVal) * 160, 0);
                return `
                    <div class="admin-bar-col">
                        <span class="admin-bar-value">${m.total}</span>
                        <div style="display:flex; flex-direction:column-reverse; align-items:center; width:100%;">
                            <div class="admin-bar" style="height:${hC}px; background:var(--accent); border-radius:0 0 4px 4px; width:100%;"></div>
                            <div class="admin-bar" style="height:${hP}px; background:var(--primary); border-radius:4px 4px 0 0; width:100%; margin-bottom:-1px;"></div>
                        </div>
                        <span class="admin-bar-label">${m.mes}</span>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderTopPrestadores(containerId, prestadores) {
    const container = document.getElementById(containerId);
    if (!prestadores || prestadores.length === 0) {
        container.innerHTML = '<p class="text-muted">Nenhum prestador encontrado.</p>';
        return;
    }

    const maxScore = Math.max(...prestadores.map(p => p.score), 1);

    container.innerHTML = `
        <div class="analytics-top-list">
            ${prestadores.map((p, i) => {
                const scorePct = (p.score / 1000) * 100;
                const medal = i === 0 ? 'analytics-medal-gold' : i === 1 ? 'analytics-medal-silver' : i === 2 ? 'analytics-medal-bronze' : '';
                return `
                    <div class="analytics-top-item ${medal}">
                        <span class="analytics-top-rank">${i + 1}</span>
                        <div class="analytics-top-info">
                            <div class="analytics-top-name">
                                ${escapeHtml(p.nome)}
                                <span class="admin-badge-status badge-prestador" style="margin-left:0.35rem;">${p.categoria}</span>
                            </div>
                            <div class="analytics-top-bar-track">
                                <div class="analytics-top-bar" style="width:${scorePct}%;"></div>
                            </div>
                        </div>
                        <div class="analytics-top-stats">
                            <span title="Score"><strong>${p.score}</strong> pts</span>
                            <span title="Servicos">${p.total_servicos} serv.</span>
                            <span title="Avaliacao">${p.avaliacao_media ? p.avaliacao_media.toFixed(1) + ' ★' : '—'}</span>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

// ====== Pagination ======

function renderPagination(containerId, currentPage, totalPages, fnName) {
    const container = document.getElementById(containerId);
    if (!container || totalPages <= 1) {
        if (container) container.innerHTML = '';
        return;
    }

    let html = '';
    if (currentPage > 1) {
        html += `<button class="admin-page-btn" onclick="${fnName}(${currentPage - 1})">&laquo;</button>`;
    }
    for (let i = 1; i <= totalPages; i++) {
        if (totalPages > 7 && i > 2 && i < totalPages - 1 && Math.abs(i - currentPage) > 1) {
            if (html.slice(-3) !== '...') html += '<span style="padding:0.4rem">...</span>';
            continue;
        }
        html += `<button class="admin-page-btn ${i === currentPage ? 'active' : ''}" onclick="${fnName}(${i})">${i}</button>`;
    }
    if (currentPage < totalPages) {
        html += `<button class="admin-page-btn" onclick="${fnName}(${currentPage + 1})">&raquo;</button>`;
    }
    container.innerHTML = html;
}

// ====== Helpers ======

function formatCurrency(value) {
    return 'R$ ' + Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(isoStr) {
    if (!isoStr) return '—';
    const d = new Date(isoStr);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

function statusLabel(status) {
    const labels = {
        pendente: 'Pendente',
        aceito: 'Aceito',
        em_andamento: 'Em andamento',
        concluido: 'Concluido',
        cancelado: 'Cancelado',
    };
    return labels[status] || status;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
