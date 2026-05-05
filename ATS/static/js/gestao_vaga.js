import { api, initSession } from '/static/js/core/api.js';
import { notify, renderCandidateProfileModal, escapeHtml } from '/static/js/core/utils.js';

const ESCOLARIDADE_RANK = {
    fundamental: 1,
    medio: 2,
    tecnologo: 3,
    superior: 4,
    pos: 5,
    doutorado: 6,
};

function getVagaId() {
    const params = new URLSearchParams(window.location.search);
    const id = Number(params.get('id'));
    return Number.isFinite(id) && id > 0 ? id : null;
}

function setEditingMode(enabled) {
    const requisitos = document.getElementById('empresa-opened-requisitos');
    const status = document.getElementById('empresa-opened-status');
    const saveButton = document.getElementById('btn-empresa-salvar-edicao');
    if (!requisitos || !status || !saveButton) return;

    requisitos.disabled = !enabled;
    status.disabled = !enabled;
    saveButton.disabled = !enabled;
}

function isSalaryWithinRange(pretensaoSalarial, faixaSalarialVaga) {
    if (!Number.isFinite(pretensaoSalarial)) return false;
    if (faixaSalarialVaga === '1') return pretensaoSalarial <= 1000;
    if (faixaSalarialVaga === '2') return pretensaoSalarial >= 1000 && pretensaoSalarial <= 2000;
    if (faixaSalarialVaga === '3') return pretensaoSalarial >= 2000 && pretensaoSalarial <= 3000;
    if (faixaSalarialVaga === '4') return pretensaoSalarial > 3000;
    return false;
}

function getMatchScore(candidateProfile, vaga) {
    const pretensaoSalarial = Number(candidateProfile?.pretensao_salarial);
    const escolaridadeCandidato = candidateProfile?.escolaridade;
    const escolaridadeMinima = vaga?.escolaridade_minima;

    const salaryMatch = isSalaryWithinRange(pretensaoSalarial, vaga?.faixa_salarial);
    const escolaridadeCandidatoRank = ESCOLARIDADE_RANK[escolaridadeCandidato] || 0;
    const escolaridadeMinimaRank = ESCOLARIDADE_RANK[escolaridadeMinima] || 0;
    const educationMatch = escolaridadeCandidatoRank >= escolaridadeMinimaRank && escolaridadeMinimaRank > 0;

    let score = 0;
    if (salaryMatch) score += 1;
    if (educationMatch) score += 1;

    return { score, salaryMatch, educationMatch };
}

function renderCandidaturas(candidaturas, vaga) {
    const list = document.getElementById('empresa-candidaturas-list');
    list.innerHTML = '';
    if (!candidaturas.length) {
        list.innerHTML = '<div class="card">Nenhuma candidatura para esta vaga.</div>';
        return;
    }
    candidaturas.forEach((item) => {
        const match = getMatchScore(item.profile, vaga);
        const isHyped = match.score === 2;

        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <h4>${escapeHtml(item.candidato_nome || item.candidato_email || 'Candidato')}</h4>
            <small>E-mail: ${escapeHtml(item.candidato_email || '-')}</small>
            <small>Data da candidatura: ${escapeHtml(item.data || '-')}</small>
            <small class="candidate-score">Pontuação de aderência: ${match.score}/2</small>
            ${isHyped ? '<span class="tag-hyped" title="Hyped: candidato dentro da faixa salarial e com escolaridade dentro ou acima do mínimo exigido para a vaga.">Hyped</span>' : ''}
        `;
        const actions = document.createElement('div');
        actions.className = 'actions';
        const btnPerfil = document.createElement('button');
        btnPerfil.className = 'btn btn-secondary';
        btnPerfil.type = 'button';
        btnPerfil.textContent = 'Abrir perfil do candidato';
        btnPerfil.addEventListener('click', async () => {
            try {
                const data = item.profile || await api(`/api/candidaturas/${item.id}/perfil-candidato/`, { auth: true });
                renderCandidateProfileModal(data);
            } catch (error) {
                notify('Falha ao carregar perfil do candidato: ' + error.message, 'error');
            }
        });
        actions.appendChild(btnPerfil);
        card.appendChild(actions);
        list.appendChild(card);
    });
}

async function loadVagaContext(vagaId) {
    const vaga = await api(`/api/vagas/${vagaId}/`, { auth: true });
    document.getElementById('empresa-vaga-menu-titulo').textContent = `Menu da vaga #${vaga.id} - ${vaga.nome}`;
    document.getElementById('empresa-opened-requisitos').value = vaga.requisitos || '';
    document.getElementById('empresa-opened-status').value = vaga.status;

    const candidaturasResponse = await api(`/api/vagas/${vagaId}/candidaturas/`, { auth: true });
    const candidaturas = candidaturasResponse.results || [];
    const candidaturasEnriquecidas = await Promise.all(
        candidaturas.map(async (item) => {
            try {
                const profile = await api(`/api/candidaturas/${item.id}/perfil-candidato/`, { auth: true });
                return { ...item, profile };
            } catch (_) {
                return { ...item, profile: null };
            }
        }),
    );
    renderCandidaturas(candidaturasEnriquecidas, vaga);
    setEditingMode(false);
}

async function saveOpenedCompanyVaga(vagaId) {
    try {
        await api(`/api/vagas/${vagaId}/`, {
            method: 'PATCH',
            auth: true,
            body: {
                requisitos: document.getElementById('empresa-opened-requisitos').value,
                status: document.getElementById('empresa-opened-status').value,
            },
        });
        notify('Vaga atualizada com sucesso.');
        await loadVagaContext(vagaId);
        setEditingMode(false);
    } catch (error) {
        notify('Falha ao salvar edição da vaga: ' + error.message, 'error');
    }
}

async function deleteOpenedCompanyVaga(vagaId) {
    try {
        await api(`/api/vagas/${vagaId}/`, {
            method: 'DELETE',
            auth: true,
        });
        window.location.assign('/empresa/');
    } catch (error) {
        notify('Falha ao deletar vaga: ' + error.message, 'error');
    }
}

async function bootstrap() {
    const me = await initSession({ requiredRole: 'empresa' });
    if (!me) return;

    const vagaId = getVagaId();
    if (!vagaId) {
        notify('Vaga inválida para gestão.', 'error');
        return;
    }

    try {
        await loadVagaContext(vagaId);
    } catch (error) {
        notify('Falha ao abrir vaga: ' + error.message, 'error');
    }

    document.getElementById('btn-empresa-salvar-edicao').addEventListener('click', () => saveOpenedCompanyVaga(vagaId));
    document.getElementById('btn-empresa-editar-vaga').addEventListener('click', () => setEditingMode(true));
    document.getElementById('btn-empresa-deletar-vaga').addEventListener('click', () => deleteOpenedCompanyVaga(vagaId));
}

bootstrap();
