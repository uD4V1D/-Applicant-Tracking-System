import { api, initSession } from '/static/js/core/api.js';
import { notify } from '/static/js/core/utils.js';

const chartState = {
    vagas: null,
    candidatos: null,
    candidaturasVaga: null,
    statusMes: null,
};

function destroyCharts() {
    if (chartState.vagas) chartState.vagas.destroy();
    if (chartState.candidatos) chartState.candidatos.destroy();
    if (chartState.candidaturasVaga) chartState.candidaturasVaga.destroy();
    if (chartState.statusMes) chartState.statusMes.destroy();
    chartState.vagas = null;
    chartState.candidatos = null;
    chartState.candidaturasVaga = null;
    chartState.statusMes = null;
}

function renderRelatoriosEmpresa(data) {
    if (typeof Chart === 'undefined') {
        notify('Chart.js não foi carregado corretamente.', 'error');
        return;
    }
    const labels = data.labels || [];
    destroyCharts();

    chartState.vagas = new Chart(document.getElementById('chart-vagas-mes'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{ label: 'Vagas criadas', data: data.vagas_criadas_por_mes || [], backgroundColor: '#1d4ed8' }],
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });

    chartState.candidatos = new Chart(document.getElementById('chart-candidatos-mes'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Candidatos recebidos',
                data: data.candidatos_recebidos_por_mes || [],
                borderColor: '#16a34a',
                backgroundColor: 'rgba(22, 163, 74, 0.2)',
                fill: true,
                tension: 0.25,
            }],
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });

    chartState.candidaturasVaga = new Chart(document.getElementById('chart-candidaturas-vaga'), {
        type: 'bar',
        data: {
            labels: data.candidaturas_por_vaga_labels || [],
            datasets: [{ label: 'Candidaturas', data: data.candidaturas_por_vaga || [], backgroundColor: '#7c3aed' }],
        },
        options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: { x: { beginAtZero: true, ticks: { precision: 0 } } } },
    });

    chartState.statusMes = new Chart(document.getElementById('chart-status-mes'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: 'Abertas', data: data.vagas_abertas_por_mes || [], backgroundColor: '#1d4ed8' },
                { label: 'Encerradas', data: data.vagas_encerradas_por_mes || [], backgroundColor: '#f59e0b' },
                { label: 'Preenchidas', data: data.vagas_preenchidas_por_mes || [], backgroundColor: '#16a34a' },
            ],
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
    });
}

async function bootstrap() {
    const me = await initSession({ requiredRole: 'empresa' });
    if (!me) return;
    try {
        const data = await api('/api/vagas/relatorios/mensal/', { auth: true });
        renderRelatoriosEmpresa(data);
    } catch (error) {
        notify('Falha ao carregar relatórios: ' + error.message, 'error');
    }
}

bootstrap();
