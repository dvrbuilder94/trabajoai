/**
 * TrabajoAI Auth + private decisions.
 * Uses Supabase Auth's documented HTTP endpoints without exposing a secret/service role key.
 * This client can only access rows permitted by PostgreSQL RLS.
 */
(() => {
  'use strict';
  const URL = 'https://lpbqzagdforlafvavgkx.supabase.co';
  const KEY = 'sb_publishable_OLazvsr0InC3O_6Ox292LA_GDmsnZs6';
  const STORAGE = 'trabajoai-auth-session-v1';
  let current = null;
  let user = null;

  const headers = (token, extra = {}) => ({
    apikey: KEY,
    ...(token ? {Authorization: 'Bearer ' + token} : {}),
    ...extra,
  });
  const message = value => {
    const el = document.getElementById('loginMessage');
    if (el) el.textContent = value;
  };
  const getStored = () => {
    try { return JSON.parse(localStorage.getItem(STORAGE) || 'null'); }
    catch { return null; }
  };
  const save = next => {
    current = next;
    if (current) localStorage.setItem(STORAGE, JSON.stringify(current));
    else localStorage.removeItem(STORAGE);
  };
  async function call(path, options = {}) {
    const response = await fetch(URL + path, options);
    if (!response.ok) {
      let info = {};
      try { info = await response.json(); } catch {}
      throw new Error(info.msg || info.error_description || info.message || ('HTTP ' + response.status));
    }
    if (response.status === 204) return null;
    const content = response.headers.get('content-type') || '';
    return content.includes('application/json') ? response.json() : null;
  }
  async function userInfo() {
    if (!current?.access_token) return null;
    return call('/auth/v1/user', {headers: headers(current.access_token)});
  }
  async function refresh() {
    if (!current?.refresh_token) throw new Error('No refresh token');
    const data = await call('/auth/v1/token?grant_type=refresh_token', {
      method: 'POST',
      headers: headers(null, {'Content-Type': 'application/json'}),
      body: JSON.stringify({refresh_token: current.refresh_token}),
    });
    save(data);
    return data;
  }
  async function session() {
    if (!current) return false;
    try {
      user = await userInfo();
    } catch {
      try { await refresh(); user = await userInfo(); }
      catch { save(null); user = null; }
    }
    return !!user?.id;
  }
  async function withSession(run) {
    if (!await session()) throw new Error('Tu sesión expiró. Inicia sesión nuevamente.');
    try { return await run(current.access_token, user.id); }
    catch (err) {
      if (String(err.message).includes('401')) {
        await refresh();
        return run(current.access_token, user.id);
      }
      throw err;
    }
  }
  async function fetchDecisions() {
    if (!await session()) return {};
    return withSession(async (token, uid) => {
      const data = await call('/rest/v1/job_decisions?select=job_id,status&user_id=eq.' + encodeURIComponent(uid), {
        headers: headers(token, {Accept: 'application/json'})
      });
      return Object.fromEntries((data || []).map(row => [row.job_id, row.status]));
    });
  }
  async function setDecision(id, status) {
    if (!['approved', 'rejected', 'review'].includes(status)) throw new Error('Invalid status');
    return withSession(async (token, uid) => call('/rest/v1/job_decisions?on_conflict=user_id,job_id', {
      method: 'POST',
      headers: headers(token, {'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal'}),
      body: JSON.stringify({user_id: uid, job_id: id, status, updated_at: new Date().toISOString()})
    }));
  }
  async function sendLink(email) {
    const redirect = location.origin + location.pathname;
    await call('/auth/v1/otp', {
      method: 'POST',
      headers: headers(null, {'Content-Type': 'application/json'}),
      body: JSON.stringify({email, create_user: true, email_redirect_to: redirect}),
    });
  }
  async function signOut() {
    try {
      if (current?.access_token) {
        await call('/auth/v1/logout', {method: 'POST', headers: headers(current.access_token)});
      }
    } catch (err) { console.warn('Logout request failed', err.message); }
    save(null);
    user = null;
    window.remoteStatuses = {};
    document.dispatchEvent(new CustomEvent('trabajo-decisions-change'));
    announce();
  }
  function announce() {
    const button = document.getElementById('accountButton');
    if (button) button.textContent = user?.email ? 'Cuenta: ' + user.email : 'Iniciar sesión';
    document.dispatchEvent(new CustomEvent('trabajo-auth-change', {detail: {loggedIn: !!user, email: user?.email || null}}));
  }
  async function loadSavedDecisions() {
    if (!user) return;
    try {
      window.remoteStatuses = await fetchDecisions();
      document.dispatchEvent(new CustomEvent('trabajo-decisions-change'));
    } catch (error) { console.warn('Could not load decisions', error.message); }
  }
  async function init() {
    const hash = new URLSearchParams(location.hash.replace(/^#/, ''));
    if (hash.has('access_token') && hash.has('refresh_token')) {
      save({access_token: hash.get('access_token'), refresh_token: hash.get('refresh_token')});
      history.replaceState(null, '', location.pathname + location.search);
    } else { current = getStored(); }
    await session();
    announce();
    await loadSavedDecisions();
  }
  window.trabajoAuth = {
    isLoggedIn: () => !!user,
    setDecision,
    signOut,
    async reload() { await session(); announce(); await loadSavedDecisions(); },
  };
  document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('loginDialog');
    const button = document.getElementById('accountButton');
    const form = document.getElementById('loginForm');
    button?.addEventListener('click', () => {
      if (user) { if (confirm('¿Cerrar sesión?')) signOut(); }
      else dialog?.showModal();
    });
    document.getElementById('dismissLogin')?.addEventListener('click', () => dialog?.close());
    form?.addEventListener('submit', async e => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value.trim();
      const submit = form.querySelector('button[type=submit]');
      submit.disabled = true;
      message('Enviando enlace...');
      try {
        await sendLink(email);
        message('Revisa tu correo. Si no llega, verifica la configuración de correo y redirección en Supabase.');
      } catch (err) { message('No se pudo enviar el enlace: ' + err.message); }
      finally { submit.disabled = false; }
    });
    init().catch(err => {console.warn('Auth initialization issue',err.message); announce();});
  });
})();
