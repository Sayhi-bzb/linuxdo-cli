# linuxdo-cli

![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

[LINUX DO](https://linux.do) 社区的命令行 TUI 工具，在终端内浏览话题、查看帖子详情。

## 安装

```bash

# 从 PyPI 安装
pip install linuxdo-cli

# 从源码安装（开发模式）
pip install -e .


```

## 使用

```bash
linuxdo          # 启动 TUI 浏览器
linuxdo login    # 登录
linuxdo me       # 查看当前登录用户
linuxdo --version
```

## 快捷键

### 全局

| 键       | 说明                |
| -------- | ------------------- |
| `?`      | 打开 / 关闭帮助     |
| `t`      | 切换主题            |
| `d`      | 切换紧凑 / 标准布局 |
| `Ctrl+Q` | 退出                |

### 话题列表

| 键                  | 说明                           |
| ------------------- | ------------------------------ |
| `Tab` / `Shift+Tab` | 切换分类（最新 / 热门 / 分类） |
| `j` / `↓`           | 光标下移                       |
| `k` / `↑`           | 光标上移                       |
| `g` / `Home`        | 跳到顶部                       |
| `G` / `End`         | 跳到底部                       |
| `Enter`             | 进入话题详情                   |
| `o`                 | 在浏览器中打开当前话题         |
| `n`                 | 立即加载下一页                 |
| `r`                 | 刷新                           |

列表接近底部时自动追加下一页（无限滚动）。

### 话题详情

| 键                    | 说明       |
| --------------------- | ---------- |
| `Esc`                 | 返回列表   |
| `j` / `↓`             | 向下滚动   |
| `k` / `↑`             | 向上滚动   |
| `PageDown` / `PageUp` | 翻页       |
| `g` / `Home`          | 滚动到顶部 |
| `G` / `End`           | 滚动到底部 |

## 凭据配置

程序通过内置 `_credentials.py` 读取 OAuth 凭据（此文件不纳入版本控制）。
也可通过环境变量覆盖：

```bash
export LINUXDO_CLIENT_ID=your-client-id
export LINUXDO_CLIENT_SECRET=your-client-secret
```

如需自行部署，复制 `src/linuxdo_cli/_credentials.py.example` 为 `_credentials.py` 并填入真实值。

## 配置

配置文件：`~/.config/linuxdo-cli/config.json`，支持环境变量覆盖（前缀 `LINUXDO_`）。

| 变量                    | 说明                                |
| ----------------------- | ----------------------------------- |
| `LINUXDO_CLIENT_ID`     | OAuth Client ID                     |
| `LINUXDO_CLIENT_SECRET` | OAuth Client Secret                 |
| `LINUXDO_BASE_URL`      | 论坛地址（默认 `https://linux.do`） |
| `LINUXDO_ACCESS_TOKEN`  | 访问令牌（登录后自动写入）          |

## 依赖

- [Textual](https://github.com/Textualize/textual) — TUI 框架
- [curl-cffi](https://github.com/lexiforest/curl_cffi) — 伪装 Chrome 的 HTTP 客户端
- [Typer](https://typer.tiangolo.com/) — CLI 框架
- [Pydantic](https://docs.pydantic.dev/) — 数据校验
- [markdownify](https://github.com/matthewwithanm/python-markdownify) — HTML 转 Markdown

## License

MIT
