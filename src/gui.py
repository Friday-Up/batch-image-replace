"""GUI 相关"""

import json
import threading

from .core import run_batch


HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: #f7f8fa; color: #333; padding: 24px;
    -webkit-user-select: none; user-select: none;
  }
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 20px; color: #1a1a1a; }

  .form-row { display: flex; align-items: center; margin-bottom: 14px; }
  .form-row label {
    width: 90px; font-size: 14px; color: #555; text-align: right;
    margin-right: 12px; flex-shrink: 0;
  }
  .form-row input[type="text"] {
    flex: 1; height: 36px; border: 1px solid #d9d9d9; border-radius: 6px;
    padding: 0 12px; font-size: 13px; color: #333; background: #fff;
    outline: none; transition: border-color 0.2s;
  }
  .form-row input[type="text"]:focus { border-color: #e74c3c; }
  .form-row .hint {
    font-size: 12px; color: #999; margin-left: 8px; white-space: nowrap;
  }

  .btn {
    height: 36px; border: 1px solid #d9d9d9; border-radius: 6px;
    padding: 0 16px; font-size: 13px; cursor: pointer;
    background: #fff; color: #333; margin-left: 8px; flex-shrink: 0;
    transition: all 0.2s;
  }
  .btn:hover { border-color: #e74c3c; color: #e74c3c; }

  .btn-primary {
    background: #e74c3c; color: #fff; border: none; height: 40px;
    padding: 0 28px; font-size: 15px; font-weight: 600; border-radius: 6px;
    cursor: pointer; transition: background 0.2s;
  }
  .btn-primary:hover { background: #c0392b; }
  .btn-primary:disabled { background: #ccc; cursor: not-allowed; }

  .btn-secondary {
    background: #fff; color: #e74c3c; border: 1px solid #e74c3c;
    height: 40px; padding: 0 20px; font-size: 14px; border-radius: 6px;
    cursor: pointer; margin-left: 12px; transition: all 0.2s;
  }
  .btn-secondary:hover { background: #fef0ef; }
  .btn-secondary:disabled { color: #ccc; border-color: #ddd; cursor: not-allowed; }

  .btn-danger {
    background: #fff; color: #e74c3c; border: 1px solid #e74c3c;
    height: 40px; padding: 0 20px; font-size: 14px; border-radius: 6px;
    cursor: pointer; margin-left: 12px; transition: all 0.2s;
  }
  .btn-danger:hover { background: #e74c3c; color: #fff; }
  .btn-danger:disabled { color: #ccc; border-color: #ddd; cursor: not-allowed; background: #fff; }

  .actions { margin-top: 20px; display: flex; align-items: center; }

  .log-label {
    font-size: 13px; color: #888; margin-top: 20px; margin-bottom: 6px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .copy-btn {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; font-size: 12px; color: #888; background: transparent;
    border: 1px solid transparent; border-radius: 4px; cursor: pointer;
    transition: all 0.15s;
  }
  .copy-btn:hover { color: #e74c3c; border-color: #e74c3c; background: #fef0ef; }
  .copy-btn:active { background: #fde2df; }
  .copy-btn svg { width: 13px; height: 13px; }
  .copy-btn.copied { color: #4ec9b0; border-color: #4ec9b0; background: #f0faf7; }

  #log {
    width: 100%; height: 220px; background: #1e1e1e; color: #d4d4d4;
    border-radius: 8px; padding: 12px; font-family: "Menlo", "Consolas", monospace;
    font-size: 12px; line-height: 1.6; overflow-y: auto; white-space: pre-wrap;
    word-break: break-all;
    -webkit-user-select: text; user-select: text; cursor: text;
  }
  #log .success { color: #4ec9b0; }
  #log .error { color: #f44747; }
  #log .warn { color: #dcdcaa; }
</style>
</head>
<body>

<h1>京准通 - 批量换图工具</h1>

<div class="form-row">
  <label>Excel 文件</label>
  <input type="text" id="excelPath" readonly placeholder="点击右侧按钮选择文件">
  <button class="btn" onclick="pickExcel()">选择文件</button>
</div>

<div class="form-row">
  <label>SKU 列名</label>
  <input type="text" id="skuCol" value="SKU" style="max-width:150px;">
  <span class="hint">Excel 中 SKU 所在列的列名</span>
</div>

<div class="form-row">
  <label>图片文件夹</label>
  <input type="text" id="imageDir" readonly placeholder="点击右侧按钮选择文件夹">
  <button class="btn" onclick="pickImageDir()">选择文件夹</button>
</div>

<div class="form-row">
  <label>执行入口</label>
  <div style="display:flex; gap:18px; align-items:center;">
    <label style="width:auto; margin:0; font-size:13px; cursor:pointer;">
      <input type="checkbox" id="scn-keyword" checked> 关键词
    </label>
    <label style="width:auto; margin:0; font-size:13px; cursor:pointer;">
      <input type="checkbox" id="scn-crowd" checked> 人群
    </label>
    <label style="width:auto; margin:0; font-size:13px; cursor:pointer;">
      <input type="checkbox" id="scn-smart" checked> 智能化
    </label>
  </div>
</div>

<div class="actions">
  <button class="btn-primary" id="startBtn" onclick="startRun()">开始执行</button>
  <button class="btn-danger" id="stopBtn" onclick="stopRun()" style="display:none;">停止执行</button>
  <button class="btn-secondary" id="loginBtn" onclick="continueAfterLogin()" disabled>登录完成，继续执行</button>
</div>

<div class="log-label">
  <span>执行日志</span>
  <button class="copy-btn" id="copyLogBtn" onclick="copyLog()" title="复制全部日志">
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="4" y="4" width="9" height="10" rx="1.5"/>
      <path d="M3 11V3a1 1 0 0 1 1-1h7"/>
    </svg>
    <span id="copyLogText">复制</span>
  </button>
</div>
<div id="log"></div>

<script>
  function appendLog(msg) {
    const el = document.getElementById('log');
    let cls = '';
    if (msg.includes('✓') || msg.includes('成功')) cls = 'success';
    else if (msg.includes('✗') || msg.includes('失败') || msg.includes('错误')) cls = 'error';
    else if (msg.includes('⚠')) cls = 'warn';
    el.innerHTML += cls ? '<span class="' + cls + '">' + msg + '</span>\\n' : msg + '\\n';
    el.scrollTop = el.scrollHeight;
  }

  async function pickExcel() {
    const path = await pywebview.api.pick_excel();
    if (path) document.getElementById('excelPath').value = path;
  }

  async function pickImageDir() {
    const path = await pywebview.api.pick_image_dir();
    if (path) document.getElementById('imageDir').value = path;
  }

  async function startRun() {
    const excel = document.getElementById('excelPath').value;
    const skuCol = document.getElementById('skuCol').value;
    const imageDir = document.getElementById('imageDir').value;
    const scenarios = [];
    if (document.getElementById('scn-keyword').checked) scenarios.push('keyword');
    if (document.getElementById('scn-crowd').checked) scenarios.push('crowd');
    if (document.getElementById('scn-smart').checked) scenarios.push('smart');
    if (!excel) { alert('请选择 Excel 文件'); return; }
    if (!imageDir) { alert('请选择图片文件夹'); return; }
    if (scenarios.length === 0) { alert('请至少选择一个执行入口'); return; }
    document.getElementById('startBtn').disabled = true;
    document.getElementById('stopBtn').style.display = 'inline-block';
    document.getElementById('stopBtn').disabled = false;
    document.getElementById('log').innerHTML = '';
    await pywebview.api.start_run(excel, skuCol, imageDir, scenarios);
  }

  async function stopRun() {
    if (!confirm('确定要停止执行吗？当前 SKU 处理完会立即中断。')) return;
    document.getElementById('stopBtn').disabled = true;
    appendLog('⚠ 正在请求停止 ...');
    await pywebview.api.stop_run();
  }

  async function continueAfterLogin() {
    document.getElementById('loginBtn').disabled = true;
    await pywebview.api.continue_after_login();
  }

  async function copyLog() {
    const logEl = document.getElementById('log');
    // 用 innerText 拿带换行的纯文本（不含 HTML 标签）
    const text = logEl.innerText || logEl.textContent || '';
    if (!text.trim()) return;

    let ok = false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        ok = true;
      }
    } catch (e) {
      ok = false;
    }
    if (!ok) {
      // 兜底：通过 textarea + execCommand 复制（适配老环境/pywebview）
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        ok = document.execCommand('copy');
        document.body.removeChild(ta);
      } catch (e) {
        ok = false;
      }
    }
    if (!ok) {
      // 终极兜底：交给 Python 写剪贴板（pywebview 提供 evaluate_js 但不直接给剪贴板，
      // 这里没有就只能放弃；正常情况 execCommand 会成功）
      alert('复制失败，请手动选中复制');
      return;
    }

    const btn = document.getElementById('copyLogBtn');
    const txt = document.getElementById('copyLogText');
    const oldText = txt.textContent;
    btn.classList.add('copied');
    txt.textContent = '已复制';
    setTimeout(() => {
      btn.classList.remove('copied');
      txt.textContent = oldText;
    }, 1500);
  }
</script>
</body>
</html>
"""


class Api:
    def __init__(self, window_ref):
        self._window_ref = window_ref
        self._login_event = threading.Event()
        self._stop_event = threading.Event()

    def _reset_buttons(self):
        win = self._window_ref()
        if win:
            win.evaluate_js(
                'document.getElementById("startBtn").disabled = false;'
                'document.getElementById("stopBtn").style.display = "none";'
                'document.getElementById("stopBtn").disabled = false;'
            )

    def _log(self, msg):
        win = self._window_ref()
        if win:
            safe_msg = json.dumps(msg, ensure_ascii=False)
            win.evaluate_js(f"appendLog({safe_msg})")

    def pick_excel(self):
        import webview
        win = self._window_ref()
        if not win:
            return None
        result = win.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Excel Files (*.xlsx;*.xls)", "All Files (*.*)")
        )
        return result[0] if result else None

    def pick_image_dir(self):
        import webview
        win = self._window_ref()
        if not win:
            return None
        result = win.create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None

    def start_run(self, excel, sku_col, image_dir, scenarios):
        self._stop_event.clear()

        def _task():
            try:
                def login_wait():
                    self._log("⚠ 请在浏览器中手动登录，登录后点击「登录完成，继续执行」")
                    win = self._window_ref()
                    if win:
                        win.evaluate_js('document.getElementById("loginBtn").disabled = false')
                    self._login_event.clear()
                    self._login_event.wait()

                run_batch(excel, sku_col, image_dir, scenarios,
                          log_fn=self._log, wait_for_login_fn=login_wait,
                          stop_event=self._stop_event)
            except Exception as e:
                self._log(f"错误: {e}")
            finally:
                self._reset_buttons()

        threading.Thread(target=_task, daemon=True).start()

    def stop_run(self):
        self._stop_event.set()
        # 万一线程正卡在登录等待，也一并放行让它退出
        self._login_event.set()

    def continue_after_login(self):
        self._login_event.set()


def run_gui():
    import webview
    window = None
    api = Api(lambda: window)
    window = webview.create_window(
        "京准通 - 批量换图工具", html=HTML,
        width=780, height=680, resizable=False,
        js_api=api
    )
    webview.start()
