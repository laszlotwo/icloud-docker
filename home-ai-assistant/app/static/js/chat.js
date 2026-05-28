const Chat = {
  initialized: false,

  init() {
    if (this.initialized) return;
    this.initialized = true;
    const page = document.getElementById('page-chat');
    page.innerHTML = `
      <div style="display:flex;flex-direction:column;height:100%;padding:0">
        <div class="page-header" style="padding:16px 16px 0">
          <span class="page-title">💬 对话</span>
          <button class="btn btn-ghost" onclick="Chat.clearHistory()">清空记录</button>
        </div>
        <div id="chat-messages"></div>
        <div id="chat-input-row">
          <input id="chat-input" type="text" placeholder="输入消息，或按住麦克风说话..."
            onkeydown="if(event.key==='Enter')Chat.send()">
          <button class="btn btn-primary" onclick="Chat.send()">发送</button>
        </div>
      </div>`;
    this.loadHistory();
  },

  async loadHistory() {
    try {
      const history = await App.api('GET', '/api/v1/chat/history');
      history.forEach(h => this.appendMsg(h.role, h.content));
      this.scrollBottom();
    } catch (_) {}
  },

  appendMsg(role, text, isTyping = false) {
    const container = document.getElementById('chat-messages');
    const el = document.createElement('div');
    el.className = `msg ${role}${isTyping ? ' typing' : ''}`;
    el.textContent = text;
    container.appendChild(el);
    this.scrollBottom();
    return el;
  },

  scrollBottom() {
    const el = document.getElementById('chat-messages');
    if (el) el.scrollTop = el.scrollHeight;
  },

  async send() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    this.appendMsg('user', text);

    const assistantEl = this.appendMsg('assistant', '...', true);

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });

      assistantEl.textContent = '';
      assistantEl.classList.remove('typing');
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = decoder.decode(value).split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            try {
              const parsed = JSON.parse(data);
              assistantEl.textContent += parsed.text;
              this.scrollBottom();
            } catch (_) {}
          }
        }
      }
    } catch (e) {
      assistantEl.textContent = `错误: ${e.message}`;
    }
  },

  async clearHistory() {
    await App.api('DELETE', '/api/v1/chat/history');
    document.getElementById('chat-messages').innerHTML = '';
    App.toast('对话记录已清空');
  },
};
