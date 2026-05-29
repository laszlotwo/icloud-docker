const Expenses = {
  initialized: false,
  categories: ['餐饮', '购物', '交通', '医疗', '娱乐', '居家', '其他'],

  init() {
    if (this.initialized) return;
    this.initialized = true;
    const page = document.getElementById('page-expenses');
    page.innerHTML = `
      <div class="page-header">
        <span class="page-title">💰 开销记录</span>
        <button class="btn btn-primary" onclick="Expenses.showAddModal()">+ 记录消费</button>
      </div>
      <div id="expense-summary"></div>
      <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">
        ${this.categories.map(c => `<button class="btn btn-ghost" style="padding:3px 10px;font-size:0.8rem" onclick="Expenses.filterCat('${c}')">${c}</button>`).join('')}
        <button class="btn btn-ghost" style="padding:3px 10px;font-size:0.8rem" onclick="Expenses.filterCat('')">全部</button>
      </div>
      <div id="expenses-list"></div>`;
    this.loadSummary();
    this.load();
  },

  async loadSummary() {
    const s = await App.api('GET', '/api/v1/expenses/summary?period=month');
    const el = document.getElementById('expense-summary');
    const cats = Object.entries(s.by_category || {});
    el.innerHTML = `
      <div class="summary-grid" style="margin-bottom:16px">
        <div class="summary-card">
          <div class="amount">¥${s.total.toFixed(2)}</div>
          <div class="label">本月总支出</div>
        </div>
        <div class="summary-card">
          <div class="amount" style="font-size:1.2rem">${s.count}</div>
          <div class="label">本月笔数</div>
        </div>
      </div>
      ${cats.length ? `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
        ${cats.map(([k, v]) => `<span class="badge cat-${k}">${k}: ¥${v.toFixed(2)}</span>`).join('')}
      </div>` : ''}`;
  },

  async load(category = '') {
    const now = new Date();
    const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().slice(0, 10);
    let url = `/api/v1/expenses?start_date=${startDate}&limit=100`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    const items = await App.api('GET', url);
    this.render(items);
  },

  render(items) {
    const list = document.getElementById('expenses-list');
    if (!items.length) { list.innerHTML = '<p style="color:var(--text-muted)">本月暂无记录</p>'; return; }
    list.innerHTML = items.map(e => `
      <div class="card" style="display:flex;align-items:center;gap:12px">
        <span class="badge cat-${e.category}" style="white-space:nowrap">${e.category}</span>
        <div style="flex:1">
          <div style="font-weight:500">${e.description || e.category}</div>
          <div style="font-size:0.8rem;color:var(--text-muted)">${e.expense_date} ${e.payment_method ? '· ' + e.payment_method : ''}</div>
        </div>
        <div style="font-weight:700;font-size:1.1rem">¥${e.amount.toFixed(2)}</div>
        <button class="btn btn-danger" style="padding:4px 8px;font-size:0.75rem" onclick="Expenses.delete(${e.id})">×</button>
      </div>`).join('');
  },

  filterCat(cat) { this.load(cat); },

  showAddModal() {
    const today = new Date().toISOString().slice(0, 10);
    App.showModal('记录消费', `
      <div class="form-group"><label>金额 (元) *</label><input id="e-amount" type="number" step="0.01" min="0" placeholder="0.00"></div>
      <div class="form-group"><label>分类 *</label>
        <select id="e-cat">
          ${this.categories.map(c => `<option value="${c}">${c}</option>`).join('')}
        </select>
      </div>
      <div class="form-group"><label>消费说明</label><input id="e-desc" placeholder="如：星巴克拿铁"></div>
      <div class="form-group"><label>支付方式</label>
        <select id="e-pay"><option value="">未指定</option>
          <option>微信支付</option><option>支付宝</option><option>信用卡</option><option>现金</option><option>银行卡</option>
        </select>
      </div>
      <div class="form-group"><label>日期</label><input id="e-date" type="date" value="${today}"></div>`,
      async (overlay) => {
        const amount = parseFloat(overlay.querySelector('#e-amount').value);
        if (!amount || amount <= 0) { App.toast('请输入有效金额', 'error'); return; }
        await App.api('POST', '/api/v1/expenses', {
          amount,
          category: overlay.querySelector('#e-cat').value,
          description: overlay.querySelector('#e-desc').value.trim() || null,
          payment_method: overlay.querySelector('#e-pay').value || null,
          expense_date: overlay.querySelector('#e-date').value,
        });
        App.toast('消费已记录');
        this.loadSummary();
        this.load();
      }, '记录');
  },

  async delete(id) {
    if (!confirm('确定删除此记录？')) return;
    await App.api('DELETE', `/api/v1/expenses/${id}`);
    App.toast('已删除');
    this.loadSummary();
    this.load();
  },
};
