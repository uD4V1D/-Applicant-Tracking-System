import { api, initSession, setTokens, state, fetchMe, updateHeaderByRole } from '/static/js/core/api.js';
import { notify, clearNotify } from '/static/js/core/utils.js';

function toggleRegisterFields() {
    const tipo = document.getElementById('register-tipo').value;
    document.getElementById('register-candidato-fields').classList.toggle('hidden', tipo === 'empresa');
    document.getElementById('register-empresa-fields').classList.toggle('hidden', tipo !== 'empresa');
}

async function register() {
    clearNotify();
    try {
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const tipo = document.getElementById('register-tipo').value;
        const payload = { email, password, tipo };

        if (tipo === 'candidato') {
            payload.nome_completo = document.getElementById('register-nome-completo').value.trim();
            payload.data_nascimento = document.getElementById('register-data-nascimento').value;
        } else {
            payload.nome_empresa = document.getElementById('register-nome-empresa').value.trim();
            payload.cnpj = document.getElementById('register-cnpj').value.trim();
        }

        await api('/api/auth/register/', { method: 'POST', body: payload });
        const loginResult = await api('/api/auth/login/', {
            method: 'POST',
            body: { email, password },
        });
        setTokens(loginResult.access, loginResult.refresh);
        await fetchMe();
        updateHeaderByRole();

        if (state.me?.tipo === 'empresa') {
            window.location.assign('/empresa/');
            return;
        }
        if (state.mustCompleteProfile) {
            window.location.assign('/perfil/');
            return;
        }
        window.location.assign('/portal/');
    } catch (error) {
        notify('Falha no cadastro: ' + error.message, 'error');
    }
}

function bindEvents() {
    document.getElementById('register-tipo').addEventListener('change', toggleRegisterFields);
    document.getElementById('btn-register').addEventListener('click', register);
}

async function bootstrap() {
    await initSession({ allowGuest: true });
    if (state.me) {
        if (state.me.tipo === 'empresa') {
            window.location.assign('/empresa/');
            return;
        }
        if (state.mustCompleteProfile) {
            window.location.assign('/perfil/');
            return;
        }
        window.location.assign('/portal/');
        return;
    }
    bindEvents();
    toggleRegisterFields();
}

bootstrap();
