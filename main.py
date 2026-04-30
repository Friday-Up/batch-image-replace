"""
京准通 - 批量换图自动化脚本

双击 scripts/批量换图.command 启动 GUI，或命令行：
  python main.py --excel data.xlsx --sku-col SKU --image-dir /path/to/images
"""

import argparse
import sys

from src.gui import run_gui
from src.core import run_batch


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

    from src.config import STEP_DELAY
    import src.config as cfg
    cfg.STEP_DELAY = args.delay

    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    run_batch(args.excel, args.sku_col, args.image_dir, scenarios)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_cli()
    else:
        run_gui()
