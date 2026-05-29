const Voice = {
  initialized: false,
  ws: null,
  mediaRecorder: null,
  isRecording: false,
  audioChunks: [],
  audioContext: null,

  init() {
    if (this.initialized) return;
    this.initialized = true;
    const page = document.getElementById('page-voice');
    page.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;gap:24px;text-align:center">
        <h2 style="font-size:1.3rem;font-weight:700">🎤 语音对话</h2>
        <button id="voice-btn" title="按住说话">🎤</button>
        <p id="voice-status">点击按钮开始录音</p>
        <div class="card" style="width:100%;max-width:500px;text-align:left">
          <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:8px">识别内容</p>
          <div id="voice-transcript">-</div>
        </div>
        <div class="card" style="width:100%;max-width:500px;text-align:left">
          <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:8px">助理回复</p>
          <div id="voice-response">-</div>
        </div>
      </div>`;

    this.connectWS();
    const btn = document.getElementById('voice-btn');
    btn.addEventListener('mousedown', () => this.startRecording());
    btn.addEventListener('mouseup', () => this.stopRecording());
    btn.addEventListener('touchstart', (e) => { e.preventDefault(); this.startRecording(); });
    btn.addEventListener('touchend', (e) => { e.preventDefault(); this.stopRecording(); });
  },

  connectWS() {
    this.ws = new WebSocket(`ws://${location.host}/ws/voice`);
    this.ws.binaryType = 'arraybuffer';
    this.ws.onmessage = (e) => this.handleMessage(e);
    this.ws.onclose = () => setTimeout(() => this.connectWS(), 3000);
  },

  handleMessage(e) {
    if (e.data instanceof ArrayBuffer) {
      this.playAudio(e.data);
      return;
    }
    try {
      const msg = JSON.parse(e.data);
      if (msg.type === 'transcript') {
        document.getElementById('voice-transcript').textContent = msg.text;
      } else if (msg.type === 'response') {
        document.getElementById('voice-response').textContent = msg.text;
      } else if (msg.type === 'processing') {
        const steps = { stt: '正在识别语音...', llm: '正在思考...', tts: '正在合成语音...' };
        document.getElementById('voice-status').textContent = steps[msg.step] || '处理中...';
      } else if (msg.type === 'audio_start') {
        this.audioBuffer = [];
      } else if (msg.type === 'audio_end') {
        document.getElementById('voice-status').textContent = '点击按钮开始录音';
      } else if (msg.type === 'error') {
        document.getElementById('voice-status').textContent = `错误: ${msg.message}`;
        App.toast(msg.message, 'error');
      } else if (msg.type === 'reminder_triggered') {
        App.toast(`⏰ 提醒: ${msg.title}`, 'reminder', 10000);
      }
    } catch (_) {}
  },

  playAudio(data) {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    this.audioContext.decodeAudioData(data.slice(0), (buffer) => {
      const source = this.audioContext.createBufferSource();
      source.buffer = buffer;
      source.connect(this.audioContext.destination);
      source.start(0);
    });
  },

  async startRecording() {
    if (this.isRecording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      this.audioChunks = [];
      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0 && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(e.data);
        }
      };
      this.ws.send(JSON.stringify({ type: 'start_recording' }));
      this.mediaRecorder.start(250);
      this.isRecording = true;
      document.getElementById('voice-btn').classList.add('recording');
      document.getElementById('voice-status').textContent = '正在录音...';
    } catch (e) {
      App.toast('无法访问麦克风: ' + e.message, 'error');
    }
  },

  stopRecording() {
    if (!this.isRecording) return;
    this.mediaRecorder.stop();
    this.mediaRecorder.stream.getTracks().forEach(t => t.stop());
    this.ws.send(JSON.stringify({ type: 'end_recording' }));
    this.isRecording = false;
    document.getElementById('voice-btn').classList.remove('recording');
    document.getElementById('voice-status').textContent = '处理中...';
  },
};
