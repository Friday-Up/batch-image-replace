"""常量配置"""

import glob
import os
import sys
from pathlib import Path

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
USER_DATA_DIR = Path(os.path.expanduser("~")) / ".jzt_browser_data"
STEP_DELAY = 1.5


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

    # 2. PyInstaller 打包环境：_internal 目录下查找
    search_roots = []
    if hasattr(sys, "_MEIPASS"):
        search_roots.append(Path(sys._MEIPASS))
    search_roots.append(BASE_DIR)

    for root in search_roots:
        # 递归查找 chrome.exe
        for pattern in [
            root / "ms-playwright" / "chromium-*" / "chrome-win" / "chrome.exe",
            root / "ms-playwright" / "chromium-*" / "chrome.exe",
            root / "**" / "chrome.exe",
        ]:
            matches = glob.glob(str(pattern), recursive=("**" in str(pattern)))
            for match in matches:
                if Path(match).exists():
                    return str(Path(match).resolve())

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
