# 京准通 - 批量换图工具

自动化批量替换京准通创意主图的桌面工具。

## 功能

- 读取 Excel 中的 SKU 列表
- 自动按 `SKU-1.jpg` 命名规则匹配本地图片文件夹
- 自动登录京准通，逐个 SKU 完成搜索 → 全选 → 上传图片 → 确定
- 执行结果写回 Excel 的「备注」列

## 使用

### Windows 用户（推荐）
从 [Actions](../../actions) 下载最新构建的 `京东批量换图-Windows.zip`，解压后双击 `JD-BatchImageReplace.exe`。

### Mac / 开发者

```bash
pip install -r requirements.txt
playwright install chromium

# GUI 模式
python3 main.py

# CLI 模式
python3 main.py --excel data.xlsx --sku-col SKU --image-dir /path/to/images
```

## 输入格式

**Excel：** 至少需要一列 SKU（默认列名 `SKU`）

| SKU | 备注（脚本自动填写） |
|---|---|
| 100332393690 | |

**图片文件夹：** 文件命名为 `SKU-序号.jpg`，例如 `100332393690-1.jpg`
