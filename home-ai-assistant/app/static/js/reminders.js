const Reminders = {
  initialized: false,

  init() {
    if (this.initialized) return;
    this.initialized = true;
    const page = document.getElementById('page-reminders');
    page.innerHTML = `
      <div class="page-header">
        <span class="page-title">⏰ 提醒闹钟</span>
        <button class="btn btn-primary" onclick="Reminders.showAddModal()">+ 新建提醒</button>
      </div>
      <div id="reminders-list"></div>`;
    this.load();
  },

  async load() {
    const items = await App.api('GET', '/api/v1/reminders?include_inactive=true');
    this.render(items);
  },

  render(items) {
    const list = document.getElementById('reminders-list');
    if (!items.length) { list.innerHTML = '<p style="color:var(--text-muted)">暂无提醒</p>'; return; }
    const typeLabel = { once: '一次性', daily: '每天', weekly: '每周', cron: '自定义' };
    list.innerHTML = items.map(r => `
      <div class="card ${r.is_active ? '' : 'opacity-50'}" style="${r.is_active ? '' : 'opacity:0.5'}">
        <div style="display:flex;align-items:start;gap:12px">
          <span style="font-size:1.5rem">${r.is_active ? '🔔' : '🔕'}</span>
          <div style="flex:1">
            <div style="font-weight:600">${r.title}</div>
            ${r.description ? `<div style="font-size:0.85rem;color:var(--text-muted)">${r.description}</div>` : ''}
            <div style="font-size:0.8rem;color:var(--text-muted);margin-top:4px">
              <span class="badge badge-gray">${typeLabel[r.reminder_type] || r.reminder_type}</span>
              &nbsp;${r.trigger_spec}
            </div>
            ${r.next_trigger_at ? `<div style="font-size:0.8rem;color:var(--primary);margin-top:2px">下次触发: ${new Date(r.next_trigger_at).toLocaleString('zh-CN')}</div>` : ''}
          </div>
          <div style="display:flex;gap:6px;flex-shrink:0">
            <button class="btn btn-ghost" style="padding:4px 8px;font-size:0.8rem" onclick="Reminders.toggle(${r.id})">${r.is_active ? '暂停' : '启用'}</button>
            <button class="btn btn-danger" style="padding:4px 8px;font-size:0.8rem" onclick="Reminders.delete(${r.id})">删除</button>
          </div>
        </div>
      </div>`).join('');
  },

  showAddModal() {
    const now = new Date();
    const defaultDt = new Date(now.getTime() + 3600000).toISOString().slice(0, 16);
    App.showModal('新建提醒', `
      <div class="form-group"><label>提醒标题 *</label><input id="r-title" placeholder="如：吃药、开会、缴水电费"></div>
      <div class="form-group"><label>备注说明</label><input id="r-desc" placeholder="可选"></div>
      <div class="form-group"><label>重复类型 *</label>
        <select id="r-type" onchange="Reminders.updateTriggerUI()">
          <option value="once">一次性</option>
          <option value="daily">每天</option>
          <option value="weekly">每周</option>
          <option value="cron">自定义(Cron)</option>
        </select>
      </div>
      <div id="r-trigger-ui">
        <div class="form-group"><label>触发时间</label><input id="r-spec" type="datetime-local" value="${defaultDt}"></div>
      </div>`,
      async (overlay) => {
        const title = overlay.querySelector('#r-title').value.trim();
        const spec = overlay.querySelector('#r-spec').value;
        if (!title || !spec) { App.toast('标题和触发时间为必填项', 'error'); return; }
        const type = overlay.querySelector('#r-type').value;
        let trigger_spec = spec;
        if (type === 'once') trigger_spec = new Date(spec).toISOString().slice(0, 19);
        await App.api('POST', '/api/v1/reminders', {
          title,
          description: overlay.querySelector('#r-desc').value.trim() || null,
          reminder_type: type,
          trigger_spec,
        });
        App.toast('提醒已创建');
        this.load();
      }, '创建');

    // Setup change handler after modal is inserted
    setTimeout(() => {
      const sel = document.getElementById('r-type');
      if (sel) sel.addEventListener('change', () => this.updateTriggerUI());
    }, 50);
  },

  updateTriggerUI() {
    const type = document.getElementById('r-type').value;
    const ui = document.getElementById('r-trigger-ui');
    if (type === 'once') {
      const now = new Date(Date.now() + 3600000).toISOString().slice(0, 16);
      ui.innerHTML = `<div class="form-group"><label>触发时间</label><input id="r-spec" type="datetime-local" value="${now}"></div>`;
    } else if (type === 'daily') {
      ui.innerHTML = `<div class="form-group"><label>每天触发时间 (HH:MM)</label><input id="r-spec" type="time" value="07:00"></div>`;
    } else if (type === 'weekly') {
      ui.innerHTML = `
        <div class="form-group"><label>触发时间 (HH:MM)</label><input id="r-time" type="time" value="07:00"></div>
        <div class="form-group"><label>重复日期</label>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            ${[['mon','周一'],['tue','周二'],['wed','周三'],['thu','周四'],['fri','周五'],['sat','周六'],['sun','周日']].map(([v,l]) =>
              `<label style="display:flex;align-items:center;gap:4px;font-size:0.85rem"><input type="checkbox" value="${v}" class="day-cb"> ${l}</label>`).join('')}
          </div>
        </div>
        <input id="r-spec" type="hidden">`;
      // Sync hidden input
      setTimeout(() => {
        const sync = () => {
          const days = [...document.querySelectorAll('.day-cb:checked')].map(c => c.value).join(',');
          const time = document.getElementById('r-time').value;
          const spec = document.getElementById('r-spec');
          if (spec) spec.value = `${days || 'mon'} ${time}`;
        };
        document.querySelectorAll('.day-cb, #r-time').forEach(el => el.addEventListener('change', sync));
        sync();
      }, 50);
    } else {
      ui.innerHTML = `<div class="form-group"><label>Cron 表达式</label><input id="r-spec" placeholder="如：0 8 * * 1-5 (工作日早8点)"></div>`;
    }
  },

  async toggle(id) {
    await App.api('POST', `/api/v1/reminders/${id}/toggle`);
    App.toast('已更新提醒状态');
    this.load();
  },

  async delete(id) {
    if (!confirm('确定删除此提醒？')) return;
    await App.api('DELETE', `/api/v1/reminders/${id}`);
    App.toast('已删除');
    this.load();
  },
};
