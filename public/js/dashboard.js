/**
 * SatyaDrishti - Citizen Dashboard & Grievance Submission Controller
 * Features:
 * - Drag and drop file upload with client-side image preview
 * - Web Speech API Voice Dictation
 * - HTML5 Geolocation GPS Auto-Detection
 * - Live verification modal feedback
 * - Citizen grievance list rendering
 */

let currentUser = null;
let selectedFile = null;

document.addEventListener('DOMContentLoaded', async () => {
  const verificationModal = document.getElementById('verificationModal');
  document.getElementById('btnCloseModal')?.addEventListener('click', closeModal);
  document.getElementById('btnAcknowledgeModal')?.addEventListener('click', () => {
    closeModal();
    document.getElementById('complaintsListContainer')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  verificationModal?.addEventListener('click', (event) => {
    if (event.target === verificationModal) closeModal();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeModal();
  });

  currentUser = await checkAuthSession();
  if (!currentUser) {
    window.location.href = '/login';
    return;
  }

  // Officers/investigators should not be on the citizen dashboard
  if (currentUser.role === 'investigator') {
    window.location.href = '/investigator';
    return;
  }


  setupDropzone();
  setupVoiceDictation();
  setupGeolocation();
  setupFormSubmission();
  loadCitizenComplaints();

  document.getElementById('btnRefreshComplaints')?.addEventListener('click', loadCitizenComplaints);
});

// Dropzone & File Preview
function setupDropzone() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('compImage');
  const previewBox = document.getElementById('imagePreviewContainer');
  const previewImg = document.getElementById('imagePreviewImg');
  const previewFileName = document.getElementById('previewFileName');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  });

  function handleFile(file) {
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewFileName.innerText = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      previewBox.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
}

// Voice Speech-to-Text Dictation (Web Speech API)
function setupVoiceDictation() {
  const voiceBtn = document.getElementById('voiceBtn');
  const voiceBtnText = document.getElementById('voiceBtnText');
  const voiceStatus = document.getElementById('voiceStatus');
  const descInput = document.getElementById('compDesc');

  if (!voiceBtn || !descInput) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtn.title = 'Speech Recognition not supported in this browser';
    voiceBtn.style.opacity = '0.5';
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = 'en-IN'; // Indian English / civic locale

  let isRecording = false;

  voiceBtn.addEventListener('click', () => {
    if (!isRecording) {
      try {
        recognition.start();
        isRecording = true;
        voiceBtn.classList.add('recording');
        voiceBtnText.innerText = 'Listening...';
        voiceStatus.style.display = 'block';
        voiceStatus.innerText = '🎙️ Recording voice... Speak your complaint details.';
      } catch (err) {
        console.error('Speech recognition error:', err);
      }
    } else {
      recognition.stop();
    }
  });

  recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      transcript += event.results[i][0].transcript;
    }
    if (transcript) {
      descInput.value = (descInput.value ? descInput.value + ' ' : '') + transcript;
    }
  };

  recognition.onend = () => {
    isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceBtnText.innerText = 'Voice Dictation';
    voiceStatus.style.display = 'none';
  };

  recognition.onerror = (event) => {
    isRecording = false;
    voiceBtn.classList.remove('recording');
    voiceBtnText.innerText = 'Voice Dictation';
    voiceStatus.innerText = `Microphone notice: ${event.error}`;
  };
}

// Geolocation GPS Auto-Detection
function setupGeolocation() {
  const gpsBtn = document.getElementById('btnAutoGps');
  const latInput = document.getElementById('compLat');
  const lngInput = document.getElementById('compLng');
  const addressInput = document.getElementById('compAddress');

  if (!gpsBtn) return;

  gpsBtn.addEventListener('click', () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    gpsBtn.innerText = '📍 Locating...';
    gpsBtn.disabled = true;

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(5);
        const lng = position.coords.longitude.toFixed(5);
        latInput.value = lat;
        lngInput.value = lng;
        if (!addressInput.value) {
          addressInput.value = `Bengaluru GPS Coordinates (${lat}, ${lng})`;
        }
        gpsBtn.innerText = '✓ GPS Synced';
        gpsBtn.disabled = false;
      },
      (err) => {
        // Fallback to Bengaluru BBMP defaults
        latInput.value = '12.9716';
        lngInput.value = '77.5946';
        if (!addressInput.value) {
          addressInput.value = 'MG Road / Vidhana Soudha, Bengaluru, Karnataka';
        }
        gpsBtn.innerText = '📍 Auto-Detect GPS';
        gpsBtn.disabled = false;
        alert('GPS location permission unavailable. Applied Bengaluru default coordinates.');
      },
      { timeout: 7000 }
    );
  });
}

// Form submission and verification call
function setupFormSubmission() {
  const form = document.getElementById('complaintForm');
  const submitBtn = document.getElementById('btnSubmitComplaint');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!selectedFile) {
      alert('Please select or drag-and-drop a photograph of the complaint.');
      return;
    }

    const title = document.getElementById('compTitle').value;
    const category = document.getElementById('compCategory').value;
    const description = document.getElementById('compDesc').value;
    const address = document.getElementById('compAddress').value;
    const latitude = document.getElementById('compLat').value || '12.9716';
    const longitude = document.getElementById('compLng').value || '77.5946';
    const ward = document.getElementById('compWard').value;

    const formData = new FormData();
    formData.append('title', title);
    formData.append('category', category);
    formData.append('description', description);
    formData.append('address', address);
    formData.append('latitude', latitude);
    formData.append('longitude', longitude);
    formData.append('ward', ward);
    formData.append('image', selectedFile);

    submitBtn.disabled = true;
    submitBtn.innerHTML = '⚡ Running Verification...';

    try {
      const res = await fetch('/api/complaints', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      submitBtn.disabled = false;
      submitBtn.innerHTML = '🔍 Submit & Trigger Verification';

      if (res.ok) {
        showVerificationModal(data.complaint);
        form.reset();
        document.getElementById('imagePreviewContainer').style.display = 'none';
        selectedFile = null;
        loadCitizenComplaints();
      } else {
        alert(data.error || 'Failed to submit complaint.');
      }
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '🔍 Submit & Trigger Verification';
      alert('Network error connecting to verification server.');
    }
  });
}

// Render Citizen-Friendly Submission Confirmation Modal
function showVerificationModal(complaint) {
  const modal = document.getElementById('verificationModal');
  const container = document.getElementById('verificationModalContent');

  const S = complaint.fraudScore || 0;
  let statusIcon = '✅';
  let statusTitle = 'Complaint Received & Verified';
  let statusMsg = 'Your grievance has been accepted and is now in the BBMP processing queue. An officer will review it shortly.';
  let statusColor = '#34d399'; // green

  if (S >= 0.60) {
    statusIcon = '⚠️';
    statusTitle = 'Complaint Submitted — Under Review';
    statusMsg = 'Your complaint has been submitted. Our system has flagged some aspects for additional review. An officer will manually verify the details before processing.';
    statusColor = '#f87171'; // red
  } else if (S >= 0.38) {
    statusIcon = '🔍';
    statusTitle = 'Complaint Submitted — Being Processed';
    statusMsg = 'Your grievance has been received and is currently being processed by our verification system. You will see updates in "My Submitted Grievances" below.';
    statusColor = '#fbbf24'; // yellow
  }

  container.innerHTML = `
    <div style="text-align: center; padding: 1rem 0 1.5rem;">
      <div style="font-size: 3.5rem; margin-bottom: 1rem; line-height:1;">${statusIcon}</div>
      <h3 style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem; color: ${statusColor};">${statusTitle}</h3>
      <p style="font-size: 0.95rem; color: var(--text-muted); max-width: 420px; margin: 0 auto 1.5rem; line-height: 1.6;">${statusMsg}</p>

      <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: var(--radius-sm); padding: 1rem 1.5rem; display: inline-block; text-align: left; min-width: 280px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span style="font-size: 0.8rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em;">Complaint ID</span>
          <span style="font-weight: 700; color: #a5b4fc; font-family: var(--font-mono);">${complaint.id}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span style="font-size: 0.8rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em;">Title</span>
          <span style="font-weight: 500; color: var(--text-main); max-width: 200px; text-align: right; font-size: 0.85rem;">${complaint.title}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 0.8rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.05em;">Status</span>
          <span style="font-weight: 600; color: ${statusColor}; font-size: 0.85rem;">${complaint.status || 'Submitted'}</span>
        </div>
      </div>

      <p style="font-size: 0.8rem; color: var(--text-dim); margin-top: 1.25rem;">
        📋 You can track the progress of your complaint in <strong style="color: var(--text-muted);">My Submitted Grievances</strong> below.
      </p>
    </div>
  `;

  modal.classList.add('active');
}


function closeModal() {
  document.getElementById('verificationModal')?.classList.remove('active');
  const content = document.getElementById('verificationModalContent');
  if (content) content.replaceChildren();
}

// Load Citizen's Complaints
async function loadCitizenComplaints() {
  const container = document.getElementById('complaintsListContainer');
  const countEl = document.getElementById('userComplaintCount');
  const verifiedEl = document.getElementById('userVerifiedCount');

  try {
    const res = await fetch('/api/complaints');
    if (!res.ok) return;

    const data = await res.json();
    const complaints = data.complaints || [];

    if (countEl) countEl.innerText = complaints.length;
    if (verifiedEl) verifiedEl.innerText = complaints.filter(c => c.status === 'Verified-low').length;

    if (complaints.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-dim);">
          <div style="font-size: 2rem; margin-bottom: 0.5rem;">📭</div>
          <p>No grievances submitted yet. Fill out the form to file your first complaint.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = complaints.map(c => {
      let badgeClass = 'badge-under-action';
      let friendlyStatus = 'Under Review';
      if (c.status === 'Verified-low') { badgeClass = 'badge-low-risk'; friendlyStatus = 'Accepted ✓'; }
      if (c.status === 'Flagged')      { badgeClass = 'badge-flagged';   friendlyStatus = 'Needs Clarification'; }
      if (c.status === 'Closed')       { badgeClass = 'badge-closed';    friendlyStatus = 'Resolved'; }

      return `
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 1.25rem; margin-bottom: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div>
              <span class="badge ${badgeClass}">${friendlyStatus}</span>
              <span style="font-size: 0.8rem; color: var(--text-dim); margin-left: 0.5rem;">${c.id}</span>
            </div>
          </div>

          <h3 style="font-size: 1.1rem; margin-bottom: 0.35rem;">${c.title}</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.75rem; line-height: 1.4;">
            ${c.description.substring(0, 120)}${c.description.length > 120 ? '...' : ''}
          </p>

          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: var(--text-dim);">
            <span>📍 ${c.ward}</span>
            <span>📅 ${new Date(c.submittedAt).toLocaleDateString()}</span>
          </div>

          ${c.investigatorNotes ? `
            <div style="margin-top: 0.75rem; padding: 0.5rem 0.75rem; background: rgba(99, 102, 241, 0.08); border-left: 3px solid var(--primary); border-radius: 4px; font-size: 0.8rem; color: #c7d2fe;">
              <strong>Investigator Note:</strong> ${c.investigatorNotes}
            </div>
          ` : ''}
        </div>
      `;
    }).join('');

  } catch (err) {
    container.innerHTML = `<div style="text-align: center; color: #f87171; padding: 2rem;">Error loading complaints.</div>`;
  }
}
