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

  .actions { margin-top: 20px; display: flex; align-items: center; }

  .log-label { font-size: 13px; color: #888; margin-top: 20px; margin-bottom: 6px; }
  #log {
    width: 100%; height: 220px; background: #1e1e1e; color: #d4d4d4;
    border-radius: 8px; padding: 12px; font-family: "Menlo", "Consolas", monospace;
    font-size: 12px; line-height: 1.6; overflow-y: auto; white-space: pre-wrap;
    word-break: break-all;
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
  <button class="btn-secondary" id="loginBtn" onclick="continueAfterLogin()" disabled>登录完成，继续执行</button>
</div>

<div class="log-label">执行日志</div>
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
    document.getElementById('log').innerHTML = '';
    await pywebview.api.start_run(excel, skuCol, imageDir, scenarios);
  }

  async function continueAfterLogin() {
    document.getElementById('loginBtn').disabled = true;
    await pywebview.api.continue_after_login();
  }
</script>
</body>
</html>
"""


class Api:
    def __init__(self, window_ref):
        self._window_ref = window_ref
        self._login_event = threading.Event()

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
        def _task():
            try:
                def login_wait():
                    self._log("⚠ 请在浏览器中手动登录，登录后点击「登录完成，继续执行」")
                    win = self._window_ref()
                    if win:
                        win.evaluate_js('document.getElementById("loginBtn").disabled = false')
                    self._login_event.clear()
                    self._login_event.wait()

                result = run_batch(excel, sku_col, image_dir, scenarios,
                                   log_fn=self._log, wait_for_login_fn=login_wait)
                if result and result["status"] == "done":
                    win = self._window_ref()
                    if win:
                        win.evaluate_js('document.getElementById("startBtn").disabled = false')
            except Exception as e:
                self._log(f"错误: {e}")
                win = self._window_ref()
                if win:
                    win.evaluate_js('document.getElementById("startBtn").disabled = false')

        threading.Thread(target=_task, daemon=True).start()

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
