const Locations = {
  initialized: false,
  rooms: ['全部', '主卧', '客厅', '厨房', '书房', '卫生间', '其他'],

  init() {
    if (this.initialized) return;
    this.initialized = true;
    const page = document.getElementById('page-locations');
    page.innerHTML = `
      <div class="page-header">
        <span class="page-title">📍 物品位置</span>
        <button class="btn btn-primary" onclick="Locations.showAddModal()">+ 记录位置</button>
      </div>
      <div class="search-bar">
        <input id="loc-search" placeholder="搜索物品名称..." oninput="Locations.search(this.value)">
      </div>
      <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap" id="room-filters">
        ${this.rooms.map(r => `<button class="btn btn-ghost" style="padding:4px 12px;font-size:0.8rem" onclick="Locations.filterRoom('${r === '全部' ? '' : r}')">${r}</button>`).join('')}
      </div>
      <div id="locations-list"></div>`;
    this.load();
  },

  async load(room = '') {
    const url = room ? `/api/v1/locations?room=${encodeURIComponent(room)}` : '/api/v1/locations';
    const items = await App.api('GET', url);
    this.render(items);
  },

  render(items) {
    const list = document.getElementById('locations-list');
    if (!items.length) { list.innerHTML = '<p style="color:var(--text-muted)">暂无记录</p>'; return; }
    list.innerHTML = items.map(i => {
      const confirmed = i.last_confirmed_at ? new Date(i.last_confirmed_at).toLocaleDateString('zh-CN') : '未确认';
      return `
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <div>
              <div style="font-weight:600;font-size:1rem">${i.item_name}</div>
              <div style="color:var(--text-muted);font-size:0.875rem;margin-top:4px">📍 ${i.location}</div>
              ${i.container ? `<div style="font-size:0.8rem;color:var(--text-muted)">收纳: ${i.container}</div>` : ''}
              ${i.description ? `<div style="font-size:0.8rem;color:var(--text-muted)">备注: ${i.description}</div>` : ''}
            </div>
            <div style="text-align:right;flex-shrink:0">
              ${i.room ? `<span class="badge badge-blue">${i.room}</span>` : ''}
              <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px">确认: ${confirmed}</div>
            </div>
          </div>
          <div style="margin-top:10px;display:flex;gap:8px">
            <button class="btn btn-success" style="padding:4px 10px;font-size:0.8rem" onclick="Locations.confirm(${i.id})">✓ 确认位置</button>
            <button class="btn btn-ghost" style="padding:4px 10px;font-size:0.8rem" onclick="Locations.showEditModal(${JSON.stringify(i).replace(/"/g, '&quot;')})">编辑</button>
            <button class="btn btn-danger" style="padding:4px 10px;font-size:0.8rem" onclick="Locations.delete(${i.id})">删除</button>
          </div>
        </div>`;
    }).join('');
  },

  async search(q) {
    if (!q.trim()) { this.load(); return; }
    const results = await App.api('GET', `/api/v1/locations/search?q=${encodeURIComponent(q)}`);
    this.render(results);
  },

  filterRoom(room) { this.load(room); },

  showAddModal(item = null) {
    const title = item ? '编辑位置' : '记录物品位置';
    App.showModal(title, `
      <div class="form-group"><label>物品名称 *</label><input id="l-name" value="${item?.item_name || ''}" placeholder="如：护照"></div>
      <div class="form-group"><label>存放位置 *</label><input id="l-loc" value="${item?.location || ''}" placeholder="如：主卧衣柜上层左侧抽屉"></div>
      <div class="form-group"><label>所在房间</label>
        <select id="l-room">
          ${['', '主卧', '客厅', '厨房', '书房', '卫生间', '其他'].map(r => `<option value="${r}" ${item?.room === r ? 'selected' : ''}>${r || '未指定'}</option>`).join('')}
        </select>
      </div>
      <div class="form-group"><label>收纳容器</label><input id="l-container" value="${item?.container || ''}" placeholder="如：蓝色收纳盒"></div>
      <div class="form-group"><label>备注描述</label><input id="l-desc" value="${item?.description || ''}" placeholder="物品外观等补充说明"></div>`,
      async (overlay) => {
        const name = overlay.querySelector('#l-name').value.trim();
        const loc = overlay.querySelector('#l-loc').value.trim();
        if (!name || !loc) { App.toast('物品名称和位置为必填项', 'error'); return; }
        const data = {
          item_name: name,
          location: loc,
          room: overlay.querySelector('#l-room').value || null,
          container: overlay.querySelector('#l-container').value.trim() || null,
          description: overlay.querySelector('#l-desc').value.trim() || null,
        };
        if (item) {
          await App.api('PUT', `/api/v1/locations/${item.id}`, data);
          App.toast('已更新');
        } else {
          await App.api('POST', '/api/v1/locations', data);
          App.toast('位置已记录');
        }
        this.load();
      }, item ? '保存' : '记录');
  },

  showEditModal(item) { this.showAddModal(item); },

  async confirm(id) {
    await App.api('POST', `/api/v1/locations/${id}/confirm`);
    App.toast('位置已确认');
    this.load();
  },

  async delete(id) {
    if (!confirm('确定删除此记录？')) return;
    await App.api('DELETE', `/api/v1/locations/${id}`);
    App.toast('已删除');
    this.load();
  },
};
