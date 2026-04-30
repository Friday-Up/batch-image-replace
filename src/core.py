"""核心换图逻辑"""

import glob
import socket
import subprocess
import time
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from .config import BASE_DIR, SCENARIOS, STEP_DELAY, USER_DATA_DIR, get_chromium_path


def wait(seconds: float = STEP_DELAY):
    time.sleep(seconds)


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

    _close_modal(page)

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
    chromium_path = get_chromium_path()

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
