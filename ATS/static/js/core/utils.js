export function firstErrorFromObject(obj) {
    if (obj === null || obj === undefined) return '';
    if (typeof obj === 'string') return obj;
    if (Array.isArray(obj)) {
        for (const item of obj) {
            const msg = firstErrorFromObject(item);
            if (msg) return msg;
        }
        return '';
    }
    if (typeof obj === 'object') {
        for (const key of Object.keys(obj)) {
            const msg = firstErrorFromObject(obj[key]);
            if (msg) return msg;
        }
    }
    return '';
}

export function notify(message, type = 'ok') {
    const feedback = document.getElementById('feedback');
    if (!feedback) return;
    feedback.classList.remove('hidden', 'ok', 'error');
    feedback.classList.add(type === 'error' ? 'error' : 'ok');
    feedback.textContent = message;
}

export function clearNotify() {
    const feedback = document.getElementById('feedback');
    if (!feedback) return;
    feedback.classList.add('hidden');
    feedback.classList.remove('ok', 'error');
    feedback.textContent = '';
}

export function showSaveModal(message) {
    const modal = document.getElementById('save-modal');
    const content = document.getElementById('save-modal-message');
    if (!modal || !content) return;
    content.textContent = message;
    modal.classList.remove('hidden');
}

export function closeSaveModal() {
    const modal = document.getElementById('save-modal');
    if (modal) modal.classList.add('hidden');
}

export function closeCandidateProfileModal() {
    const modal = document.getElementById('candidate-profile-modal');
    if (modal) modal.classList.add('hidden');
}

export function escolaridadeLabel(value) {
    const labels = {
        fundamental: 'Ensino fundamental',
        medio: 'Ensino médio',
        tecnologo: 'Tecnólogo',
        superior: 'Ensino Superior',
        pos: 'Pós / MBA / Mestrado',
        doutorado: 'Doutorado',
    };
    return labels[value] || value || '-';
}

export function vagaStatusLabel(status) {
    if (status === 'aberta') return 'Aberta';
    if (status === 'encerrada') return 'Encerrada';
    if (status === 'preenchida') return 'Preenchida';
    return status;
}

export function escapeHtml(value) {
    return (value || '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

export function renderCandidateProfileModal(data) {
    const container = document.getElementById('candidate-profile-modal-content');
    const modal = document.getElementById('candidate-profile-modal');
    if (!container || !modal) return;

    const experiencias = Array.isArray(data.experiencias) ? data.experiencias : [];
    const expHtml = experiencias.length
        ? experiencias.map((exp, index) => `
            <div class="card" style="margin-top:8px;">
                <h4>Experiência ${index + 1}</h4>
                <div class="candidate-profile-line"><strong>Empresa:</strong> ${escapeHtml(exp.nome_empresa || '-')}</div>
                <div class="candidate-profile-line"><strong>Data de início:</strong> ${escapeHtml(exp.data_inicio || '-')}</div>
                <div class="candidate-profile-line"><strong>Data de saída:</strong> ${escapeHtml(exp.data_saida || '-')}</div>
                <div class="candidate-profile-line"><strong>Emprego atual:</strong> ${exp.emprego_atual ? 'Sim' : 'Não'}</div>
                <div class="candidate-profile-line"><strong>Responsabilidades:</strong> ${escapeHtml(exp.principais_responsabilidades || '-')}</div>
            </div>
        `).join('')
        : '<div class="card">Nenhuma experiência cadastrada.</div>';

    container.innerHTML = `
        <div class="candidate-profile-line"><strong>Nome completo:</strong> ${escapeHtml(data.nome_completo || '-')}</div>
        <div class="candidate-profile-line"><strong>E-mail:</strong> ${escapeHtml(data.email || '-')}</div>
        <div class="candidate-profile-line"><strong>Data de nascimento:</strong> ${escapeHtml(data.data_nascimento || '-')}</div>
        <div class="candidate-profile-line"><strong>Pretensão salarial:</strong> ${data.pretensao_salarial ?? '-'}</div>
        <div class="candidate-profile-line"><strong>Escolaridade:</strong> ${escolaridadeLabel(data.escolaridade)}</div>
        <h4>Experiências profissionais</h4>
        ${expHtml}
    `;
    modal.classList.remove('hidden');
}
