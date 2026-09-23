/**
 * I LOVE EXAM MATCHER - Core Engine & UI Controller
 * REAL Backend Integration: Files are sent to FastAPI → Gemini AI → Real Extraction & Matching
 */

const API_BASE = window.location.origin;

// Current App State
const AppState = {
  questions: JSON.parse(localStorage.getItem('exam_results')) || [],
  matchResult: JSON.parse(localStorage.getItem('exam_match_result')) || null,
  currentPage: 1,
  pageSize: 10,
  user: JSON.parse(localStorage.getItem('exam_user')) || null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  highlightActiveNav();
  initUploadDropzones();
  initResultPage();
  initScoreDonut();
  initAuthForm();
});

// ========================= NAVBAR =========================
function initNavbar() {
  const toggleBtn = document.querySelector('.menu-toggle');
  const navMenu = document.querySelector('.nav-menu');
  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('show');
    });
    // Close menu when clicking a link
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => navMenu.classList.remove('show'));
    });
  }

  const loginBtn = document.querySelector('.nav-btn-login');
  if (loginBtn && AppState.user) {
    loginBtn.innerHTML = `<span>👤</span> ${AppState.user.name || 'Account'}`;
  }
}

function highlightActiveNav() {
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-link').forEach(link => {
    const linkPath = link.getAttribute('href');
    if (linkPath === currentPath || (currentPath === '' && linkPath === 'index.html')) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
}

// ========================= UPLOAD DROPZONES =========================
function initUploadDropzones() {
  const dropzones = document.querySelectorAll('.dropzone-box');
  dropzones.forEach(box => {
    const input = box.querySelector('input[type="file"]');
    if (!input) return;

    box.addEventListener('dragover', (e) => {
      e.preventDefault();
      box.classList.add('dragover');
    });
    box.addEventListener('dragleave', () => box.classList.remove('dragover'));
    box.addEventListener('drop', (e) => {
      e.preventDefault();
      box.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        showFilePill(box, input.files[0]);
      }
    });
    input.addEventListener('change', () => {
      if (input.files.length) showFilePill(box, input.files[0]);
    });
  });
}

function showFilePill(box, file) {
  let pill = box.querySelector('.file-selected-pill');
  if (!pill) {
    pill = document.createElement('div');
    pill.className = 'file-selected-pill';
    box.appendChild(pill);
  }
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
  pill.textContent = `✓ ${file.name} (${sizeMB} MB)`;
  pill.style.display = 'inline-block';

  // Change dropzone visual
  const icon = box.querySelector('.dropzone-icon');
  if (icon) icon.textContent = '✅';
  const title = box.querySelector('.dropzone-title');
  if (title) title.textContent = 'File Selected!';
}

// ========================= MATCH PAGE: Real Backend Call =========================
async function handleStartMatch(redirectUrl = 'result.html') {
  const btn = document.querySelector('#startMatchBtn') || document.querySelector('#startOmrBtn');
  const statusDiv = document.getElementById('matchStatusMsg');

  // Get file inputs
  const paperInput = document.getElementById('inputPaper') || document.getElementById('inputStudentOmr');
  const keyInput = document.getElementById('inputKey') || document.getElementById('inputKeyOmr');

  if (!paperInput || !paperInput.files || paperInput.files.length === 0) {
    alert('⚠️ कृपया कम से कम Question Paper / OMR Sheet upload करें!');
    return;
  }

  // Show loading state
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-inline"></span> ⏳ AI Reading & Matching... कृपया प्रतीक्षा करें (30-60 sec)`;
    btn.style.opacity = '0.7';
    btn.style.pointerEvents = 'none';
  }

  // Show status message
  showStatusBanner('processing', '🔄 AI आपके पेपर को पढ़ रहा है... कृपया Tab बंद न करें।');

  try {
    // Build FormData with real files
    const formData = new FormData();
    formData.append('paper_a', paperInput.files[0]);

    if (keyInput && keyInput.files && keyInput.files.length > 0) {
      formData.append('answer_key', keyInput.files[0]);
    }

    // Call real backend API
    const response = await fetch(`${API_BASE}/api/match-series`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server Error: ${response.status}`);
    }

    const result = await response.json();

    if (!result.success) {
      throw new Error(result.detail || 'Matching failed');
    }

    // Convert matched_table to display format
    const displayData = (result.matched_table || []).map((item, idx) => ({
      s_no: idx + 1,
      matched_q_no: item.series_b_q_no || item.series_a_q_no || (idx + 1),
      question: item.question || `Question ${idx + 1}`,
      options: item.options || {},
      correct_answer: item.correct_answer || '?',
      your_answer: item.correct_answer || '?', // Same as correct when no student answer provided
      subject: item.subject || 'General',
      matched_by: item.matched_by || 'ai'
    }));

    // Save to localStorage and redirect
    localStorage.setItem('exam_results', JSON.stringify(displayData));
    localStorage.setItem('exam_match_result', JSON.stringify({
      total_questions: result.total_questions,
      questions_a: result.questions_a,
      questions_b_count: result.questions_b_count,
      has_key: result.has_key,
      timestamp: new Date().toISOString()
    }));

    showStatusBanner('success', `✅ ${result.total_questions} प्रश्न सफलतापूर्वक मैच किए गए!`);

    setTimeout(() => {
      window.location.href = redirectUrl;
    }, 800);

  } catch (error) {
    console.error('Match Error:', error);
    showStatusBanner('error', `❌ Error: ${error.message}`);

    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>⚡</span> <span>Try Again — Retry Matching</span>`;
      btn.style.opacity = '1';
      btn.style.pointerEvents = 'auto';
    }
  }
}

// ========================= OMR Page: Real Backend Call =========================
async function handleOmrMatch(redirectUrl = 'result.html') {
  const btn = document.getElementById('startOmrBtn');
  const studentOmrInput = document.getElementById('inputStudentOmr');
  const keyOmrInput = document.getElementById('inputKeyOmr');

  if (!studentOmrInput || !studentOmrInput.files || studentOmrInput.files.length === 0) {
    alert('⚠️ कृपया Student OMR Sheet upload करें!');
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-inline"></span> ⏳ OMR Reading... कृपया प्रतीक्षा करें`;
    btn.style.opacity = '0.7';
  }

  showStatusBanner('processing', '🔄 AI आपकी OMR Sheet पढ़ रहा है...');

  try {
    const formData = new FormData();
    formData.append('paper_a', studentOmrInput.files[0]);

    if (keyOmrInput && keyOmrInput.files && keyOmrInput.files.length > 0) {
      formData.append('answer_key', keyOmrInput.files[0]);
    }

    const response = await fetch(`${API_BASE}/api/match-series`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server Error: ${response.status}`);
    }

    const result = await response.json();

    const displayData = (result.matched_table || []).map((item, idx) => ({
      s_no: idx + 1,
      matched_q_no: item.series_b_q_no || (idx + 1),
      question: item.question || `Question ${idx + 1}`,
      options: item.options || {},
      correct_answer: item.correct_answer || '?',
      your_answer: item.correct_answer || '?',
      subject: 'General',
      matched_by: item.matched_by || 'ai'
    }));

    localStorage.setItem('exam_results', JSON.stringify(displayData));
    showStatusBanner('success', `✅ ${result.total_questions} प्रश्नों का OMR Evaluation पूरा!`);

    setTimeout(() => { window.location.href = redirectUrl; }, 800);
  } catch (error) {
    console.error('OMR Error:', error);
    showStatusBanner('error', `❌ Error: ${error.message}`);
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>Start Matching</span>`;
      btn.style.opacity = '1';
    }
  }
}

// ========================= Status Banner =========================
function showStatusBanner(type, message) {
  let banner = document.getElementById('statusBanner');
  if (!banner) {
    banner = document.createElement('div');
    banner.id = 'statusBanner';
    const mainContent = document.querySelector('.main-content .container-lg') ||
                        document.querySelector('.main-content .container-xl') ||
                        document.querySelector('.main-content');
    if (mainContent) mainContent.prepend(banner);
  }

  const colors = {
    processing: { bg: '#fff3cd', border: '#ffc107', color: '#664d03' },
    success: { bg: '#d1e7dd', border: '#badbcc', color: '#0f5132' },
    error: { bg: '#f8d7da', border: '#f5c2c7', color: '#842029' }
  };
  const c = colors[type] || colors.processing;

  banner.style.cssText = `
    background: ${c.bg}; border: 1px solid ${c.border}; color: ${c.color};
    border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 0.75rem;
    font-size: 0.95rem; font-weight: 600; animation: fadeIn 0.3s;
  `;
  banner.innerHTML = message;

  if (type === 'success') {
    setTimeout(() => { if (banner) banner.style.opacity = '0.6'; }, 3000);
  }
}

// ========================= RESULT PAGE =========================
function initResultPage() {
  const tbody = document.getElementById('resultTableBody');
  if (!tbody) return;

  // Load data from localStorage
  const savedData = localStorage.getItem('exam_results');
  if (savedData) {
    try {
      AppState.questions = JSON.parse(savedData);
    } catch(e) {
      AppState.questions = [];
    }
  }

  if (AppState.questions.length === 0) {
    showNoDataMessage();
    return;
  }

  renderTableRows();
  renderPagination();
  calculateAndRenderMetrics();
}

function showNoDataMessage() {
  const tbody = document.getElementById('resultTableBody');
  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center;padding:3rem;color:var(--text-muted);">
          <div style="font-size:3rem;margin-bottom:0.5rem;">📋</div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--primary-navy);margin-bottom:0.5rem;">कोई Result उपलब्ध नहीं है</div>
          <div style="margin-bottom:1rem;">पहले <a href="match.html" style="color:var(--primary-blue);font-weight:700;">Match Page</a> पर जाकर अपना Question Paper और Answer Key upload करें।</div>
          <a href="match.html" style="background:var(--primary-blue);color:white;padding:0.6rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:700;">Upload & Match Now →</a>
        </td>
      </tr>
    `;
  }
  // Reset metric cards to 0
  const ids = ['metricTotal', 'metricCorrect', 'metricWrong', 'metricScore'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = id === 'metricScore' ? '0 / 0' : '0';
  });
}

function renderTableRows() {
  const tbody = document.getElementById('resultTableBody');
  if (!tbody) return;

  const startIdx = (AppState.currentPage - 1) * AppState.pageSize;
  const endIdx = startIdx + AppState.pageSize;
  const pageItems = AppState.questions.slice(startIdx, endIdx);

  tbody.innerHTML = '';

  pageItems.forEach(item => {
    const isCorrect = item.your_answer === item.correct_answer;
    const isUnattempted = !item.your_answer || item.your_answer === '?';
    let badgeClass, badgeText;

    if (isUnattempted) {
      badgeClass = 'badge-unattempted';
      badgeText = '— Unattempted';
    } else if (isCorrect) {
      badgeClass = 'badge-correct';
      badgeText = '✓ Correct';
    } else {
      badgeClass = 'badge-wrong';
      badgeText = '✗ Wrong';
    }

    // Truncate long questions for table display
    const shortQ = (item.question || '').length > 80
      ? item.question.substring(0, 80) + '...'
      : item.question;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${item.s_no}</strong></td>
      <td><span style="color:var(--primary-blue);font-weight:700;">Q.${item.matched_q_no}</span></td>
      <td>
        <div style="font-weight:600;color:var(--primary-navy);margin-bottom:2px;" title="${(item.question||'').replace(/"/g,'&quot;')}">${shortQ}</div>
        <small style="color:var(--text-muted);">${item.subject || 'General'} ${item.matched_by === 'ai' ? '· 🤖 AI Matched' : ''}</small>
      </td>
      <td><span style="font-weight:700;color:var(--success);">${item.correct_answer}</span></td>
      <td><span style="font-weight:700;color:${isCorrect ? 'var(--success)' : isUnattempted ? 'var(--text-muted)' : 'var(--danger)'};">${item.your_answer || '—'}</span></td>
      <td><span class="badge-result ${badgeClass}">${badgeText}</span></td>
    `;
    tbody.appendChild(tr);
  });

  const counterEl = document.getElementById('tableCounterText');
  if (counterEl) {
    counterEl.textContent = `Showing ${startIdx + 1} to ${Math.min(endIdx, AppState.questions.length)} of ${AppState.questions.length} questions`;
  }
}

function renderPagination() {
  const container = document.getElementById('paginationBtns');
  if (!container) return;

  const totalPages = Math.ceil(AppState.questions.length / AppState.pageSize);
  container.innerHTML = '';

  const prevBtn = document.createElement('button');
  prevBtn.className = 'page-btn';
  prevBtn.innerHTML = '&lt;';
  prevBtn.disabled = AppState.currentPage === 1;
  prevBtn.onclick = () => { AppState.currentPage--; renderTableRows(); renderPagination(); };
  container.appendChild(prevBtn);

  for (let i = 1; i <= Math.min(totalPages, 5); i++) {
    const pageBtn = document.createElement('button');
    pageBtn.className = `page-btn ${i === AppState.currentPage ? 'active' : ''}`;
    pageBtn.textContent = i;
    pageBtn.onclick = () => { AppState.currentPage = i; renderTableRows(); renderPagination(); };
    container.appendChild(pageBtn);
  }

  if (totalPages > 5) {
    const dots = document.createElement('span');
    dots.textContent = '...';
    dots.style.padding = '0 4px';
    container.appendChild(dots);

    const lastBtn = document.createElement('button');
    lastBtn.className = `page-btn ${totalPages === AppState.currentPage ? 'active' : ''}`;
    lastBtn.textContent = totalPages;
    lastBtn.onclick = () => { AppState.currentPage = totalPages; renderTableRows(); renderPagination(); };
    container.appendChild(lastBtn);
  }

  const nextBtn = document.createElement('button');
  nextBtn.className = 'page-btn';
  nextBtn.innerHTML = '&gt;';
  nextBtn.disabled = AppState.currentPage === totalPages;
  nextBtn.onclick = () => { AppState.currentPage++; renderTableRows(); renderPagination(); };
  container.appendChild(nextBtn);
}

function calculateAndRenderMetrics() {
  const total = AppState.questions.length;
  if (total === 0) return;

  const correct = AppState.questions.filter(q => q.your_answer && q.your_answer !== '?' && q.your_answer === q.correct_answer).length;
  const unattempted = AppState.questions.filter(q => !q.your_answer || q.your_answer === '?').length;
  const wrong = total - correct - unattempted;
  const marksPerQ = 2;
  const negativePerQ = 0.5;
  const score = (correct * marksPerQ) - (wrong * negativePerQ);
  const maxScore = total * marksPerQ;

  const totalEl = document.getElementById('metricTotal');
  const correctEl = document.getElementById('metricCorrect');
  const wrongEl = document.getElementById('metricWrong');
  const scoreEl = document.getElementById('metricScore');

  if (totalEl) totalEl.textContent = total;
  if (correctEl) correctEl.textContent = correct;
  if (wrongEl) wrongEl.textContent = wrong;
  if (scoreEl) scoreEl.textContent = `${Math.max(0, score)} / ${maxScore}`;

  const overallScoreText = document.getElementById('overallScoreText');
  const statCorrect = document.getElementById('statCorrect');
  const statWrong = document.getElementById('statWrong');
  const statTotal = document.getElementById('statTotal');

  if (overallScoreText) overallScoreText.textContent = `Score: ${Math.max(0, score)} / ${maxScore}`;
  if (statCorrect) statCorrect.textContent = correct;
  if (statWrong) statWrong.textContent = wrong;
  if (statTotal) statTotal.textContent = total;

  // Update Circular Progress
  const circlePct = document.getElementById('circlePercent');
  const circleBar = document.querySelector('.circle-bar');
  const percentage = total > 0 ? Math.round((correct / total) * 100) : 0;

  if (circlePct) circlePct.textContent = `${percentage}%`;
  if (circleBar) {
    const circumference = 377;
    const offset = circumference - (circumference * percentage) / 100;
    circleBar.style.strokeDashoffset = offset;
  }
}

function initScoreDonut() {
  const circleBar = document.querySelector('.circle-bar');
  if (circleBar) {
    setTimeout(() => calculateAndRenderMetrics(), 150);
  }
}

// ========================= AUTH =========================
function initAuthForm() {
  const loginTab = document.getElementById('tabLogin');
  const signupTab = document.getElementById('tabSignup');
  const authForm = document.getElementById('authForm');
  const nameField = document.getElementById('groupFullName');
  const submitBtn = document.getElementById('authSubmitBtn');
  const togglePassBtn = document.getElementById('togglePassword');
  const passwordInput = document.getElementById('authPassword');

  if (togglePassBtn && passwordInput) {
    togglePassBtn.addEventListener('click', () => {
      const isPass = passwordInput.type === 'password';
      passwordInput.type = isPass ? 'text' : 'password';
      togglePassBtn.textContent = isPass ? '🙈' : '👁️';
    });
  }

  if (loginTab && signupTab) {
    loginTab.addEventListener('click', () => {
      loginTab.classList.add('active');
      signupTab.classList.remove('active');
      if (nameField) nameField.style.display = 'none';
      if (submitBtn) submitBtn.textContent = 'Log In';
    });

    signupTab.addEventListener('click', () => {
      signupTab.classList.add('active');
      loginTab.classList.remove('active');
      if (nameField) nameField.style.display = 'block';
      if (submitBtn) submitBtn.textContent = 'Create Account';
    });
  }

  if (authForm) {
    authForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const identifier = document.getElementById('authIdentifier')?.value || 'student@example.com';
      const name = document.getElementById('authFullName')?.value || identifier.split('@')[0];

      const user = { name: name, email: identifier, loggedInAt: new Date().toISOString() };
      localStorage.setItem('exam_user', JSON.stringify(user));
      AppState.user = user;

      alert(`Welcome, ${name}! Logged in successfully.`);
      window.location.href = 'index.html';
    });
  }
}

// ========================= CSS Animation =========================
const style = document.createElement('style');
style.textContent = `
  @keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
  .spinner-inline {
    display: inline-block; width: 16px; height: 16px;
    border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
    border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
`;
document.head.appendChild(style);
