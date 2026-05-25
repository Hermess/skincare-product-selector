# 安装与依赖

这个 Skill 可以只用 Markdown 说明运行，也可以配合工具脚本抓取公开页面、做来源裁决和 NMPA 备案编号路由。

## 1. 一键安装

最快方式：

```bash
npx -y github:Hermess/skincare-product-selector install
```

连 Python 依赖一起装：

```bash
npx -y github:Hermess/skincare-product-selector install --with-python
```

安装到自定义目录：

```bash
npx -y github:Hermess/skincare-product-selector install --target ~/.agents/skills/skincare-product-selector
```

## 2. 手动安装 Python 依赖

在技能目录执行：

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

检查：

```bash
python3 tools/check_dependencies.py
```

## 3. 建议启用的 Codex 插件

安装或启用 Skill 时，建议提示用户同时启用这些插件：

| 插件 | 必需性 | 用途 |
| --- | --- | --- |
| Browser | 推荐 | 检查本地 HTML、README 预览、普通网页渲染 |
| Chrome | 推荐 | 读取用户已登录或已完成普通验证的可见页面 |
| Computer Use | 推荐 | 手动导航 NMPA 政务服务门户等动态官方页面 |
| Spreadsheets | 可选 | 把多产品对比导出成表格 |
| Documents | 可选 | 把最终选品报告打包成文档 |

## 4. 推荐提示文案

安装时可以直接提示：

```text
建议同时启用 Browser、Chrome、Computer Use。
其中 Chrome/Computer Use 用于 NMPA 或登录后可见页面的人工验证；Browser 用于渲染检查。
```

## 5. 降级策略

- 没有 Chrome/Computer Use：遇到 NMPA 或登录后页面时，请用户提供截图。
- 没有 Browser/Playwright：只使用静态公开页面，不声称已验证动态内容。
- 没有 Spreadsheets/Documents：仍可输出 Markdown 对比结论。
