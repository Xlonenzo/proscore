/* PASSA - Frontend JavaScript v2 */

const API_BASE = '/api';

// ====== Mobile Navigation ======

(function initNav() {
    const toggle = document.querySelector('.nav-toggle');
    const menu = document.getElementById('nav-menu');
    if (!toggle || !menu) return;

    toggle.addEventListener('click', () => {
        const isOpen = menu.classList.toggle('open');
        toggle.setAttribute('aria-expanded', isOpen);
        toggle.setAttribute('aria-label', isOpen ? 'Fechar menu' : 'Abrir menu');
    });

    // Close menu when clicking a link
    menu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            menu.classList.remove('open');
            toggle.setAttribute('aria-expanded', 'false');
        });
    });

    // Close on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && menu.classList.contains('open')) {
            menu.classList.remove('open');
            toggle.setAttribute('aria-expanded', 'false');
            toggle.focus();
        }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (menu.classList.contains('open') && !menu.contains(e.target) && !toggle.contains(e.target)) {
            menu.classList.remove('open');
            toggle.setAttribute('aria-expanded', 'false');
        }
    });
})();

// ====== Toast Notifications ======

function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
        error: '<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
        info: '<svg viewBox="0 0 20 20" fill="currentColor" class="toast-icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>',
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span>${message}</span>
        <button class="toast-close" aria-label="Fechar notificacao">&times;</button>
    `;

    container.appendChild(toast);

    const close = () => {
        toast.classList.add('toast-out');
        toast.addEventListener('animationend', () => toast.remove());
    };

    toast.querySelector('.toast-close').addEventListener('click', close);

    if (duration > 0) {
        setTimeout(close, duration);
    }
}

// ====== API Helper ======

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    };

    try {
        const response = await fetch(url, config);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Erro na requisicao');
        }
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ====== Photo Upload for Pricing ======

let _fotoBase64 = null;

function previewFoto(input) {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
        showToast('Foto muito grande. Maximo 5MB.', 'error');
        input.value = '';
        return;
    }
    const reader = new FileReader();
    reader.onload = function(e) {
        _fotoBase64 = e.target.result.split(',')[1]; // Remove data:image/...;base64, prefix
        document.getElementById('hero-foto-img').src = e.target.result;
        document.getElementById('hero-foto-preview').style.display = 'block';
    };
    reader.readAsDataURL(file);
}

function removerFoto() {
    _fotoBase64 = null;
    document.getElementById('hero-foto').value = '';
    document.getElementById('hero-foto-preview').style.display = 'none';
}

// ====== Precificacao Rapida (Hero) ======

// Store last pricing data for the "aceitar" flow
let _lastPrecificacao = null;
let _lastDescricao = '';

async function precificarRapido() {
    const input = document.getElementById('hero-servico');
    if (!input) return;

    const descricao = input.value.trim();
    if (!descricao) {
        input.focus();
        showToast('Digite o servico que voce precisa.', 'info');
        return;
    }

    const btn = document.getElementById('hero-btn');
    const resultDiv = document.getElementById('price-result');

    // Get regiao from address field if logged in
    const bairroInput = document.getElementById('hero-bairro');
    const urgenteCheck = document.getElementById('hero-urgente');
    const regiao = bairroInput ? bairroInput.value.trim() : '';
    const urgente = urgenteCheck ? urgenteCheck.checked : false;

    btn.disabled = true;
    btn.innerHTML = '<i class="fi fi-rr-spinner" aria-hidden="true"></i> Calculando...';

    try {
        const data = await apiCall('/precificar', {
            method: 'POST',
            body: JSON.stringify({
                descricao: descricao,
                regiao: regiao,
                urgente: urgente,
                foto_base64: _fotoBase64 || null,
            }),
        });

        const p = data.precificacao;
        _lastPrecificacao = p;
        _lastDescricao = descricao;

        document.getElementById('price-value').textContent = `R$ ${p.preco.toFixed(0)}`;
        document.getElementById('price-tempo').textContent = formatarTempo(p.tempo_estimado_min);
        document.getElementById('price-categoria').textContent = capitalize(p.categoria);
        document.getElementById('price-complexidade').textContent = `${p.complexidade}/5`;

        const detalhesEl = document.getElementById('price-detalhes');
        if (detalhesEl && p.detalhes) {
            detalhesEl.textContent = p.detalhes;
        }

        resultDiv.classList.add('show');
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
        console.error('Precificar error:', error);
        showToast('Erro ao precificar: ' + (error.message || 'Tente novamente'), 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fi fi-rr-search" aria-hidden="true"></i> Buscar preco';
    }
}

// ====== Salvar Endereco (auto-save on blur) ======

async function salvarEndereco() {
    const enderecoInput = document.getElementById('hero-endereco');
    const bairroInput = document.getElementById('hero-bairro');
    if (!enderecoInput || !bairroInput) return;

    const endereco = enderecoInput.value.trim();
    const bairro = bairroInput.value.trim();

    // Check if changed from original
    const form = document.getElementById('hero-logado-form');
    if (!form) return;
    const origEndereco = form.dataset.endereco || '';
    const origBairro = form.dataset.bairro || '';

    if (endereco === origEndereco && bairro === origBairro) return;

    try {
        await apiCall('/auth/endereco', {
            method: 'PUT',
            body: JSON.stringify({ endereco, bairro }),
        });
        // Update data attributes to prevent re-saving
        form.dataset.endereco = endereco;
        form.dataset.bairro = bairro;
        showToast('Endereco salvo!', 'success', 2000);
    } catch (error) {
        // Silent fail - address save is not critical
        console.error('Erro ao salvar endereco:', error);
    }
}

// ====== Aceitar Preco e Buscar Profissional ======

async function aceitarEBuscar() {
    const descricao = _lastDescricao || document.getElementById('hero-servico')?.value?.trim();
    if (!descricao) {
        showToast('Primeiro busque o preco do servico.', 'info');
        return;
    }

    const urgenteCheck = document.getElementById('hero-urgente');
    const urgente = urgenteCheck ? urgenteCheck.checked : false;
    const btn = document.getElementById('btn-aceitar');

    btn.disabled = true;
    btn.innerHTML = '<i class="fi fi-rr-spinner" aria-hidden="true"></i> Buscando profissionais...';

    try {
        const data = await apiCall('/solicitar-logado', {
            method: 'POST',
            body: JSON.stringify({ descricao, urgente }),
        });

        // Store solicitacao_id for choosing professional
        window._solicitacaoId = data.solicitacao_id;

        const profDiv = document.getElementById('profissionais-result');
        const grid = document.getElementById('profissionais-grid');

        if (data.profissionais_disponiveis && data.profissionais_disponiveis.length > 0) {
            let html = '';
            for (const prof of data.profissionais_disponiveis) {
                const scoreClass = getScoreClass(prof.score);
                const chegada = prof.tempo_chegada_min || 0;
                html += `
                    <div class="pro-card">
                        <div class="pro-chegada">
                            <i class="fi fi-rr-marker" aria-hidden="true"></i>
                            <span>${chegada} min</span>
                        </div>
                        <div class="pro-header">
                            <div class="pro-avatar">${getInitials(prof.nome)}</div>
                            <div class="pro-info">
                                <h3>${prof.nome}</h3>
                                <span class="categoria">${capitalize(prof.categoria)}</span>
                                ${prof.regiao ? `<span style="display:block;font-size:0.75rem;color:var(--text-muted)">${prof.regiao}</span>` : ''}
                            </div>
                            <div class="pro-score-badge ${scoreClass}">
                                <div class="pro-score-value">${prof.score.toFixed(0)}</div>
                                <div class="pro-score-label">score</div>
                            </div>
                        </div>
                        <div class="pro-stats">
                            <div class="pro-stat">
                                <div class="label">Avaliacao</div>
                                <div class="value">${prof.avaliacao_media.toFixed(1)}</div>
                            </div>
                            <div class="pro-stat">
                                <div class="label">Servicos</div>
                                <div class="value">${prof.total_servicos}</div>
                            </div>
                            <div class="pro-stat">
                                <div class="label">Conclusao</div>
                                <div class="value">${prof.taxa_conclusao.toFixed(0)}%</div>
                            </div>
                        </div>
                        <div class="pro-badges">
                            ${prof.documento_verificado ? '<span class="badge badge-verified">Verificado</span>' : ''}
                            ${prof.antecedentes_ok ? '<span class="badge badge-antecedentes">Antecedentes OK</span>' : ''}
                        </div>
                        <button onclick="escolherProfissional(${data.solicitacao_id}, ${prof.id})" class="btn btn-primary btn-escolher">
                            <i class="fi fi-rr-check" aria-hidden="true"></i> Escolher este profissional
                        </button>
                    </div>
                `;
            }
            grid.innerHTML = html;
            profDiv.style.display = 'block';
            profDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            grid.innerHTML = '<p style="text-align:center;color:var(--text-muted);grid-column:1/-1;padding:2rem">Nenhum profissional disponivel para esta categoria no momento.</p>';
            profDiv.style.display = 'block';
        }

        showToast('Solicitacao criada! Escolha seu profissional.', 'success');
    } catch (error) {
        showToast(error.message || 'Erro ao buscar profissionais.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fi fi-rr-check" aria-hidden="true"></i> Aceitar e buscar profissional';
    }
}

// ====== Escolher Profissional ======

async function escolherProfissional(solicitacaoId, profissionalId) {
    try {
        await apiCall(`/solicitacoes/${solicitacaoId}/aceitar`, {
            method: 'POST',
            body: JSON.stringify({ profissional_id: profissionalId }),
        });

        // Hide professionals grid, show confirmation
        document.getElementById('profissionais-result').style.display = 'none';
        document.getElementById('price-result').classList.remove('show');
        document.getElementById('confirmacao-result').style.display = 'flex';
        document.getElementById('confirmacao-result').scrollIntoView({ behavior: 'smooth', block: 'center' });

        showToast('Profissional escolhido com sucesso!', 'success');
    } catch (error) {
        showToast(error.message || 'Erro ao escolher profissional.', 'error');
    }
}

// ====== Solicitar Servico ======

async function solicitarServico(event) {
    event.preventDefault();
    const form = event.target;
    const btn = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('solicitar-result');

    btn.disabled = true;
    btn.textContent = 'Enviando...';

    try {
        const data = await apiCall('/solicitar', {
            method: 'POST',
            body: JSON.stringify({
                nome_cliente: form.nome.value,
                email_cliente: form.email.value,
                telefone_cliente: form.telefone.value,
                endereco: form.endereco.value,
                bairro: form.bairro.value,
                descricao: form.descricao.value,
                urgente: form.urgente?.checked || false,
            }),
        });

        const p = data.precificacao;

        let html = `
            <div class="alert alert-success">
                Solicitacao #${data.solicitacao_id} criada com sucesso!
            </div>
            <div class="price-result show" style="display:block">
                <h3 class="price-result-title">Preco fechado</h3>
                <div class="price-single">
                    <span class="price-value-big">R$ ${p.preco.toFixed(0)}</span>
                </div>
                <div class="price-details">
                    <div class="price-detail-item">
                        <div class="label">Tempo estimado</div>
                        <div class="value">${formatarTempo(p.tempo_estimado_min)}</div>
                    </div>
                    <div class="price-detail-item">
                        <div class="label">Categoria</div>
                        <div class="value">${capitalize(p.categoria)}</div>
                    </div>
                </div>
            </div>
        `;

        if (data.profissionais_disponiveis && data.profissionais_disponiveis.length > 0) {
            html += `<h3 style="margin: 2rem 0 1rem; text-align:center">Profissionais Disponiveis</h3>`;
            html += `<div class="pro-grid">`;
            for (const prof of data.profissionais_disponiveis) {
                const scoreClass = getScoreClass(prof.score);
                html += `
                    <a href="/profissional/${prof.id}" class="pro-card">
                        <div class="pro-header">
                            <div class="pro-avatar">${getInitials(prof.nome)}</div>
                            <div class="pro-info">
                                <h3>${prof.nome}</h3>
                            </div>
                            <div class="pro-score-badge ${scoreClass}">
                                <div class="pro-score-value">${prof.score.toFixed(0)}</div>
                                <div class="pro-score-label">score</div>
                            </div>
                        </div>
                        <div class="pro-stats">
                            <div class="pro-stat">
                                <div class="label">Avaliacao</div>
                                <div class="value">${prof.avaliacao_media.toFixed(1)}</div>
                            </div>
                            <div class="pro-stat">
                                <div class="label">Servicos</div>
                                <div class="value">${prof.total_servicos}</div>
                            </div>
                            <div class="pro-stat">
                                <div class="label">Verificado</div>
                                <div class="value">${prof.documento_verificado ? 'Sim' : 'Nao'}</div>
                            </div>
                        </div>
                    </a>
                `;
            }
            html += `</div>`;
        }

        resultDiv.innerHTML = html;
        resultDiv.scrollIntoView({ behavior: 'smooth' });
        showToast('Solicitacao enviada com sucesso!', 'success');
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-error">Erro: ${error.message}</div>`;
        showToast('Erro ao enviar solicitacao.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Solicitar Servico';
    }
}

// ====== Listar Profissionais ======

async function carregarProfissionais(categoria = '', regiao = '') {
    const container = document.getElementById('pro-list');
    const loading = document.getElementById('pro-loading');
    if (!container) return;

    // Show skeleton loading
    loading?.classList.add('show');
    container.innerHTML = '';

    try {
        let endpoint = '/profissionais?limit=50';
        if (categoria) endpoint += `&categoria=${categoria}`;
        if (regiao) endpoint += `&regiao=${encodeURIComponent(regiao)}`;

        const data = await apiCall(endpoint);

        if (data.profissionais.length === 0) {
            container.innerHTML = `
                <div style="text-align:center;padding:3rem 1rem;grid-column:1/-1">
                    <p style="color:var(--text-muted);font-size:1.1rem;margin-bottom:0.5rem">Nenhum profissional encontrado</p>
                    <p style="color:var(--text-muted);font-size:0.9rem">Tente outra categoria ou remova os filtros</p>
                </div>`;
            return;
        }

        let html = '';
        for (const prof of data.profissionais) {
            const scoreClass = getScoreClass(prof.score);
            html += `
                <a href="/profissional/${prof.id}" class="pro-card">
                    <div class="pro-header">
                        <div class="pro-avatar">
                            ${getInitials(prof.nome)}
                            ${prof.documento_verificado ? '<div class="verified-badge"></div>' : ''}
                        </div>
                        <div class="pro-info">
                            <h3>${prof.nome}</h3>
                            <span class="categoria">${capitalize(prof.categoria)}</span>
                        </div>
                        <div class="pro-score-badge ${scoreClass}">
                            <div class="pro-score-value">${prof.score.toFixed(0)}</div>
                            <div class="pro-score-label">score</div>
                        </div>
                    </div>
                    <div class="pro-stats">
                        <div class="pro-stat">
                            <div class="label">Avaliacao</div>
                            <div class="value">${prof.avaliacao_media.toFixed(1)}</div>
                        </div>
                        <div class="pro-stat">
                            <div class="label">Servicos</div>
                            <div class="value">${prof.total_servicos}</div>
                        </div>
                        <div class="pro-stat">
                            <div class="label">Conclusao</div>
                            <div class="value">${prof.taxa_conclusao.toFixed(0)}%</div>
                        </div>
                    </div>
                    <div class="pro-badges">
                        ${prof.documento_verificado ? '<span class="badge badge-verified">Verificado</span>' : ''}
                        ${prof.antecedentes_ok ? '<span class="badge badge-antecedentes">Antecedentes OK</span>' : ''}
                    </div>
                </a>
            `;
        }

        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p style="text-align:center;color:var(--danger);padding:2rem">Erro ao carregar: ${error.message}</p>`;
    } finally {
        loading?.classList.remove('show');
    }
}

// ====== Detalhe Profissional ======

async function carregarProfissionalDetalhe(id) {
    const container = document.getElementById('pro-detail');
    if (!container) return;

    try {
        const data = await apiCall(`/profissionais/${id}`);
        const s = data.score_info;
        const scorePct = (s.score / 1000) * 100;

        let html = `
            <div style="display:flex;gap:2rem;flex-wrap:wrap">
                <div style="flex:1;min-width:280px">
                    <div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:2rem">
                        <div class="pro-avatar" style="width:72px;height:72px;font-size:1.75rem">${getInitials(data.nome)}</div>
                        <div>
                            <h2 style="margin-bottom:0.25rem;font-size:1.5rem">${data.nome}</h2>
                            <span style="color:var(--text-muted);text-transform:uppercase;font-size:0.8rem;letter-spacing:0.5px;font-weight:500">${capitalize(data.categoria)}</span>
                            ${data.regiao ? `<br><span style="color:var(--text-secondary);font-size:0.85rem">${data.regiao}</span>` : ''}
                        </div>
                    </div>

                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:2rem">
                        <div class="price-detail-item">
                            <div class="label">Total Servicos</div>
                            <div class="value">${data.total_servicos}</div>
                        </div>
                        <div class="price-detail-item">
                            <div class="label">Taxa Conclusao</div>
                            <div class="value">${data.taxa_conclusao.toFixed(0)}%</div>
                        </div>
                        <div class="price-detail-item">
                            <div class="label">Tempo Medio</div>
                            <div class="value">${formatarTempo(data.tempo_medio_min)}</div>
                        </div>
                        <div class="price-detail-item">
                            <div class="label">Especialidades</div>
                            <div class="value" style="font-size:0.8rem">${data.especialidades || 'N/A'}</div>
                        </div>
                    </div>

                    <div class="pro-badges" style="margin-bottom:1.5rem">
                        ${data.documento_verificado ? '<span class="badge badge-verified">Documento Verificado</span>' : '<span class="badge" style="background:var(--warning-bg);color:#B45309">Documento Pendente</span>'}
                        ${data.antecedentes_ok ? '<span class="badge badge-antecedentes">Antecedentes OK</span>' : ''}
                        ${data.certificacoes ? `<span class="badge" style="background:var(--warning-bg);color:#B45309">${data.certificacoes}</span>` : ''}
                    </div>
                </div>

                <div style="flex:0 0 260px;text-align:center">
                    <div class="score-meter" style="--score-pct: ${scorePct}" role="img" aria-label="Score ${s.score.toFixed(0)} de 1000, nivel ${s.nivel}">
                        <div class="score-meter-circle">
                            <div class="score-meter-inner">
                                <div class="score-meter-value" style="color:${s.cor}">${s.score.toFixed(0)}</div>
                                <div class="score-meter-label">${s.nivel}</div>
                            </div>
                        </div>
                    </div>
                    <p style="margin-top:1rem;color:var(--text-secondary);font-size:0.85rem">${s.descricao}</p>
                </div>
            </div>

            <div class="score-breakdown">
                <h3 style="margin-bottom:1.5rem;font-size:1.1rem">Detalhamento do Score</h3>
        `;

        const breakdown = s.detalhamento;
        const labels = {
            pontualidade: 'Pontualidade',
            avaliacao: 'Avaliacao Media',
            reclamacoes: 'Sem Reclamacoes',
            frequencia: 'Frequencia de Uso',
            recorrencia: 'Clientes Recorrentes',
            compliance: 'Conformidade',
        };

        for (const [key, info] of Object.entries(breakdown)) {
            const maxPontos = parseFloat(info.peso) / 100 * 1000;
            const pct = maxPontos > 0 ? (info.pontos / maxPontos) * 100 : 0;
            html += `
                <div class="score-bar-item">
                    <div class="score-bar-header">
                        <span>${labels[key] || key} (${info.peso})</span>
                        <span>${info.pontos.toFixed(0)} pts</span>
                    </div>
                    <div class="score-bar-track" role="progressbar" aria-valuenow="${pct.toFixed(0)}" aria-valuemin="0" aria-valuemax="100">
                        <div class="score-bar-fill" style="width:${pct.toFixed(0)}%"></div>
                    </div>
                </div>
            `;
        }

        html += `</div>`;
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p style="color:var(--danger);text-align:center;padding:2rem">Erro ao carregar profissional: ${error.message}</p>`;
    }
}

// ====== Dashboard ======

async function carregarDashboard() {
    const container = document.getElementById('dashboard-content');
    if (!container) return;

    try {
        const data = await apiCall('/dashboard/stats');

        let html = `
            <div class="dashboard-stats">
                <div class="stat-card">
                    <div class="stat-value">${data.total_profissionais}</div>
                    <div class="stat-label">Profissionais</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.total_clientes}</div>
                    <div class="stat-label">Clientes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.total_solicitacoes}</div>
                    <div class="stat-label">Solicitacoes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.total_concluidos}</div>
                    <div class="stat-label">Concluidos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${data.total_pendentes}</div>
                    <div class="stat-label">Pendentes</div>
                </div>
            </div>
        `;

        if (data.top_profissionais && data.top_profissionais.length > 0) {
            html += `<h3 style="margin:2rem 0 1rem;font-size:1.1rem">Top Profissionais</h3>`;
            html += `<div class="pro-grid">`;
            for (const prof of data.top_profissionais) {
                const scoreClass = getScoreClass(prof.score);
                html += `
                    <a href="/profissional/${prof.id}" class="pro-card">
                        <div class="pro-header">
                            <div class="pro-avatar">${getInitials(prof.nome)}</div>
                            <div class="pro-info">
                                <h3>${prof.nome}</h3>
                                <span class="categoria">${capitalize(prof.categoria)}</span>
                            </div>
                            <div class="pro-score-badge ${scoreClass}">
                                <div class="pro-score-value">${prof.score.toFixed(0)}</div>
                                <div class="pro-score-label">score</div>
                            </div>
                        </div>
                    </a>
                `;
            }
            html += `</div>`;
        }

        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<p style="color:var(--danger);text-align:center;padding:2rem">Erro ao carregar dashboard: ${error.message}</p>`;
    }
}

// ====== Helpers ======

function formatarTempo(minutos) {
    if (!minutos || minutos === 0) return 'N/A';
    if (minutos < 60) return `${minutos}min`;
    const horas = Math.floor(minutos / 60);
    const min = minutos % 60;
    return min > 0 ? `${horas}h${min}min` : `${horas}h`;
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function getInitials(nome) {
    if (!nome) return '?';
    const parts = nome.split(' ');
    if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return nome[0].toUpperCase();
}

function getScoreClass(score) {
    if (score >= 850) return 'score-elite';
    if (score >= 700) return 'score-ouro';
    if (score >= 500) return 'score-prata';
    return 'score-bronze';
}

// ====== Enter key for hero input ======

document.addEventListener('DOMContentLoaded', () => {
    const heroInput = document.getElementById('hero-servico');
    if (heroInput) {
        heroInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                precificarRapido();
            }
        });
    }
});

// ====== Auth Functions ======

async function fazerLogin(event) {
    event.preventDefault();
    const btn = document.getElementById('login-btn');
    const alertEl = document.getElementById('login-alert');
    const email = document.getElementById('login-email').value.trim();
    const senha = document.getElementById('login-senha').value;

    if (!email || !senha) {
        alertEl.textContent = 'Preencha email e senha.';
        alertEl.style.display = 'flex';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Entrando...';
    alertEl.style.display = 'none';

    try {
        await apiCall('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, senha }),
        });
        showToast('Login realizado com sucesso!', 'success');
        window.location.href = '/';
    } catch (error) {
        alertEl.textContent = error.message || 'Email ou senha incorretos';
        alertEl.style.display = 'flex';
        showToast(error.message || 'Erro ao fazer login', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fi fi-rr-sign-in-alt" aria-hidden="true"></i> Entrar';
    }
}

async function registrarCliente(event) {
    event.preventDefault();
    const btn = document.getElementById('reg-btn');
    const alertEl = document.getElementById('registro-alert');
    const form = document.getElementById('registro-cliente-form');

    const nome = form.nome.value.trim();
    const email = form.email.value.trim();
    const senha = form.senha.value;
    const telefone = form.telefone.value.trim();
    const endereco = form.endereco ? form.endereco.value.trim() : '';
    const bairro = form.bairro ? form.bairro.value.trim() : '';

    if (!nome || !email || !senha || !telefone) {
        alertEl.textContent = 'Preencha todos os campos obrigatorios.';
        alertEl.style.display = 'flex';
        return;
    }

    if (senha.length < 6) {
        alertEl.textContent = 'A senha deve ter no minimo 6 caracteres.';
        alertEl.style.display = 'flex';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Criando conta...';
    alertEl.style.display = 'none';

    try {
        await apiCall('/auth/registro/cliente', {
            method: 'POST',
            body: JSON.stringify({ nome, email, senha, telefone, endereco, bairro }),
        });
        showToast('Conta criada com sucesso!', 'success');
        window.location.href = '/';
    } catch (error) {
        alertEl.textContent = error.message || 'Erro ao criar conta';
        alertEl.style.display = 'flex';
        showToast(error.message || 'Erro ao criar conta', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fi fi-rr-user-add" aria-hidden="true"></i> Criar minha conta';
    }
}

async function registrarPrestador(event) {
    event.preventDefault();
    const btn = document.getElementById('reg-btn');
    const alertEl = document.getElementById('registro-alert');
    const form = document.getElementById('registro-prestador-form');

    const nome = form.nome.value.trim();
    const email = form.email.value.trim();
    const senha = form.senha.value;
    const telefone = form.telefone.value.trim();
    const cpf = form.cpf.value.trim();
    const categoria = form.categoria.value;
    const especialidades = form.especialidades ? form.especialidades.value.trim() : '';
    const regiao = form.regiao ? form.regiao.value.trim() : 'Sao Paulo';

    if (!nome || !email || !senha || !telefone || !cpf || !categoria) {
        alertEl.textContent = 'Preencha todos os campos obrigatorios.';
        alertEl.style.display = 'flex';
        return;
    }

    if (senha.length < 6) {
        alertEl.textContent = 'A senha deve ter no minimo 6 caracteres.';
        alertEl.style.display = 'flex';
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Criando conta...';
    alertEl.style.display = 'none';

    try {
        await apiCall('/auth/registro/prestador', {
            method: 'POST',
            body: JSON.stringify({ nome, email, senha, telefone, cpf, categoria, especialidades, regiao }),
        });
        showToast('Conta de prestador criada com sucesso!', 'success');
        window.location.href = '/';
    } catch (error) {
        alertEl.textContent = error.message || 'Erro ao criar conta';
        alertEl.style.display = 'flex';
        showToast(error.message || 'Erro ao criar conta', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fi fi-rr-user-add" aria-hidden="true"></i> Criar minha conta';
    }
}

async function fazerLogout() {
    try {
        await apiCall('/auth/logout', { method: 'POST' });
        showToast('Logout realizado', 'info');
        window.location.href = '/';
    } catch (error) {
        window.location.href = '/';
    }
}
