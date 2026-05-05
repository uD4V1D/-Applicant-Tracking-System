import { firstErrorFromObject, closeCandidateProfileModal, closeSaveModal } from '/static/js/core/utils.js';

const state = {
    access: localStorage.getItem('ats_access') || '',
    refresh: localStorage.getItem('ats_refresh') || '',
    me: null,
    mustCompleteProfile: false,
};

function setTokens(access, refresh = state.refresh) {
    state.access = access || '';
    state.refresh = refresh || '';
    localStorage.setItem('ats_access', state.access);
    localStorage.setItem('ats_refresh', state.refresh);
}

function clearTokens() {
    setTokens('', '');
    state.me = null;
    state.mustCompleteProfile = false;
}

function authHeaders(auth = false) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth && state.access) {
        headers.Authorization = `Bearer ${state.access}`;
    }
    return headers;
}

async function api(url, { method = 'GET', body = null, auth = false } = {}) {
    const response = await fetch(url, {
        method,
        headers: authHeaders(auth),
        body: body ? JSON.stringify(body) : null,
    });

    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json') ? await response.json() : await response.text();

    if (!response.ok) {
        if (typeof payload === 'string') throw new Error(payload);
        if (payload?.detail) throw new Error(payload.detail);
        throw new Error(firstErrorFromObject(payload) || JSON.stringify(payload));
    }

    return payload;
}

async function refreshSession() {
    if (!state.refresh) return;
    try {
        const data = await api('/api/auth/refresh/', {
            method: 'POST',
            body: { refresh: state.refresh },
        });
        setTokens(data.access, state.refresh);
    } catch (_) {
        clearTokens();
    }
}

async function fetchMe() {
    const me = await api('/api/auth/me/', { auth: true });
    state.me = me;
    state.mustCompleteProfile = me.tipo === 'candidato' && !me.candidate_profile_completed;
    return me;
}

function updateHeaderByRole() {
    const session = document.getElementById('session-status');
    const logout = document.getElementById('btn-logout');
    const portal = document.getElementById('nav-link-portal');
    const empresa = document.getElementById('nav-link-empresa');
    const perfil = document.getElementById('nav-link-perfil');
    const relatorios = document.getElementById('nav-link-relatorios');

    if (!session) return;

    if (!state.me) {
        session.textContent = 'Não autenticado';
        if (logout) logout.classList.add('hidden');
        if (portal) portal.classList.remove('hidden');
        if (empresa) empresa.classList.add('hidden');
        if (perfil) perfil.classList.add('hidden');
        if (relatorios) relatorios.classList.add('hidden');
        return;
    }

    session.textContent = `${state.me.email} (${state.me.tipo})`;
    if (logout) logout.classList.remove('hidden');
    if (perfil) perfil.classList.remove('hidden');

    if (state.me.tipo === 'empresa') {
        if (portal) {
            portal.classList.add('hidden');
            portal.setAttribute('href', '/empresa/');
        }
        if (empresa) empresa.classList.remove('hidden');
        if (relatorios) relatorios.classList.remove('hidden');
    } else {
        if (portal) {
            portal.classList.remove('hidden');
            portal.setAttribute('href', '/portal/');
        }
        if (empresa) empresa.classList.add('hidden');
        if (relatorios) relatorios.classList.add('hidden');
    }
}

function bindGlobalElements() {
    const logout = document.getElementById('btn-logout');
    if (logout && logout.dataset.bound !== '1') {
        logout.dataset.bound = '1';
        logout.addEventListener('click', () => {
            clearTokens();
            window.location.assign('/');
        });
    }

    const closeSave = document.getElementById('btn-close-modal');
    if (closeSave && closeSave.dataset.bound !== '1') {
        closeSave.dataset.bound = '1';
        closeSave.addEventListener('click', closeSaveModal);
    }

    const closeCandidate = document.getElementById('btn-close-candidate-profile-modal');
    if (closeCandidate && closeCandidate.dataset.bound !== '1') {
        closeCandidate.dataset.bound = '1';
        closeCandidate.addEventListener('click', closeCandidateProfileModal);
    }
}

async function initSession({ allowGuest = false, requiredRole = null } = {}) {
    bindGlobalElements();

    if (state.access) {
        await refreshSession();
    }
    if (state.access) {
        try {
            await fetchMe();
        } catch (_) {
            clearTokens();
        }
    }

    updateHeaderByRole();

    if (!state.me && !allowGuest) {
        window.location.assign('/');
        return null;
    }

    if (state.me && requiredRole && state.me.tipo !== requiredRole) {
        if (state.me.tipo === 'empresa') {
            window.location.assign('/empresa/');
        } else {
            window.location.assign('/portal/');
        }
        return null;
    }

    return state.me;
}

export {
    state,
    api,
    setTokens,
    clearTokens,
    refreshSession,
    fetchMe,
    initSession,
    updateHeaderByRole,
};
