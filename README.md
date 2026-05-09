<div align="center">

# 🛠️ 京准通批量工具

**批量换图 + 批量设置预算，京准通日常运营自动化**

*换图三入口全覆盖 · 日预算按日期批量设定 · Excel 驱动一键执行*

[![Build Windows EXE](https://github.com/Friday-Up/batch-image-replace/actions/workflows/build-windows.yml/badge.svg)](https://github.com/Friday-Up/batch-image-replace/actions/workflows/build-windows.yml)
[![Release](https://img.shields.io/github/v/release/Friday-Up/batch-image-replace?color=blue&logo=github)](https://github.com/Friday-Up/batch-image-replace/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33?logo=playwright&logoColor=white)](https://playwright.dev/python/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-lightgrey.svg)](#-快速开始)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Friday-Up/batch-image-replace/pulls)
[![GitHub Stars](https://img.shields.io/github/stars/Friday-Up/batch-image-replace?style=social)](https://github.com/Friday-Up/batch-image-replace)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [注意事项](#%EF%B8%8F-注意事项) • [常见问题](#-常见问题) • [技术栈](#-技术栈)

</div>

---

## 📖 简介

每次到了换图季，几百个 SKU、三个入口（关键词 / 人群 / 智能化）、上千张图片，手动换图既枯燥又容易出错。每到月初调预算，几十个计划、每天不同的金额，手动逐个设置更是重复劳动。

**京准通批量工具**通过浏览器自动化 + Excel 驱动，把这些事压缩成"配置 → 一键执行"的两步操作。

> 把"加班三小时"变成"喝杯咖啡的功夫"。

---

## ✨ 功能特性

| 特性 | 说明 |
| --- | --- |
| 🎯 **三入口全覆盖** | 关键词、人群、智能化，可单独勾选或全选执行 |
| 💰 **批量设置预算** | 按日期批量设定日预算，支持数值和"不限" |
| 📊 **Excel 驱动** | 读取配置、执行结果自动写回备注列 |
| 🔍 **智能匹配图片** | 按 `SKU-序号.扩展名` 命名规则自动匹配本地图片 |
| 📅 **多种日期格式** | `2026/5/9`、`2026-05-09`、`5月9日`、`5/9` 均可识别 |
| 🖥️ **可视化操作** | 内置 GUI，Tab 切换换图/预算，无需命令行 |
| 🔐 **登录态持久化** | 浏览器登录信息自动保存，下次免登 |
| 🛑 **支持中途停止** | 一键停止执行，已处理的结果不丢失 |
| 📋 **日志可复制** | 日志区支持选词复制 + 一键复制全部日志 |
| 📦 **Windows 一键打包** | GitHub Actions 自动构建 EXE，开箱即用 |

---

## 🚀 快速开始

### 🪟 Windows 用户（推荐）

1. 从 [Releases](https://github.com/Friday-Up/batch-image-replace/releases) 下载最新版本 `京准通批量换图-Windows.zip`
2. 解压到任意文件夹（建议路径不含中文）
3. 双击 `JD-BatchImageReplace.exe` 启动
4. 首次启动约 10 秒，请耐心等待

> 💡 **提示**：如果 Windows 提示"未知发布者"，请点击「更多信息」→「仍要运行」。

### 🍎 macOS / 开发者

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# GUI 模式
python3 main.py

# CLI 模式
python3 main.py \
  --excel data.xlsx \
  --sku-col SKU \
  --image-dir /path/to/images \
  --scenarios keyword,crowd,smart
```

---

## 📚 使用指南

### 功能一：批量换图

#### 1️⃣ 准备数据

**📄 Excel 文件**

至少包含一列 SKU（默认列名 `SKU`），其他备注列工具会自动写入：

| SKU | 关键词备注 | 人群备注 | 智能化备注 |
|-----|-----------|---------|-----------|
| 100332393690 | | | |
| 100311842764 | | | |

**📁 图片文件夹**

按 `SKU-序号.扩展名` 命名，工具会自动匹配：

```text
images/
├── 100332393690-1.jpg
├── 100332393690-2.png
├── 100311842764-1.jpg
└── 100311842764-2.jpg
```

#### 2️⃣ 执行流程

| 步骤 | 操作 |
| --- | --- |
| 1 | 点击「选择文件」加载 Excel |
| 2 | 确认 SKU 列名（默认 `SKU`） |
| 3 | 点击「选择文件夹」加载图片目录 |
| 4 | 勾选需要执行的入口（关键词 / 人群 / 智能化） |
| 5 | 点击「开始执行」 |
| 6 | **首次运行**：弹出 Chromium 浏览器，**手动登录京准通** |
| 7 | 登录成功后，回到工具窗口点击「登录完成，继续执行」 |
| 8 | 等待执行完成，查看 Excel「备注」列结果 |

#### 3️⃣ 结果说明

| 备注内容 | 含义 |
|---------|------|
| ✅ `换图成功` | 该 SKU 对应入口已替换完成 |
| ⚠️ `未找到匹配图片` | 图片文件夹中无对应 SKU 的图片 |
| ❌ `失败: xxx` | 操作失败原因，详见错误信息 |

---

### 功能二：批量设置预算

#### 1️⃣ 准备数据

**📄 Excel 文件**（参考 [`templates/预算模板.xlsx`](./templates/预算模板.xlsx)）

- **第一列**：计划名称（用于搜索定位计划）
- **后续列**：列名为日期，单元格为该日的预算值

| 计划名称 | 2026/5/9 | 2026/5/10 | 2026/5/11 | 2026/5/12 |
|---------|----------|-----------|-----------|-----------|
| 智能化-爆款产品集合计划 | 3160 | 3900 | 不限 | 4000 |
| 低预算集合 | 2000 | 2800 | 1800 | |

**预算值填写规则：**

| 值 | 含义 |
|----|------|
| 数字（如 `3000`） | 设置为该金额 |
| `不限` | 设为不限预算 |
| 留空 | 跳过该日期，不修改 |

**支持的日期格式（列名）：**

| 格式 | 示例 |
|------|------|
| 斜杠/短横线完整日期 | `2026/5/9`、`2026-05-10` |
| 中文格式 | `5月9日`、`5月9` |
| 无年份简写 | `5/9`、`05-09`（自动补当前年） |
| Excel 日期单元格 | 单元格格式设为"日期"即可 |

#### 2️⃣ 执行流程

| 步骤 | 操作 |
| --- | --- |
| 1 | 切换到「批量设置预算」Tab |
| 2 | 点击「选择文件」加载预算 Excel |
| 3 | 点击「开始执行」 |
| 4 | **首次运行**：弹出浏览器，**手动登录京准通** |
| 5 | 登录成功后，回到工具窗口点击「登录完成，继续执行」 |
| 6 | 等待执行完成，查看 Excel「备注」列结果 |

#### 3️⃣ 结果说明

| 备注内容 | 含义 |
|---------|------|
| ✅ `设置成功` | 该计划所有日期预算已设置 |
| ❌ `失败: xxx` | 操作失败原因，详见错误信息 |

---

## ⚠️ 注意事项

### 📐 图片规格要求

| 类型 | 尺寸 | 格式 | 大小 |
| --- | --- | --- | --- |
| **竖图** | 350 × 520 | PNG / JPG | 1 - 500 KB |
| **方图** | 350 - 1500 px (1:1) | PNG / JPG | 1 - 3072 KB |

### 🚫 执行期间

- **请勿手动操作浏览器**，会打断自动化流程
- **登录态自动保存**，下次启动无需重新登录
- **杀毒软件误报**：如遇到误报，请将程序加入信任列表

---

## ❓ 常见问题

<details>
<summary><b>Q1：为什么首次启动比较慢？</b></summary>

首次启动需要初始化 Playwright 浏览器环境，约 10 秒，后续启动正常。
</details>

<details>
<summary><b>Q2：可以批量处理多少个 SKU？</b></summary>

理论上无上限，建议**单次不超过 500 个**，避免京准通页面超时。如果数据量更大，建议分批执行。
</details>

<details>
<summary><b>Q3：支持哪些图片格式？</b></summary>

PNG、JPG、JPEG。建议按京准通要求的尺寸和大小准备。
</details>

<details>
<summary><b>Q4：智能化入口和关键词/人群有什么区别？</b></summary>

- **关键词 / 人群**：可批量修改同一 SKU 下的所有创意，效率较高
- **智能化**：需要逐个编辑，工具会自动处理翻页和多行场景
</details>

<details>
<summary><b>Q5：执行中途能停止吗？已处理的结果会丢失吗？</b></summary>

可以。点击「停止执行」按钮即可中断，**已处理的 SKU 结果会保留在 Excel 中**，下次可继续从未处理的 SKU 开始。
</details>

<details>
<summary><b>Q6：登录态保存在哪？怎么清除？</b></summary>

登录态保存在程序目录下的 `.browser_data/` 中。如需重新登录，删除该目录即可。
</details>

<details>
<summary><b>Q7：预算 Excel 的日期列名怎么写？</b></summary>

支持多种格式：`2026/5/9`、`2026-05-09`、`5月9日`、`5/9` 等。无年份的格式会自动补当前年份。也可以直接把单元格格式设为"日期"类型，程序会自动识别。
</details>

<details>
<summary><b>Q8：CLI 模式怎么只跑指定入口？</b></summary>

通过 `--scenarios` 参数指定，逗号分隔：
```bash
python3 main.py --excel data.xlsx --image-dir ./images --scenarios keyword,smart
```
可选值：`keyword` / `crowd` / `smart`。
</details>

---

## 🛠️ 技术栈

| 组件 | 用途 |
| --- | --- |
| 🐍 [Python 3.11](https://www.python.org/) | 运行环境 |
| 🎭 [Playwright](https://playwright.dev/python/) | 浏览器自动化 |
| 🪟 [pywebview](https://pywebview.flowrl.com/) | 桌面 GUI |
| 📊 [pandas](https://pandas.pydata.org/) / [openpyxl](https://openpyxl.readthedocs.io/) | Excel 处理 |
| 📅 [python-dateutil](https://dateutil.readthedocs.io/) | 多格式日期解析 |
| 📦 [PyInstaller](https://pyinstaller.org/) | 打包分发 |
| 🤖 [GitHub Actions](https://docs.github.com/actions) | CI 自动构建 Windows EXE |

---

## 🗂️ 项目结构

```text
batch-image-replace/
├── main.py                # CLI / GUI 入口
├── src/                   # 核心逻辑
│   ├── core.py            # 批量换图调度
│   ├── budget.py          # 批量设置预算
│   ├── gui.py             # GUI 实现
│   └── config.py          # 全局配置
├── templates/             # Excel 模板
│   └── 预算模板.xlsx       # 批量设置预算模板
├── scripts/               # 启动脚本（macOS .command）
├── docs/                  # 内部文档
├── .github/workflows/     # GitHub Actions 配置
├── requirements.txt       # Python 依赖
├── LICENSE                # MIT 协议
└── README.md              # 本文件
```

---

## 🤝 贡献

欢迎任何形式的贡献！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交变更：`git commit -m 'feat: add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

提交信息请遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

---

## 📜 License

本项目基于 [MIT License](./LICENSE) 开源协议发布。

---

## 🌟 致谢

- [Playwright](https://playwright.dev/) —— 现代浏览器自动化引擎
- [pywebview](https://pywebview.flowrl.com/) —— 极简 Python 桌面 GUI 方案
- 所有提交反馈和 PR 的小伙伴 ❤️

---

<div align="center">

由 [Friday Up](https://github.com/Friday-Up) 维护

**如果这个工具帮到了你，欢迎点一个 ⭐ Star 支持一下！**

</div>