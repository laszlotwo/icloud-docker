// Global state and routing

const App = {
  currentPage: 'chat',

  init() {
    this.setupRouting();
    this.navigate(location.hash.slice(1) || 'chat');
    this.connectReminders();
  },

  navigate(page) {
    if (!page) page = 'chat';
    document.querySelectorAll('.page').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    const pageEl = document.getElementById(`page-${page}`);
    const navEl = document.querySelector(`[data-page="${page}"]`);
    if (pageEl) {
      pageEl.classList.remove('hidden');
      this.currentPage = page;
    }
    if (navEl) navEl.classList.add('active');

    // Initialize pages on first visit
    const initMap = {
      chat: () => Chat.init(),
      voice: () => Voice.init(),
      manuals: () => Manuals.init(),
      vault: () => Vault.init(),
      locations: () => Locations.init(),
      expenses: () => Expenses.init(),
      reminders: () => Reminders.init(),
    };
    if (initMap[page]) initMap[page]();
  },

  setupRouting() {
    window.addEventListener('hashchange', () => {
      this.navigate(location.hash.slice(1));
    });
  },

  connectReminders() {
    // Listen for reminder notifications via voice WebSocket
    // (The voice WS doubles as notification channel when not recording)
    const ws = new WebSocket(`ws://${location.host}/ws/voice`);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'reminder_triggered') {
          App.toast(`⏰ 提醒: ${data.title}`, 'reminder', 10000);
        }
      } catch (_) {}
    };
  },

  toast(message, type = 'success', duration = 3000) {
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = message;
    document.getElementById('toast-container').appendChild(el);
    setTimeout(() => el.remove(), duration);
  },

  // Generic modal
  showModal(title, bodyHtml, onConfirm, confirmText = '确认') {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <div class="modal-title">${title}</div>
        <div class="modal-body">${bodyHtml}</div>
        <div class="modal-footer">
          <button class="btn btn-ghost" id="modal-cancel">取消</button>
          <button class="btn btn-primary" id="modal-confirm">${confirmText}</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    overlay.querySelector('#modal-cancel').onclick = () => overlay.remove();
    overlay.querySelector('#modal-confirm').onclick = () => {
      onConfirm(overlay);
      overlay.remove();
    };
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
    return overlay;
  },

  async api(method, path, body = null) {
    const opts = { method, headers: {} };
    if (body) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || '请求失败');
    }
    return res.json();
  },
};

document.addEventListener('DOMContentLoaded', () => App.init());
