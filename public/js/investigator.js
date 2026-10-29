/**
 * SatyaDrishti - BBMP Investigator Workspace & Ranked Queue Controller
 * Implements:
 * - Ranked triage queue ordered by Fraud Score S descending
 * - Deep forensic inspection modal with ELA residual heatmaps
 * - Multi-branch score gauges (s_img, s_for, s_x, s_txt)
 * - Triage lifecycle updates (Verified-low, Flagged, Under action, Closed)
 */

let activeFilter = 'all';
let currentQueue = [];
let selectedComplaint = null;

document.addEventListener('DOMContentLoaded', async () => {
  const user = await checkAuthSession();
  if (!user) {
    window.location.href = '/login';
    return;
  }
  if (user.role !== 'investigator') {
    alert('Access restricted to BBMP Grievance Investigators.');
    window.location.href = '/dashboard';
    return;
  }

  setupFilters();
  setupSearch();
  setupModalActions();
  loadQueue();

  document.getElementById('btnRefreshQueue')?.addEventListener('click', loadQueue);
});

function setupFilters() {
  const filterBtns = document.querySelectorAll('[data-filter]');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active-filter'));
      btn.classList.add('active-filter');
      activeFilter = btn.dataset.filter;
      loadQueue();
    });
  });
}

function setupSearch() {
  const searchInput = document.getElementById('queueSearchInput');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#rankedQueueBody tr');
    rows.forEach(row => {
      const text = row.innerText.toLowerCase();
      row.style.display = text.includes(q) ? '' : 'none';
    });
  });
}

async function loadQueue() {
  const tbody = document.getElementById('rankedQueueBody');
  tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-dim);">Loading queue...</td></tr>`;

  try {
    const res = await fetch(`/api/investigator/queue?filter=${activeFilter}`);
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #f87171; padding: 2rem;">Failed to load queue.</td></tr>`;
      return;
    }

    const data = await res.json();
    currentQueue = data.queue || [];

    updateKPIs();
    renderQueueTable(currentQueue);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #f87171; padding: 2rem;">Error connecting to queue.</td></tr>`;
  }
}

function updateKPIs() {
  const totalEl = document.getElementById('kpiTotal');
  const flaggedEl = document.getElementById('kpiFlagged');
  const verifiedEl = document.getElementById('kpiVerified');
  const actionEl = document.getElementById('kpiAction');

  if (totalEl) totalEl.innerText = currentQueue.length;
  if (flaggedEl) flaggedEl.innerText = currentQueue.filter(c => c.status === 'Flagged').length;
  if (verifiedEl) verifiedEl.innerText = currentQueue.filter(c => c.status === 'Verified-low').length;
  if (actionEl) actionEl.innerText = currentQueue.filter(c => c.status === 'Under action' || c.status === 'Under review').length;
}

function renderQueueTable(complaints) {
  const tbody = document.getElementById('rankedQueueBody');

  if (complaints.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 3rem; color: var(--text-dim);">No complaints match the selected filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = complaints.map(c => {
    const S = c.fraudScore || 0;
    let riskClass = 'low';
    let badgeClass = 'badge-low-risk';
    if (S >= 0.60) {
      riskClass = 'high';
      badgeClass = 'badge-flagged';
    } else if (S >= 0.38) {
      riskClass = 'medium';
      badgeClass = 'badge-under-action';
    }

    let statusBadge = 'badge-under-action';
    if (c.status === 'Verified-low') statusBadge = 'badge-low-risk';
    if (c.status === 'Flagged') statusBadge = 'badge-flagged';
    if (c.status === 'Closed') statusBadge = 'badge-closed';

    return `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: 700; color: #a5b4fc;">${c.id}</td>
        <td>
          <img src="${c.imageUrl}" alt="evidence" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px; border: 1px solid var(--border-color); cursor: pointer;" onclick="openInspectorModal('${c.id}')">
        </td>
        <td>
          <div style="font-weight: 600; color: #fff; margin-bottom: 0.2rem;">${c.title}</div>
          <div style="font-size: 0.8rem; color: var(--text-dim);">📍 ${c.ward} • Submitter: ${c.userName || 'Citizen'}</div>
        </td>
        <td>
          <div class="fraud-meter">
            <div class="fraud-bar-bg" style="width: 80px;">
              <div class="fraud-bar-fill ${riskClass}" style="width: ${Math.max(8, S * 100)}%;"></div>
            </div>
            <span class="fraud-val" style="color: ${riskClass === 'high' ? '#f87171' : (riskClass === 'medium' ? '#fbbf24' : '#34d399')};">
              ${(S * 100).toFixed(0)}%
            </span>
          </div>
        </td>
        <td>
          <span class="badge ${statusBadge}">${c.status}</span>
        </td>
        <td style="font-size: 0.8rem; color: var(--text-dim);">
          ${new Date(c.submittedAt).toLocaleDateString()}
        </td>
        <td style="text-align: right;">
          <button class="btn btn-secondary btn-sm" onclick="openInspectorModal('${c.id}')">
            🔍 Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

// Open Deep Forensic Inspection Modal
function openInspectorModal(complaintId) {
  const complaint = currentQueue.find(c => c.id === complaintId);
  if (!complaint) return;
  selectedComplaint = complaint;

  const modal = document.getElementById('inspectorModal');
  const branches = complaint.branches || {};

  document.getElementById('modalComplaintTitle').innerText = complaint.title;
  document.getElementById('modalComplaintSub').innerText = `ID: ${complaint.id} • ${complaint.ward} • Category: ${complaint.category}`;
  document.getElementById('modalDescText').innerText = complaint.description || 'No description entered.';
  document.getElementById('modalLocationText').innerText = `${complaint.location.address} (${complaint.location.latitude}, ${complaint.location.longitude})`;
  document.getElementById('modalCitizenName').innerText = complaint.userName || 'Citizen';
  document.getElementById('modalInvestigatorNotes').value = complaint.investigatorNotes || '';

  // Original & ELA preview
  document.getElementById('modalImgOriginal').src = complaint.imageUrl;
  // If ELA base64 is present, use it; else fallback to original
  document.getElementById('modalImgEla').src = complaint.elaPreviewBase64 || complaint.imageUrl;

  // Fraud Score S
  const S = complaint.fraudScore || 0;
  const scoreEl = document.getElementById('modalScoreDisplay');
  scoreEl.innerText = `S = ${S.toFixed(4)} (${(S * 100).toFixed(1)}%)`;
  scoreEl.style.color = S >= 0.60 ? '#f87171' : (S >= 0.38 ? '#fbbf24' : '#34d399');

  const riskBadge = document.getElementById('modalRiskBadge');
  riskBadge.className = `badge ${S >= 0.60 ? 'badge-flagged' : (S >= 0.38 ? 'badge-under-action' : 'badge-low-risk')}`;
  riskBadge.innerText = complaint.riskLabel || (S >= 0.60 ? 'High Risk' : 'Low Risk');

  // 4 Branches
  const sImg = branches.s_img ? branches.s_img.score : 0.2;
  const sFor = branches.s_for ? branches.s_for.score : 0.2;
  const sX = branches.s_x ? branches.s_x.score : 0.2;
  const sTxt = branches.s_txt ? branches.s_txt.score : 0.2;

  document.getElementById('modalSImg').innerText = sImg.toFixed(3);
  document.getElementById('modalCNNLabel').innerText = `Label: ${branches.s_img?.label || 'Genuine'} (${branches.s_img?.confidence || 70}%)`;

  document.getElementById('modalSFor').innerText = sFor.toFixed(3);
  document.getElementById('modalForDetail').innerText = `ELA: ${(branches.s_for?.ela_score || 0).toFixed(2)} | EXIF: ${(branches.s_for?.exif_score || 0).toFixed(2)}`;

  document.getElementById('modalSX').innerText = sX.toFixed(3);
  document.getElementById('modalCrossDetail').innerText = `Visual: ${branches.s_x?.visual_detected || complaint.category} vs Text`;

  document.getElementById('modalSTxt').innerText = sTxt.toFixed(3);
  document.getElementById('modalTxtDetail').innerText = `Exaggeration: ${(branches.s_txt?.exaggeration || 0).toFixed(2)}`;

  // Explanations
  const expList = document.getElementById('modalExplanationsList');
  expList.innerHTML = (complaint.explanations || []).map(e => `<li>${e}</li>`).join('');

  modal.classList.add('active');
}

function setupModalActions() {
  document.getElementById('btnCloseInspectorModal')?.addEventListener('click', () => {
    document.getElementById('inspectorModal')?.classList.remove('active');
  });

  document.getElementById('btnAcceptGenuine')?.addEventListener('click', () => updateStatus('Verified-low'));
  document.getElementById('btnIssueWorkOrder')?.addEventListener('click', () => updateStatus('Under action'));
  document.getElementById('btnFlagReview')?.addEventListener('click', () => updateStatus('Flagged'));
  document.getElementById('btnRejectFraud')?.addEventListener('click', () => updateStatus('Closed', 'Rejected as fraudulent submission'));
}

async function updateStatus(newStatus, defaultNotes = '') {
  if (!selectedComplaint) return;
  const notes = document.getElementById('modalInvestigatorNotes').value || defaultNotes;

  try {
    const res = await fetch(`/api/complaints/${selectedComplaint.id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus, notes })
    });

    if (res.ok) {
      document.getElementById('inspectorModal')?.classList.remove('active');
      loadQueue();
    } else {
      const err = await res.json();
      alert(err.error || 'Failed to update status.');
    }
  } catch (e) {
    alert('Network error updating complaint status.');
  }
}
