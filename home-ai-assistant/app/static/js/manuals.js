const Manuals = {
  initialized: false,
  data: [],

  init() {
    if (this.initialized) return;
    this.initialized = true;
    const page = document.getElementById('page-manuals');
    page.innerHTML = `
      <div class="page-header">
        <span class="page-title">📖 设备说明书</span>
        <button class="btn btn-primary" onclick="Manuals.showAddModal()">+ 添加说明书</button>
      </div>
      <div class="search-bar">
        <input id="manuals-search" placeholder="搜索设备名称或内容..." oninput="Manuals.search(this.value)">
      </div>
      <div id="manuals-grid" class="grid"></div>`;
    this.load();
  },

  async load() {
    this.data = await App.api('GET', '/api/v1/manuals');
    this.render(this.data);
  },

  render(items) {
    const grid = document.getElementById('manuals-grid');
    if (!items.length) { grid.innerHTML = '<p style="color:var(--text-muted)">暂无说明书，点击右上角添加</p>'; return; }
    grid.innerHTML = items.map(m => `
      <div class="card" style="cursor:pointer" onclick="Manuals.view(${m.id})">
        <div style="display:flex;justify-content:space-between;align-items:start">
          <div>
            <div style="font-weight:600">${m.name}</div>
            ${m.brand ? `<div style="font-size:0.8rem;color:var(--text-muted)">${m.brand}</div>` : ''}
          </div>
          ${m.category ? `<span class="badge badge-blue">${m.category}</span>` : ''}
        </div>
        <div style="margin-top:8px;display:flex;gap:8px">
          <button class="btn btn-ghost" style="padding:4px 10px;font-size:0.8rem" onclick="event.stopPropagation();Manuals.view(${m.id})">查看</button>
          <button class="btn btn-danger" style="padding:4px 10px;font-size:0.8rem" onclick="event.stopPropagation();Manuals.delete(${m.id})">删除</button>
        </div>
      </div>`).join('');
  },

  async search(q) {
    if (!q.trim()) { this.render(this.data); return; }
    try {
      const results = await App.api('GET', `/api/v1/manuals/search?q=${encodeURIComponent(q)}`);
      this.render(results);
    } catch (_) {}
  },

  async view(id) {
    const manual = await App.api('GET', `/api/v1/manuals/${id}`);
    App.showModal(manual.name, `
      <div style="font-size:0.85rem;white-space:pre-wrap;max-height:50vh;overflow-y:auto">${manual.content}</div>`, () => {});
  },

  showAddModal() {
    App.showModal('添加说明书', `
      <div class="form-group"><label>设备名称 *</label><input id="m-name" placeholder="如：小米扫地机器人 S10"></div>
      <div class="form-group"><label>品牌</label><input id="m-brand" placeholder="如：小米"></div>
      <div class="form-group"><label>分类</label>
        <select id="m-category">
          <option value="">选择分类</option>
          <option>家电</option><option>厨具</option><option>路由器</option><option>安防</option><option>其他</option>
        </select>
      </div>
      <div class="form-group"><label>说明书内容 *</label>
        <textarea id="m-content" rows="6" placeholder="粘贴说明书文字内容..."></textarea>
      </div>`, async (overlay) => {
        const name = overlay.querySelector('#m-name').value.trim();
        const content = overlay.querySelector('#m-content').value.trim();
        if (!name || !content) { App.toast('名称和内容为必填项', 'error'); return; }
        await App.api('POST', '/api/v1/manuals', {
          name,
          brand: overlay.querySelector('#m-brand').value.trim() || null,
          category: overlay.querySelector('#m-category').value || null,
          content,
        });
        App.toast('说明书已添加');
        this.load();
      }, '添加');
  },

  async delete(id) {
    if (!confirm('确定要删除这本说明书吗？')) return;
    await App.api('DELETE', `/api/v1/manuals/${id}`);
    App.toast('已删除');
    this.load();
  },
};
