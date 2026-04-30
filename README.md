# 京准通批量换图工具

[![Build Windows EXE](https://github.com/Friday-Up/batch-image-replace/actions/workflows/build-windows.yml/badge.svg)](https://github.com/Friday-Up/batch-image-replace/actions/workflows/build-windows.yml)
[![Release](https://img.shields.io/github/v/release/Friday-Up/batch-image-replace)](https://github.com/Friday-Up/batch-image-replace/releases)

自动化批量替换京准通创意主图的桌面工具，支持关键词、人群、智能化三大入口。

---

## 功能特性

- **三入口全覆盖**：关键词、人群、智能化，一次配置全部搞定
- **Excel 驱动**：读取 SKU 列表，执行结果自动写回备注列
- **智能匹配图片**：按 `SKU-1.jpg` 命名规则自动匹配本地图片
- **可视化操作**：内置 GUI，无需命令行，开箱即用
- **登录态持久化**：浏览器登录信息自动保存，下次免登

---

## 快速开始

### Windows 用户（推荐）

1. 从 [Releases](../../releases) 下载最新版本 `京准通批量换图-Windows.zip`
2. 解压到任意文件夹（建议路径不含中文）
3. 双击 `JD-BatchImageReplace.exe` 启动
4. 首次启动约 10 秒，请耐心等待

> **提示**：如果 Windows 提示"未知发布者"，请点击「更多信息」→「仍要运行」。

### Mac / 开发者

```bash
pip install -r requirements.txt
playwright install chromium

# GUI 模式
python3 main.py

# CLI 模式
python3 main.py --excel data.xlsx --sku-col SKU --image-dir /path/to/images
```

---

## 使用指南

### 1. 准备数据

**Excel 文件**：至少包含一列 SKU（默认列名 `SKU`）

| SKU | 关键词备注 | 人群备注 | 智能化备注 |
|-----|-----------|---------|-----------|
| 100332393690 | | | |

**图片文件夹**：按 `SKU-序号.扩展名` 命名，例如：

```
images/
├── 100332393690-1.jpg
├── 100332393690-2.png
├── 100311842764-1.jpg
└── ...
```

### 2. 执行流程

1. 点击「选择文件」加载 Excel
2. 确认 SKU 列名（默认 `SKU`）
3. 点击「选择文件夹」加载图片目录
4. 勾选需要执行的入口（关键词 / 人群 / 智能化）
5. 点击「开始执行」
6. 首次运行会弹出 Chromium 浏览器，**手动登录京准通**
7. 登录成功后，回到工具窗口点击「登录完成，继续执行」
8. 等待执行完成，查看 Excel「备注」列结果

### 3. 结果说明

| 备注内容 | 含义 |
|---------|------|
| `换图成功` | 该 SKU 对应入口已替换完成 |
| `未找到匹配图片` | 图片文件夹中无对应 SKU 的图片 |
| `失败: xxx` | 操作失败原因，详见错误信息 |

---

## 注意事项

- **图片规格**：
  - 竖图：350×520（PNG/JPG，1-500KB）
  - 方图：1:1（350-1500px，PNG/JPG，1-3072KB）
- **执行过程中请勿手动操作浏览器**，会打断自动化流程
- **登录态自动保存**，下次启动无需重新登录
- **杀毒软件误报**：如遇到误报，请将程序加入信任列表

---

## 技术栈

- Python 3.11
- Playwright（浏览器自动化）
- pywebview（桌面 GUI）
- pandas / openpyxl（Excel 处理）
- PyInstaller（打包分发）

---

## 常见问题

**Q: 为什么首次启动比较慢？**
> A: 首次启动需要初始化 Playwright 浏览器环境，约 10 秒，后续启动正常。

**Q: 可以批量处理多少个 SKU？**
> A: 理论上无上限，建议单次不超过 500 个，避免京准通页面超时。

**Q: 支持哪些图片格式？**
> A: PNG、JPG、JPEG。建议按京准通要求的尺寸和大小准备。

**Q: 智能化入口和关键词/人群有什么区别？**
> A: 关键词和人群入口可以批量修改同一 SKU 下的所有创意；智能化入口需要逐个编辑，工具会自动处理。

---

## 贡献

欢迎提交 Issue 和 PR。

## License

MIT
