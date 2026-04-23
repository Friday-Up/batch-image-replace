"""
京准通 - 批量换图自动化脚本

双击 批量换图.command 启动 GUI，或命令行：
  python main.py --excel data.xlsx --sku-col SKU --image-dir /path/to/images
"""

import argparse
import glob
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# 三个入口的 URL 与备注列名
SCENARIOS = {
    "keyword": {
        "label": "关键词",
        "url": (
            "https://jzt.jd.com/msa/#/list/tab/creative"
            "?objective=item&scenario=normal&targetingType=keyword&activeTab=creative"
        ),
        "remark_col": "关键词备注",
    },
    "crowd": {
        "label": "人群",
        "url": (
            "https://jzt.jd.com/msa/#/list/tab/creative"
            "?objective=item&scenario=normal&targetingType=crowd&activeTab=creative"
        ),
        "remark_col": "人群备注",
    },
    "smart": {
        "label": "智能化",
        "url": (
            "https://jzt.jd.com/msa/#/list/smart"
            "?objective=item&scenario=normal&targetingType=smart"
        ),
        "remark_col": "智能化备注",
    },
}
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
USER_DATA_DIR = Path(os.path.expanduser("~")) / ".jzt_browser_data"
STEP_DELAY = 1.5


# ========== 核心逻辑 ==========

def find_images_for_sku(image_dir: Path, sku: str) -> list[str]:
    patterns = [f"{sku}-*.*", f"{sku}.*"]
    found = []
    for pattern in patterns:
        found.extend(glob.glob(str(image_dir / pattern)))
    return sorted(set(found))


def load_input(excel_path: str, sku_col: str, image_dir: str, scenarios: list[str]):
    df = pd.read_excel(excel_path, dtype=str)
    if sku_col not in df.columns:
        raise ValueError(f"Excel 中找不到列「{sku_col}」，可用的列: {', '.join(df.columns.tolist())}")

    # 按选中的入口创建对应备注列
    for key in scenarios:
        col = SCENARIOS[key]["remark_col"]
        if col not in df.columns:
            df[col] = ""

    image_dir_path = Path(image_dir)
    if not image_dir_path.exists():
        raise FileNotFoundError(f"图片文件夹不存在: {image_dir}")

    records = []
    for idx, row in df.iterrows():
        sku = str(row[sku_col]).strip() if pd.notna(row[sku_col]) else ""
        if not sku:
            continue
        images = find_images_for_sku(image_dir_path, sku)
        if not images:
            for key in scenarios:
                df.at[idx, SCENARIOS[key]["remark_col"]] = "未找到匹配图片"
            continue
        records.append({"sku": sku, "image_path": images[0], "row_idx": idx})

    return df, records


def wait(seconds: float = STEP_DELAY):
    time.sleep(seconds)


def process_sku_batch(page, sku: str, image_path: str, url: str):
    """关键词 / 人群入口：搜索 → 全选 → 修改图片 → 上传 → 确定"""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    wait(2)

    search_input = page.locator('input[placeholder*="创意名称"]')
    search_input.click()
    wait(0.5)
    search_input.fill(sku)
    wait(0.5)
    search_input.press("Enter")
    wait(3)

    select_all = page.locator(
        'thead input[type="checkbox"], th input[type="checkbox"], '
        '.ant-table-selection input[type="checkbox"]'
    ).first
    if not select_all.is_visible():
        select_all = page.locator('table input[type="checkbox"]').first
    if select_all.is_disabled():
        raise Exception("搜索无结果，跳过")
    select_all.click()
    wait(1)

    page.get_by_text("修改图片").click()
    wait(2)

    upload_btn = page.get_by_text("上传图片")
    with page.expect_file_chooser() as fc_info:
        upload_btn.click()
    fc_info.value.set_files(image_path)
    wait(3)

    error_modal = page.locator('.upload-error-modal')
    if error_modal.is_visible():
        error_modal.locator('button').first.click()
        wait(1)
        raise Exception("图片上传失败，请检查图片格式和尺寸")

    page.locator('button.jad-btn-primary.jad-btn-large', has_text="确定").click()
    wait(2)


def _close_modal(page):
    """关闭残留的抽屉/遮罩"""
    try:
        close_btn = page.locator('.jad-modal-slide .jad-modal-close').first
        if close_btn.is_visible(timeout=1000):
            close_btn.click()
            wait(1)
            return
    except Exception:
        pass
    try:
        page.keyboard.press("Escape")
        wait(1)
    except Exception:
        pass


def process_sku_smart(page, sku: str, image_path: str, url: str):
    """智能化入口：搜索 SKU ID → 对每一行点击编辑 → 抽屉中上传图片 → 确认"""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    wait(2)

    # 关闭残留遮罩/抽屉
    _close_modal(page)

    # 先点击「商品」标签页
    product_tab = page.locator('span.jad-tabs-nav-tab-no-icon', has_text="商品").first
    product_tab.click(timeout=10000)
    wait(2)

    search_input = page.locator('input[placeholder*="SKU"]').first
    search_input.click()
    wait(0.5)
    search_input.fill(sku)
    wait(0.5)
    search_input.press("Enter")
    wait(3)

    edit_buttons = page.get_by_role("button", name="编辑")
    count = edit_buttons.count()
    if count == 0:
        edit_buttons = page.locator('table').get_by_text("编辑", exact=True)
        count = edit_buttons.count()
    if count == 0:
        raise Exception("搜索无结果，跳过")

    success_n = 0
    last_err = None
    for i in range(count):
        try:
            edit_buttons.nth(i).click()
            wait(2)

            upload_btn = page.locator('.jad-modal-slide button, .jad-modal-slide span').filter(has_text="上传图片").first
            with page.expect_file_chooser() as fc_info:
                upload_btn.click(timeout=10000)
            fc_info.value.set_files(image_path)
            wait(3)

            error_modal = page.locator('.upload-error-modal')
            if error_modal.is_visible():
                error_modal.locator('button').first.click()
                wait(1)
                raise Exception("图片上传失败，请检查图片格式和尺寸")

            confirm = page.locator('.jad-modal-slide button', has_text="确认").or_(
                page.locator('.jad-modal-slide button', has_text="确定")
            ).first
            confirm.click(timeout=10000)
            wait(2)
            success_n += 1
        except Exception as e:
            last_err = str(e).split("\nCall log:")[0]
            _close_modal(page)

    if success_n == 0:
        raise Exception(last_err or "全部行处理失败")
    if success_n < count:
        raise Exception(f"部分成功 {success_n}/{count}: {last_err}")


def _ensure_browser(log_fn):
    """确保浏览器启动并返回 (browser, page)"""
    with sync_playwright() as p:
        chromium_path = p.chromium.executable_path

    debug_port = 9222
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", debug_port))
        s.close()
        log_fn("检测到已有浏览器运行，复用中 ...")
    except (ConnectionRefusedError, OSError):
        log_fn("启动浏览器 ...")
        cmd = [
            chromium_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={str(USER_DATA_DIR)}",
            "--window-size=1440,900",
            "--no-first-run",
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait(3)

    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else context.new_page()
    return browser, page


def run_batch(excel_path: str, sku_col: str, image_dir: str, scenarios: list[str],
              log_fn=print, wait_for_login_fn=None):
    """执行批量换图。scenarios: ["keyword", "crowd", "smart"] 的子集"""
    if not scenarios:
        raise ValueError("至少需要选择一个入口")
    for key in scenarios:
        if key not in SCENARIOS:
            raise ValueError(f"未知入口: {key}")

    df, records = load_input(excel_path, sku_col, image_dir, scenarios)

    no_image_count = sum(
        1 for _, row in df.iterrows()
        if row.get(SCENARIOS[scenarios[0]]["remark_col"]) == "未找到匹配图片"
    )
    if no_image_count:
        log_fn(f"⚠ {no_image_count} 个 SKU 未找到匹配图片")

    if not records:
        df.to_excel(excel_path, index=False)
        log_fn("没有可处理的 SKU，备注已写回 Excel")
        return {"status": "done", "success": 0, "total": 0, "failed": []}

    log_fn(f"共 {len(records)} 条记录 × {len(scenarios)} 个入口")
    for r in records:
        log_fn(f"  {r['sku']} -> {Path(r['image_path']).name}")

    browser, page = _ensure_browser(log_fn)

    # 用第一个入口检测登录态
    first_url = SCENARIOS[scenarios[0]]["url"]
    page.goto(first_url, wait_until="domcontentloaded", timeout=60000)
    wait(2)

    if "passport" in page.url or "login" in page.url:
        log_fn("⚠ 请在浏览器中手动登录京准通")
        if wait_for_login_fn:
            wait_for_login_fn()
        else:
            input("登录成功后按回车继续 ...")
        page.goto(first_url, wait_until="domcontentloaded", timeout=60000)
        wait(3)

    total = 0
    success = 0
    failed = []
    for key in scenarios:
        scn = SCENARIOS[key]
        log_fn(f"\n========== 入口: {scn['label']} ==========")
        handler = process_sku_smart if key == "smart" else process_sku_batch
        for i, record in enumerate(records, 1):
            total += 1
            idx = record["row_idx"]
            sku = record["sku"]
            log_fn(f"[{scn['label']} {i}/{len(records)}] SKU: {sku} | 图片: {Path(record['image_path']).name}")
            try:
                handler(page, sku, record["image_path"], scn["url"])
                success += 1
                df.at[idx, scn["remark_col"]] = "换图成功"
                log_fn(f"  ✓ {scn['label']}换图成功")
            except (PlaywrightTimeout, Exception) as e:
                err_msg = str(e).split("\nCall log:")[0]
                log_fn(f"  ✗ {scn['label']}失败: {err_msg}")
                failed.append(f"{scn['label']}:{sku}")
                df.at[idx, scn["remark_col"]] = f"失败: {err_msg}"

    browser.close()
    df.to_excel(excel_path, index=False)
    log_fn(f"\n备注已写回 Excel")
    log_fn(f"处理完成: 成功 {success}/{total}")
    if failed:
        log_fn(f"失败列表: {', '.join(failed)}")
    return {"status": "done", "success": success, "total": total, "failed": failed}


# ========== GUI (pywebview) ==========

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


# ========== CLI ==========

def main_cli():
    parser = argparse.ArgumentParser(description="京准通批量换图")
    parser.add_argument("--excel", required=True, help="Excel 文件路径")
    parser.add_argument("--sku-col", default="SKU", help="SKU 所在列名（默认: SKU）")
    parser.add_argument("--image-dir", required=True, help="图片文件夹路径")
    parser.add_argument(
        "--scenarios", default="keyword,crowd,smart",
        help="执行的入口，逗号分隔。可选: keyword,crowd,smart（默认全部）"
    )
    parser.add_argument("--delay", type=float, default=1.5, help="操作间隔秒数")
    args = parser.parse_args()

    global STEP_DELAY
    STEP_DELAY = args.delay
    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    run_batch(args.excel, args.sku_col, args.image_dir, scenarios)


# ========== 入口 ==========

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_cli()
    else:
        run_gui()
