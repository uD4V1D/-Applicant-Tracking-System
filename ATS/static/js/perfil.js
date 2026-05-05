import { api, initSession, state, fetchMe, updateHeaderByRole } from '/static/js/core/api.js';
import { notify, showSaveModal, escapeHtml } from '/static/js/core/utils.js';

function normalizeProfileData(profile) {
    const experiencias = (profile.experiencias || []).map((exp) => ({
        nome_empresa: (exp.nome_empresa || '').trim(),
        data_inicio: exp.data_inicio || null,
        data_saida: exp.data_saida || null,
        principais_responsabilidades: (exp.principais_responsabilidades || '').trim(),
        emprego_atual: Boolean(exp.emprego_atual),
    }));
    return {
        pretensao_salarial: Number(profile.pretensao_salarial),
        escolaridade: profile.escolaridade || '',
        experiencias,
    };
}

function normalizeUserProfileData(profile) {
    return {
        email: (profile.email || '').trim(),
        nome_completo: (profile.nome_completo || '').trim(),
        data_nascimento: profile.data_nascimento || null,
        nome_empresa: (profile.nome_empresa || '').trim(),
        cnpj: (profile.cnpj || '').replace(/\D/g, ''),
    };
}

function profilesEqual(a, b) {
    return JSON.stringify(a) === JSON.stringify(b);
}

function createExperienciaCard(data = {}) {
    const wrapper = document.createElement('div');
    wrapper.className = 'card experiencia-item';
    wrapper.innerHTML = `
        <div class="field">
            <label>Nome da empresa</label>
            <input type="text" class="exp-nome-empresa" value="${escapeHtml(data.nome_empresa || '')}">
        </div>
        <div class="field">
            <label>Data de início</label>
            <input type="date" class="exp-data-inicio" value="${escapeHtml(data.data_inicio || '')}">
        </div>
        <div class="field">
            <label>Data de saída</label>
            <input type="date" class="exp-data-saida" value="${escapeHtml(data.data_saida || '')}">
        </div>
        <div class="field" style="flex-direction:row;align-items:center;gap:8px;">
            <input type="checkbox" class="exp-emprego-atual" ${data.emprego_atual ? 'checked' : ''}>
            <label>Este é meu emprego atual</label>
        </div>
        <div class="field">
            <label>Principais responsabilidades</label>
            <textarea class="exp-responsabilidades">${escapeHtml(data.principais_responsabilidades || '')}</textarea>
        </div>
        <div class="actions">
            <button type="button" class="btn btn-secondary btn-remove-experiencia">Remover</button>
        </div>
    `;

    const checkbox = wrapper.querySelector('.exp-emprego-atual');
    const dataSaidaInput = wrapper.querySelector('.exp-data-saida');
    const removeBtn = wrapper.querySelector('.btn-remove-experiencia');

    function syncCurrentJobRule() {
        dataSaidaInput.disabled = checkbox.checked;
        if (checkbox.checked) dataSaidaInput.value = '';
    }

    checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
            document.querySelectorAll('.exp-emprego-atual').forEach((item) => {
                if (item !== checkbox) {
                    item.checked = false;
                    const inputSaida = item.closest('.experiencia-item')?.querySelector('.exp-data-saida');
                    if (inputSaida) inputSaida.disabled = false;
                }
            });
        }
        syncCurrentJobRule();
    });
    removeBtn.addEventListener('click', () => wrapper.remove());
    syncCurrentJobRule();
    return wrapper;
}

function resetExperiencias(experiencias = []) {
    const container = document.getElementById('experiencias-container');
    container.innerHTML = '';
    if (!experiencias.length) {
        container.appendChild(createExperienciaCard());
        return;
    }
    experiencias.forEach((exp) => container.appendChild(createExperienciaCard(exp)));
}

function collectExperiencias() {
    const items = document.querySelectorAll('.experiencia-item');
    const experiencias = [];
    items.forEach((item) => {
        const nome_empresa = item.querySelector('.exp-nome-empresa').value.trim();
        const data_inicio = item.querySelector('.exp-data-inicio').value;
        const data_saida = item.querySelector('.exp-data-saida').value;
        const principais_responsabilidades = item.querySelector('.exp-responsabilidades').value.trim();
        const emprego_atual = item.querySelector('.exp-emprego-atual').checked;

        if (!nome_empresa && !data_inicio && !data_saida && !principais_responsabilidades) return;

        experiencias.push({
            nome_empresa,
            data_inicio: data_inicio || null,
            data_saida: data_saida || null,
            principais_responsabilidades,
            emprego_atual,
        });
    });
    return experiencias;
}

function toggleProfileFields() {
    const candidateBlocks = ['candidate-user-fields', 'candidate-professional-fields'];
    const perfilGrid = document.getElementById('perfil-grid');
    const candidaturasPanel = document.getElementById('perfil-candidaturas-panel');
    if (state.me?.tipo === 'empresa') {
        candidateBlocks.forEach((id) => document.getElementById(id).classList.add('hidden'));
        document.getElementById('company-user-fields').classList.remove('hidden');
        candidaturasPanel.classList.add('hidden');
        perfilGrid.classList.add('single-column');
    } else {
        candidateBlocks.forEach((id) => document.getElementById(id).classList.remove('hidden'));
        document.getElementById('company-user-fields').classList.add('hidden');
        candidaturasPanel.classList.remove('hidden');
        perfilGrid.classList.remove('single-column');
    }
}

async function loadMinhasCandidaturas() {
    try {
        if (state.me?.tipo !== 'candidato') return;
        const data = await api('/api/candidaturas/', { auth: true });
        const list = document.getElementById('minhas-candidaturas-list');
        list.innerHTML = '';
        const results = data.results || [];
        if (!results.length) {
            list.innerHTML = '<div class="card">Sem candidaturas registradas.</div>';
            return;
        }
        results.forEach((item) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = `
                <h4>Candidatura #${item.id}</h4>
                <small>Vaga: ${item.vaga}</small>
                <small>Data: ${item.data}</small>
            `;
            list.appendChild(card);
        });
    } catch (error) {
        notify('Falha ao carregar candidaturas: ' + error.message, 'error');
    }
}

async function loadPerfil() {
    try {
        const userData = await api('/api/auth/profile/', { auth: true });
        document.getElementById('profile-email').value = userData.email || '';
        document.getElementById('profile-password').value = '';
        document.getElementById('profile-nome-completo').value = userData.nome_completo || '';
        document.getElementById('profile-data-nascimento').value = userData.data_nascimento || '';
        document.getElementById('profile-nome-empresa').value = userData.nome_empresa || '';
        document.getElementById('profile-cnpj').value = userData.cnpj || '';
        state.userProfileSnapshot = normalizeUserProfileData(userData);

        if (state.me?.tipo === 'candidato') {
            try {
                const data = await api('/api/candidatos/perfil/', { auth: true });
                document.getElementById('perfil-salario').value = data.pretensao_salarial || '';
                document.getElementById('perfil-escolaridade').value = data.escolaridade || '';
                resetExperiencias(data.experiencias || []);
                state.profileSnapshot = normalizeProfileData(data);
            } catch (error) {
                if ((error.message || '').includes('Perfil de candidato não encontrado')) {
                    document.getElementById('perfil-salario').value = '';
                    document.getElementById('perfil-escolaridade').value = '';
                    resetExperiencias([]);
                    state.profileSnapshot = null;
                } else {
                    throw error;
                }
            }
            await loadMinhasCandidaturas();
        }

        toggleProfileFields();
    } catch (error) {
        notify('Falha ao carregar perfil: ' + error.message, 'error');
    }
}

async function savePerfil() {
    try {
        const userPayload = { email: document.getElementById('profile-email').value.trim() };
        const newPassword = document.getElementById('profile-password').value.trim();
        if (newPassword) userPayload.password = newPassword;

        if (state.me?.tipo === 'candidato') {
            userPayload.nome_completo = document.getElementById('profile-nome-completo').value.trim();
            userPayload.data_nascimento = document.getElementById('profile-data-nascimento').value;
        } else {
            userPayload.nome_empresa = document.getElementById('profile-nome-empresa').value.trim();
            userPayload.cnpj = document.getElementById('profile-cnpj').value.trim();
        }

        let hasDbChanges = false;
        const normalizedUserPayload = normalizeUserProfileData(userPayload);
        const passwordChanged = Boolean(userPayload.password);
        if (!state.userProfileSnapshot || !profilesEqual(normalizedUserPayload, state.userProfileSnapshot) || passwordChanged) {
            const savedUser = await api('/api/auth/profile/', {
                method: 'PUT',
                auth: true,
                body: userPayload,
            });
            state.userProfileSnapshot = normalizeUserProfileData(savedUser);
            hasDbChanges = true;
        }

        if (state.me?.tipo === 'candidato') {
            const profilePayload = {
                pretensao_salarial: Number(document.getElementById('perfil-salario').value),
                escolaridade: document.getElementById('perfil-escolaridade').value,
                experiencias: collectExperiencias(),
            };
            const normalizedPayload = normalizeProfileData(profilePayload);
            if (!state.profileSnapshot || !profilesEqual(normalizedPayload, state.profileSnapshot)) {
                const savedProfile = await api('/api/candidatos/perfil/', {
                    method: 'PUT',
                    auth: true,
                    body: profilePayload,
                });
                state.profileSnapshot = normalizeProfileData(savedProfile);
                hasDbChanges = true;
            }
        }

        if (!hasDbChanges) {
            notify('Nenhuma alteração detectada no perfil.');
            return;
        }

        await fetchMe();
        updateHeaderByRole();
        showSaveModal('Perfil salvo com sucesso. Alterações persistidas no banco.');
    } catch (error) {
        notify('Falha ao salvar perfil: ' + error.message, 'error');
    }
}

function bindEvents() {
    document.getElementById('btn-carregar-perfil').addEventListener('click', loadPerfil);
    document.getElementById('btn-salvar-perfil').addEventListener('click', savePerfil);
    document.getElementById('btn-minhas-candidaturas').addEventListener('click', loadMinhasCandidaturas);
    document.getElementById('btn-add-experiencia').addEventListener('click', () => {
        document.getElementById('experiencias-container').appendChild(createExperienciaCard());
    });
}

async function bootstrap() {
    state.profileSnapshot = null;
    state.userProfileSnapshot = null;
    const me = await initSession();
    if (!me) return;
    bindEvents();
    await loadPerfil();
}

bootstrap();
