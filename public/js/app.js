/**
 * SatyaDrishti - Shared Application Scripts & Session Controller
 */

async function checkAuthSession() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      updateNavForUser(data.user);
      return data.user;
    }
  } catch (err) {
    // Session unauthenticated
  }
  return null;
}

function updateNavForUser(user) {
  const authNav = document.getElementById('authNavButtons');
  if (authNav && user) {
    authNav.innerHTML = `
      <div style="display:flex; align-items:center; gap: 0.75rem;">
        <a href="${user.role === 'investigator' ? '/investigator' : '/dashboard'}" class="btn btn-secondary btn-sm">
          ${user.role === 'investigator' ? '🛡️ Workspace' : '👤 ' + user.name.split(' ')[0]}
        </a>
        <button id="globalLogoutBtn" class="btn btn-secondary btn-sm">Sign Out</button>
      </div>
    `;

    document.getElementById('globalLogoutBtn')?.addEventListener('click', handleLogout);
  }

  // Populate user names if present on specific page headers
  const userNameEl = document.getElementById('navUserName');
  const userWardEl = document.getElementById('navUserWard');
  const welcomeEl = document.getElementById('welcomeCitizenName');
  const officerEl = document.getElementById('invOfficerName');
  const zoneEl = document.getElementById('invZoneBadge');

  if (userNameEl && user) userNameEl.innerText = user.name;
  if (userWardEl && user) userWardEl.innerText = user.ward || 'BBMP Bengaluru';
  if (welcomeEl && user) welcomeEl.innerText = user.name;
  if (officerEl && user) officerEl.innerText = user.name;
  if (zoneEl && user) zoneEl.innerText = user.ward || 'BBMP Triage Unit';
}

async function handleLogout() {
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
  } catch (e) {}
  window.location.href = '/login';
}

document.addEventListener('DOMContentLoaded', () => {
  checkAuthSession();

  document.getElementById('navLogoutBtn')?.addEventListener('click', handleLogout);
  document.getElementById('invLogoutBtn')?.addEventListener('click', handleLogout);
});
