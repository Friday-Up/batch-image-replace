"""常量配置"""

import glob
import os
import sys
from pathlib import Path

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
USER_DATA_DIR = Path(os.path.expanduser("~")) / ".jzt_browser_data"
STEP_DELAY = 1.5


def _find_in_patterns(patterns):
    for pattern in patterns:
        matches = glob.glob(str(pattern))
        if matches:
            exe = Path(matches[0])
            if exe.exists():
                return str(exe)
    return None


def get_chromium_path():
    """获取 Chromium 可执行文件路径，支持 PyInstaller 打包环境"""
    # 1. 先尝试 Playwright 自带的路径（源码运行时有效）
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            path = p.chromium.executable_path
        if Path(path).exists():
            return path
    except Exception:
        pass

    # 2. PyInstaller 打包环境：从 _MEIPASS 查找
    if hasattr(sys, "_MEIPASS"):
        meipass = Path(sys._MEIPASS)
        result = _find_in_patterns([
            meipass / "ms-playwright" / "chromium-*" / "chrome-win" / "chrome.exe",
            meipass / "ms-playwright" / "chromium-*" / "chrome.exe",
            meipass / "ms-playwright" / "chromium" / "chrome-win" / "chrome.exe",
        ])
        if result:
            return result

    # 3. 也尝试 BASE_DIR（项目根目录）
    result = _find_in_patterns([
        BASE_DIR / "ms-playwright" / "chromium-*" / "chrome-win" / "chrome.exe",
        BASE_DIR / "ms-playwright" / "chromium-*" / "chrome.exe",
        BASE_DIR / "ms-playwright" / "chromium" / "chrome-win" / "chrome.exe",
    ])
    if result:
        return result

    raise FileNotFoundError(
        "找不到 Chromium 可执行文件，请确认 Playwright 浏览器已正确打包。"
        f"BASE_DIR={BASE_DIR}, _MEIPASS={getattr(sys, '_MEIPASS', 'N/A')}"
    )


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
