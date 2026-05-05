import { api, initSession, setTokens, state, fetchMe, updateHeaderByRole } from '/static/js/core/api.js';
import { notify, clearNotify, vagaStatusLabel, escapeHtml } from '/static/js/core/utils.js';

function renderPortalVagas(vagas) {
    const list = document.getElementById('vagas-list');
    list.innerHTML = '';
    if (!vagas.length) {
        list.innerHTML = '<div class="card">Nenhuma vaga encontrada.</div>';
        return;
    }

    vagas.forEach((vaga) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <h4>${escapeHtml(vaga.nome)}<span class="badge">${vagaStatusLabel(vaga.status)}</span></h4>
            <small>Empresa: ${escapeHtml(vaga.empresa_email || '-')}</small>
            <small>Escolaridade mínima: ${escapeHtml(vaga.escolaridade_minima)}</small>
            <small>Descrição resumida: ${escapeHtml((vaga.requisitos || '').slice(0, 120))}${(vaga.requisitos || '').length > 120 ? '...' : ''}</small>
        `;
        const actions = document.createElement('div');
        actions.className = 'actions';
        const btn = document.createElement('a');
        btn.className = 'btn btn-secondary';
        btn.href = `/vaga/${vaga.id}/`;
        btn.textContent = 'Ver detalhes';
        actions.appendChild(btn);
        card.appendChild(actions);
        list.appendChild(card);
    });
}

async function loadPortal() {
    try {
        const q = document.getElementById('search-keyword').value.trim();
        const url = '/api/vagas/' + (q ? `?q=${encodeURIComponent(q)}` : '');
        const data = await api(url);
        renderPortalVagas(data.results || []);
    } catch (error) {
        notify('Falha ao carregar vagas: ' + error.message, 'error');
    }
}

async function performLogin(email, password) {
    const data = await api('/api/auth/login/', {
        method: 'POST',
        body: { email, password },
    });
    setTokens(data.access, data.refresh);
    await fetchMe();
    updateHeaderByRole();
}

async function login() {
    clearNotify();
    try {
        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;
        await performLogin(email, password);
        if (state.me?.tipo === 'empresa') {
            window.location.assign('/empresa/');
            return;
        }
        document.getElementById('auth-screen').classList.add('hidden');
        document.getElementById('portal-screen').classList.remove('hidden');
        if (state.mustCompleteProfile) {
            notify('No primeiro acesso, complete o perfil do candidato para continuar.', 'error');
            window.location.assign('/perfil/');
            return;
        }
        await loadPortal();
        notify('Login realizado com sucesso.');
    } catch (error) {
        notify(error.message, 'error');
    }
}

function bindEvents() {
    document.getElementById('btn-login').addEventListener('click', login);
    document.getElementById('btn-search-vagas').addEventListener('click', loadPortal);
}

async function bootstrap() {
    bindEvents();
    await initSession({ allowGuest: true });
    if (!state.me) {
        document.getElementById('auth-screen').classList.remove('hidden');
        document.getElementById('portal-screen').classList.add('hidden');
        return;
    }
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('portal-screen').classList.remove('hidden');
    if (state.me.tipo === 'empresa') {
        window.location.assign('/empresa/');
        return;
    }
    if (state.mustCompleteProfile) {
        notify('Complete seu perfil para candidatar-se nas vagas.', 'error');
        window.location.assign('/perfil/');
        return;
    }
    await loadPortal();
}

bootstrap();
