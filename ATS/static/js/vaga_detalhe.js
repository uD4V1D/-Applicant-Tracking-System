import { api, initSession, state } from '/static/js/core/api.js';
import { notify, vagaStatusLabel, escapeHtml } from '/static/js/core/utils.js';

function vagaIdFromPath() {
    const match = window.location.pathname.match(/\/vaga\/(\d+)\/?$/);
    return match ? Number(match[1]) : null;
}

function renderDetalhe(vaga) {
    const box = document.getElementById('vaga-detalhes');
    box.innerHTML = `
        <div class="card">
            <h4>${escapeHtml(vaga.nome)}<span class="badge">${vagaStatusLabel(vaga.status)}</span></h4>
            <small>Empresa: ${escapeHtml(vaga.empresa_email || '-')}</small>
            <small>Faixa salarial: ${escapeHtml(vaga.faixa_salarial || '-')}</small>
            <small>Escolaridade mínima: ${escapeHtml(vaga.escolaridade_minima || '-')}</small>
            <small style="margin-top:8px;">Descrição completa:</small>
            <div style="margin-top:6px;">${escapeHtml(vaga.requisitos || '').replaceAll('\n', '<br>')}</div>
        </div>
    `;

    const btn = document.getElementById('btn-candidatar');
    const canApply = state.me && state.me.tipo === 'candidato' && !state.mustCompleteProfile && vaga.status === 'aberta';
    btn.classList.toggle('hidden', !canApply);
    btn.dataset.vagaId = String(vaga.id);
}

async function candidatar() {
    try {
        const vagaId = Number(document.getElementById('btn-candidatar').dataset.vagaId);
        await api('/api/candidaturas/', {
            method: 'POST',
            auth: true,
            body: { vaga: vagaId },
        });
        notify('Candidatura enviada com sucesso.');
    } catch (error) {
        notify('Falha ao candidatar: ' + error.message, 'error');
    }
}

async function bootstrap() {
    await initSession({ allowGuest: true });
    const vagaId = vagaIdFromPath();
    if (!vagaId) {
        notify('Vaga inválida.', 'error');
        return;
    }
    try {
        const vaga = await api(`/api/vagas/${vagaId}/`);
        renderDetalhe(vaga);
        document.getElementById('btn-candidatar').addEventListener('click', candidatar);
    } catch (error) {
        notify('Falha ao carregar detalhes da vaga: ' + error.message, 'error');
    }
}

bootstrap();
