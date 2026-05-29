const Vault = {
  initialized: false,
  unlocked: false,

  init() {
    if (this.initialized) return;
    this.initialized = true;
    this.render();
  },

  render() {
    const page = document.getElementById('page-vault');
    page.innerHTML = `
      <div class="page-header">
        <span class="page-title">🔐 密码库</span>
        <div style="display:flex;gap:8px">
          ${this.unlocked ? '<button class="btn btn-ghost" onclick="Vault.lock()">🔒 锁定</button>' : ''}
          ${this.unlocked ? '<button class="btn btn-primary" onclick="Vault.showAddModal()">+ 添加</button>' : ''}
        </div>
      </div>
      ${this.unlocked ? '<div id="vault-list"></div>' : this.lockScreen()}`;
    if (this.unlocked) this.loadEntries();
  },

  lockScreen() {
    return `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:60vh;gap:16px">
        <div style="font-size:3rem">🔒</div>
        <p style="color:var(--text-muted)">密码库已锁定，请输入主密码解锁</p>
        <div style="width:100%;max-width:300px">
          <input id="master-pwd" type="password" placeholder="主密码"
            onkeydown="if(event.key==='Enter')Vault.unlock()">
        </div>
        <button class="btn btn-primary" onclick="Vault.unlock()">解锁</button>
        <p style="font-size:0.8rem;color:var(--text-muted)">密码库内容加密存储，主密码不会上传至云端</p>
      </div>`;
  },

  async unlock() {
    const pwd = document.getElementById('master-pwd').value;
    if (!pwd) { App.toast('请输入主密码', 'error'); return; }
    try {
      await App.api('POST', '/api/v1/vault/unlock', { master_password: pwd });
      this.unlocked = true;
      this.render();
    } catch (e) {
      App.toast(e.message, 'error');
    }
  },

  async lock() {
    await App.api('POST', '/api/v1/vault/lock');
    this.unlocked = false;
    this.render();
    App.toast('密码库已锁定');
  },

  async loadEntries() {
    try {
      const entries = await App.api('GET', '/api/v1/vault');
      const list = document.getElementById('vault-list');
      if (!entries.length) { list.innerHTML = '<p style="color:var(--text-muted)">暂无保存的密码</p>'; return; }
      const catIcon = { wifi: '📶', bank: '🏦', website: '🌐', other: '🔑' };
      list.innerHTML = entries.map(e => `
        <div class="card" style="display:flex;align-items:center;gap:12px">
          <span style="font-size:1.5rem">${catIcon[e.category] || '🔑'}</span>
          <div style="flex:1">
            <div style="font-weight:600">${e.title}</div>
            ${e.url ? `<div style="font-size:0.8rem;color:var(--text-muted)">${e.url}</div>` : ''}
          </div>
          <button class="btn btn-ghost" style="padding:4px 10px;font-size:0.8rem"
            onclick="Vault.copyPassword(${e.id})">复制密码</button>
          <button class="btn btn-danger" style="padding:4px 10px;font-size:0.8rem"
            onclick="Vault.delete(${e.id})">删除</button>
        </div>`).join('');
    } catch (e) {
      if (e.message.includes('锁定')) { this.unlocked = false; this.render(); }
    }
  },

  async copyPassword(id) {
    try {
      const entry = await App.api('GET', `/api/v1/vault/${id}`);
      await navigator.clipboard.writeText(entry.password);
      App.toast(`已复制"${entry.title}"的密码到剪贴板`);
    } catch (e) {
      App.toast(e.message, 'error');
    }
  },

  showAddModal() {
    App.showModal('添加密码', `
      <div class="form-group"><label>标题 *</label><input id="v-title" placeholder="如：家庭WiFi"></div>
      <div class="form-group"><label>分类</label>
        <select id="v-cat"><option value="other">其他</option><option value="wifi">WiFi</option>
          <option value="bank">银行/金融</option><option value="website">网站账号</option></select>
      </div>
      <div class="form-group"><label>用户名</label><input id="v-user" placeholder="可选"></div>
      <div class="form-group"><label>密码 *</label><input id="v-pwd" type="password"></div>
      <div class="form-group"><label>网址</label><input id="v-url" placeholder="可选，如：https://..."></div>
      <div class="form-group"><label>备注</label><input id="v-notes" placeholder="可选"></div>`,
      async (overlay) => {
        const title = overlay.querySelector('#v-title').value.trim();
        const password = overlay.querySelector('#v-pwd').value;
        if (!title || !password) { App.toast('标题和密码为必填项', 'error'); return; }
        await App.api('POST', '/api/v1/vault', {
          title,
          category: overlay.querySelector('#v-cat').value,
          username: overlay.querySelector('#v-user').value || null,
          password,
          url: overlay.querySelector('#v-url').value || null,
          notes: overlay.querySelector('#v-notes').value || null,
        });
        App.toast('密码已安全保存');
        this.loadEntries();
      }, '保存');
  },

  async delete(id) {
    if (!confirm('确定要删除这条密码吗？')) return;
    await App.api('DELETE', `/api/v1/vault/${id}`);
    App.toast('已删除');
    this.loadEntries();
  },
};
