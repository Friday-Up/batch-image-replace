"""常量配置"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
USER_DATA_DIR = Path(os.path.expanduser("~")) / ".jzt_browser_data"
STEP_DELAY = 1.5

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
