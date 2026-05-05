import { api, initSession, state } from '/static/js/core/api.js';
import { notify, vagaStatusLabel, escapeHtml } from '/static/js/core/utils.js';

function toggleNovaVagaForm(forceOpen = null) {
    const box = document.getElementById('empresa-nova-vaga-box');
    const shouldOpen = forceOpen === null ? box.classList.contains('hidden') : forceOpen;
    box.classList.toggle('hidden', !shouldOpen);
}

function renderCompanyStatusSummary() {
    const totals = state.companyVagas.reduce(
        (acc, vaga) => {
            if (vaga.status === 'aberta') acc.abertas += 1;
            if (vaga.status === 'encerrada') acc.encerradas += 1;
            if (vaga.status === 'preenchida') acc.preenchidas += 1;
            return acc;
        },
        { abertas: 0, encerradas: 0, preenchidas: 0 },
    );
    document.getElementById('summary-abertas').textContent = String(totals.abertas);
    document.getElementById('summary-encerradas').textContent = String(totals.encerradas);
    document.getElementById('summary-preenchidas').textContent = String(totals.preenchidas);
}

function renderEmpresaTituloOptions() {
    const datalist = document.getElementById('empresa-titulo-options');
    datalist.innerHTML = '';
    state.companyVagas.forEach((vaga) => {
        const option = document.createElement('option');
        option.value = vaga.nome;
        datalist.appendChild(option);
    });
}

function getCompanyVagasFiltered() {
    const status = document.getElementById('empresa-filtro-status').value;
    const title = document.getElementById('empresa-filtro-titulo').value.trim().toLowerCase();
    return state.companyVagas.filter((vaga) => {
        const byStatus = !status || vaga.status === status;
        const byTitle = !title || (vaga.nome || '').toLowerCase().includes(title);
        return byStatus && byTitle;
    });
}

function renderMinhasVagas() {
    const vagas = getCompanyVagasFiltered();
    const list = document.getElementById('minhas-vagas-list');
    list.innerHTML = '';
    if (!vagas.length) {
        list.innerHTML = '<div class="card">Você ainda não possui vagas.</div>';
        return;
    }
    vagas.forEach((vaga) => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <h4>#${vaga.id} - ${escapeHtml(vaga.nome)}<span class="badge">${vagaStatusLabel(vaga.status)}</span></h4>
            <small>Faixa salarial: ${escapeHtml(vaga.faixa_salarial)}</small>
            <small>Escolaridade mínima: ${escapeHtml(vaga.escolaridade_minima)}</small>
            <small>Descrição: ${escapeHtml((vaga.requisitos || '').slice(0, 180))}${(vaga.requisitos || '').length > 180 ? '...' : ''}</small>
            <small class="candidate-count">📌 ${vaga.total_candidaturas || 0} candidatos</small>
        `;
        const actions = document.createElement('div');
        actions.className = 'actions';
        const btnOpen = document.createElement('a');
        btnOpen.className = 'btn';
        btnOpen.href = `/gestao-vaga/?id=${vaga.id}`;
        btnOpen.textContent = 'Abrir vaga';
        actions.appendChild(btnOpen);
        card.appendChild(actions);
        list.appendChild(card);
    });
}

async function loadMinhasVagas() {
    try {
        const vagas = await api('/api/vagas/minhas/', { auth: true });
        state.companyVagas = vagas;
        renderCompanyStatusSummary();
        renderEmpresaTituloOptions();
        renderMinhasVagas();
    } catch (error) {
        notify('Falha ao carregar gerenciamento de vagas: ' + error.message, 'error');
    }
}

async function createVaga() {
    try {
        const payload = {
            nome: document.getElementById('vaga-nome').value.trim(),
            faixa_salarial: document.getElementById('vaga-faixa').value,
            escolaridade_minima: document.getElementById('vaga-escolaridade').value,
            requisitos: document.getElementById('vaga-requisitos').value.trim(),
        };
        await api('/api/vagas/', {
            method: 'POST',
            auth: true,
            body: payload,
        });
        document.getElementById('vaga-nome').value = '';
        document.getElementById('vaga-requisitos').value = '';
        toggleNovaVagaForm(false);
        notify('Vaga criada com sucesso.');
        await loadMinhasVagas();
    } catch (error) {
        notify('Falha ao criar vaga: ' + error.message, 'error');
    }
}

function bindEvents() {
    document.getElementById('empresa-filtro-status').addEventListener('change', renderMinhasVagas);
    document.getElementById('empresa-filtro-titulo').addEventListener('input', renderMinhasVagas);
    document.getElementById('btn-toggle-nova-vaga').addEventListener('click', () => toggleNovaVagaForm(true));
    document.getElementById('btn-cancelar-nova-vaga').addEventListener('click', () => toggleNovaVagaForm(false));
    document.getElementById('btn-criar-vaga').addEventListener('click', createVaga);
    document.getElementById('btn-abrir-relatorios').addEventListener('click', () => window.location.assign('/relatorios/'));
}

async function bootstrap() {
    state.companyVagas = [];
    const me = await initSession({ requiredRole: 'empresa' });
    if (!me) return;
    bindEvents();
    await loadMinhasVagas();
}

bootstrap();
