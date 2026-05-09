"""批量设置预算核心逻辑"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from dateutil import parser as dateutil_parser
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from .config import BUDGET_URL, STEP_DELAY
from .core import _ensure_browser, wait


def _parse_date(raw) -> tuple[int, int, int] | None:
    """解析各种日期格式，返回 (year, month, day) 或 None"""
    if pd.isna(raw):
        return None

    if isinstance(raw, (pd.Timestamp, datetime)):
        return (raw.year, raw.month, raw.day)

    text = str(raw).strip()
    if not text:
        return None

    m = re.match(r"(\d{1,2})月(\d{1,2})日?", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = datetime.now().year
        return (year, month, day)

    m = re.match(r"^(\d{1,2})[/\-](\d{1,2})$", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = datetime.now().year
        return (year, month, day)

    try:
        dt = dateutil_parser.parse(text)
        return (dt.year, dt.month, dt.day)
    except (ValueError, TypeError):
        return None


def parse_budget_excel(excel_path: str) -> tuple[pd.DataFrame, list[dict]]:
    """读取预算 Excel，返回 (df, records)"""
    df = pd.read_excel(excel_path, dtype={0: str})

    if "备注" not in df.columns:
        df["备注"] = ""

    plan_col = df.columns[0]
    date_cols = []
    for col in df.columns[1:]:
        if col == "备注":
            continue
        parsed = _parse_date(col)
        if parsed:
            date_cols.append((col, parsed))

    records = []
    for idx, row in df.iterrows():
        plan_name = str(row[plan_col]).strip() if pd.notna(row[plan_col]) else ""
        if not plan_name:
            continue

        budgets = []
        for col, (year, month, day) in date_cols:
            val = row[col]
            if pd.isna(val):
                continue
            val_str = str(val).strip()
            if not val_str:
                continue
            if val_str == "不限":
                budgets.append((year, month, day, "不限"))
            else:
                try:
                    num = float(val_str)
                    budgets.append((year, month, day, num))
                except ValueError:
                    continue

        if budgets:
            records.append({
                "plan_name": plan_name,
                "budgets": budgets,
                "row_idx": idx,
            })

    return df, records


def _wait_for_table(page, timeout=15000):
    """等待计划列表表格加载完成"""
    try:
        page.wait_for_selector('span.TestUIdaybuget', timeout=timeout)
    except PlaywrightTimeout:
        pass


def _wait_for_search_result(page, plan_name: str, timeout=10):
    """等待搜索结果刷新并包含目标计划名称"""
    safe_name = json.dumps(plan_name, ensure_ascii=False)
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = page.evaluate(f'''() => {{
            const name = {safe_name};
            const rows = document.querySelectorAll('tbody tr');
            for (const row of rows) {{
                if ((row.textContent || '').includes(name)) return true;
            }}
            return false;
        }}''')
        if found:
            return True
        wait(0.3)
    return False


def _find_budget_entry_pos(page, plan_name: str):
    """找到目标计划所在可见行的日预算入口坐标"""
    safe_name = json.dumps(plan_name, ensure_ascii=False)
    return page.evaluate(f'''() => {{
        const name = {safe_name};
        const rows = Array.from(document.querySelectorAll('tbody tr'));
        for (const row of rows) {{
            const rowRect = row.getBoundingClientRect();
            const rowStyle = window.getComputedStyle(row);
            if (rowRect.width === 0 || rowRect.height === 0) continue;
            if (rowStyle.display === 'none' || rowStyle.visibility === 'hidden') continue;
            if (!(row.textContent || '').includes(name)) continue;

            const budgetSpan = row.querySelector('span.TestUIdaybuget');
            if (!budgetSpan) continue;
            budgetSpan.scrollIntoView({{block: 'center', inline: 'center'}});
            const rect = budgetSpan.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) continue;
            return {{x: rect.x + rect.width / 2, y: rect.y + rect.height / 2}};
        }}
        return null;
    }}''')


def _open_budget_drawer(page, plan_name: str):
    """打开目标计划的预算抽屉"""
    last_pos = None
    for _ in range(2):
        pos = _find_budget_entry_pos(page, plan_name)
        if not pos:
            raise Exception(f"找不到计划「{plan_name}」对应的日预算入口")
        last_pos = pos
        page.mouse.click(pos['x'], pos['y'])
        try:
            page.wait_for_selector('.jad-modal-slide-main', state="visible", timeout=4000)
            return
        except PlaywrightTimeout:
            wait(0.8)
    raise Exception(f"预算设置抽屉未打开")


def _close_budget_popover(page):
    """关闭当前打开的日期预算弹窗"""
    try:
        visible_cw = page.locator('.content-warp:visible')
        if visible_cw.count() > 0:
            close_icon = visible_cw.first.locator('.icon-close').first
            close_icon.click()
            wait(0.4)
    except Exception:
        pass


def _wait_popover_visible(page, timeout=3000) -> bool:
    """等待日期预算弹窗出现，返回是否成功"""
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        if page.locator('.content-warp:visible').count() > 0:
            return True
        wait(0.15)
    return False


def _set_budget_for_date(page, year: int, month: int, day: int, value, log_fn=print):
    """在日历中点击指定日期格子，设置预算值"""
    target_date_str = f"{year}-{month:02d}-{day:02d}"

    _close_budget_popover(page)

    pos = page.evaluate(f'''() => {{
        const cells = document.querySelectorAll('td.day-cell');
        for (const cell of cells) {{
            const ds = cell.querySelector('span.cur-date');
            if (ds && ds.textContent.includes('{target_date_str}')) {{
                const price = cell.querySelector('.priceMod');
                if (price) {{
                    price.scrollIntoView({{block: 'center', inline: 'center'}});
                    const rect = price.getBoundingClientRect();
                    return {{x: rect.x + rect.width/2, y: rect.y + rect.height/2}};
                }}
            }}
        }}
        return null;
    }}''')

    if not pos:
        raise Exception(f"找不到日期 {target_date_str} 的格子，可能超出日历可见范围")

    page.mouse.click(pos['x'], pos['y'])
    if not _wait_popover_visible(page, 3000):
        page.mouse.click(pos['x'], pos['y'])
        if not _wait_popover_visible(page, 3000):
            raise Exception(f"点击日期 {target_date_str} 后弹窗未出现")

    cw = page.locator('.content-warp:visible').first

    if value == "不限":
        unlimited_btn = cw.locator('.budget-suffix').first
        unlimited_btn.click()
        wait(0.3)
    else:
        budget_input = cw.locator('input.jad-input').first
        budget_input.click(click_count=3)
        budget_val = str(int(value)) if float(value) == int(value) else str(value)
        budget_input.fill(budget_val)
        budget_input.press("Enter")
        wait(0.3)

    _close_budget_popover(page)


def _close_drawer(page):
    """关闭预算设置抽屉"""
    close_pos = page.evaluate('''() => {
        const btn = document.querySelector('.jzt-day-budget-modal-wrap .jad-icon-close2, .jad-modal-slide .jad-modal-close');
        if (btn) {
            const rect = btn.getBoundingClientRect();
            return {x: rect.x + rect.width/2, y: rect.y + rect.height/2};
        }
        return null;
    }''')
    if close_pos:
        page.mouse.click(close_pos['x'], close_pos['y'])
        wait(0.5)
    else:
        page.keyboard.press("Escape")
        wait(0.5)


def run_batch_budget(excel_path: str, log_fn=print, wait_for_login_fn=None, stop_event=None):
    """执行批量设置预算

    stop_event: 可选的 threading.Event；被 set 后在下一次计划边界处中断并保存进度。
    """

    def _is_stopped():
        return stop_event is not None and stop_event.is_set()

    df, records = parse_budget_excel(excel_path)

    if not records:
        df.to_excel(excel_path, index=False)
        log_fn("没有可处理的计划，备注已写回 Excel")
        return {"status": "done", "success": 0, "total": 0, "failed": []}

    log_fn(f"共 {len(records)} 个计划需要设置预算")
    for r in records:
        dates_str = ", ".join(f"{m}/{d}" for (_, m, d, _) in r["budgets"])
        log_fn(f"  {r['plan_name']} -> {len(r['budgets'])} 个日期 ({dates_str})")

    browser, page = _ensure_browser(log_fn)

    # SPA hash 路由导航 + reload 确保页面刷新
    page.evaluate('window.location.hash = "#/list/tab/plan?objective=overview"')
    wait(1)
    page.reload(wait_until="domcontentloaded", timeout=60000)
    _wait_for_table(page)

    if "passport" in page.url or "login" in page.url:
        log_fn("⚠ 请在浏览器中手动登录京准通")
        if wait_for_login_fn:
            wait_for_login_fn()
        else:
            input("登录成功后按回车继续 ...")
        page.evaluate('window.location.hash = "#/list/tab/plan?objective=overview"')
        wait(1)
        page.reload(wait_until="domcontentloaded", timeout=60000)
        _wait_for_table(page)

    total = 0
    success = 0
    failed = []
    stopped = False

    for i, record in enumerate(records, 1):
        if _is_stopped():
            stopped = True
            log_fn("⚠ 已收到停止信号，正在中断 ...")
            break

        total += 1
        plan_name = record["plan_name"]
        idx = record["row_idx"]
        log_fn(f"\n[{i}/{len(records)}] 计划: {plan_name}")

        try:
            # 搜索计划名称
            search_input = page.locator('input[placeholder*="请输入计划名称"]').first
            search_input.click()
            search_input.fill("")
            search_input.fill(plan_name)
            search_input.press("Enter")
            # 等搜索结果刷新并包含目标计划
            if not _wait_for_search_result(page, plan_name):
                raise Exception(f"搜索结果中未找到计划「{plan_name}」")

            # 打开目标计划的预算抽屉（含 scrollIntoView + 重试）
            _open_budget_drawer(page, plan_name)

            # 等日历内容渲染完成
            try:
                page.wait_for_selector('td.day-cell .priceMod', state="visible", timeout=5000)
            except PlaywrightTimeout:
                raise Exception("日历内容未加载完成")

            log_fn(f"  抽屉已打开")

            # 遍历该计划需要设置的每个日期
            for year, month, day, value in record["budgets"]:
                if _is_stopped():
                    stopped = True
                    break
                val_display = "不限" if value == "不限" else str(value)
                log_fn(f"  设置 {year}-{month:02d}-{day:02d} -> {val_display}")
                _set_budget_for_date(page, year, month, day, value, log_fn)

            if stopped:
                _close_drawer(page)
                break

            # 保存：先关闭可能残留的日期弹窗
            _close_budget_popover(page)
            wait(0.3)
            save_pos = page.evaluate('''() => {
                const btn = document.querySelector('.jad-modal-slide-footer button.jad-btn-primary');
                if (btn) {
                    const r = btn.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }
                return null;
            }''')
            if save_pos:
                page.mouse.click(save_pos['x'], save_pos['y'])
                # 等抽屉关闭表示保存完成
                try:
                    page.wait_for_selector('.jad-modal-slide-main', state="hidden", timeout=8000)
                except PlaywrightTimeout:
                    wait(1)
            else:
                raise Exception("找不到确定按钮")

            success += 1
            df.at[idx, "备注"] = "设置成功"
            log_fn(f"  ✓ 预算设置成功")

        except (PlaywrightTimeout, Exception) as e:
            err_msg = str(e).split("\nCall log:")[0]
            log_fn(f"  ✗ 失败: {err_msg}")
            failed.append(plan_name)
            df.at[idx, "备注"] = f"失败: {err_msg}"
            _close_drawer(page)

        if stopped:
            break

    try:
        browser.close()
    except Exception:
        pass
    df.to_excel(excel_path, index=False)
    log_fn(f"\n备注已写回 Excel")

    status = "stopped" if stopped else "done"
    if stopped:
        log_fn(f"已停止: 成功 {success}/{total}")
    else:
        log_fn(f"处理完成: 成功 {success}/{total}")
    if failed:
        log_fn(f"失败列表: {', '.join(failed)}")

    return {"status": status, "success": success, "total": total, "failed": failed}
