# linuxdo-cli

[LINUX DO](https://linux.do) 社区的命令行 TUI 工具，支持终端内浏览话题、查看帖子详情。

主文档以仓库根目录的 `README.md` 为准。
这里仅保留包内实现的最小结构说明，避免与主 README 长期漂移。

## 安装

```bash
pip install -e .
```

## 使用

```bash
# 启动 TUI 浏览器（默认行为）
linuxdo

# 登录
linuxdo login

# 查看当前登录用户信息
linuxdo me
```

## TUI 快捷键

### 全局

| 键 | 说明 |
|---|---|
| `?` | 打开 / 关闭帮助 |

### 话题列表

| 键 | 说明 |
|---|---|
| `Tab` / `Shift+Tab` | 切换分类（最新 / 热门） |
| `j` / `↓` | 光标下移 |
| `k` / `↑` | 光标上移 |
| `g` / `Home` | 跳到顶部 |
| `G` / `End` | 跳到底部 |
| `Enter` | 进入话题详情 |
| `o` | 在浏览器中打开当前话题 |
| `n` | 立即加载下一页 |
| `r` | 刷新 |
| `Ctrl+Q` | 退出 |

列表接近底部时会自动追加下一页话题，实现无限滚动。

### 话题详情

| 键 | 说明 |
|---|---|
| `Esc` / `q` | 返回列表 |
| `j` / `↓` | 向下滚动 |
| `k` / `↑` | 向上滚动 |
| `PageDown` / `PageUp` | 翻页滚动 |
| `g` / `Home` | 滚动到顶部 |
| `G` / `End` | 滚动到底部 |

话题详情页在接近底部或滚动到底部时，也会自动追加更多回复。

## 配置

配置文件位于 `~/.config/linuxdo-cli/config.json`，也可通过环境变量覆盖（前缀 `LINUXDO_`）：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `LINUXDO_BASE_URL` | 论坛地址 | `https://linux.do` |
| `LINUXDO_ACCESS_TOKEN` | 访问令牌（登录后自动写入） | — |

## 项目结构

```
src/linuxdo_cli/
├── main.py          # CLI 入口（Typer）
├── client.py        # 论坛 API 客户端（curl_cffi）
├── connect_client.py # Connect OAuth / 用户 API 客户端（httpx）
├── services/        # 应用服务（auth / topics / detail）
├── settings.py      # 配置 schema 与内置凭据合并
├── config_repository.py # 配置持久化
├── config.py        # 稳定导出入口
├── models.py        # Pydantic 数据模型
├── auth.py          # CLI 登录壳，实际流程在 AuthService
├── utils/
│   └── converter.py # HTML → Markdown 转换
└── tui/
    ├── app.py       # Textual App 根
    ├── state.py     # 浏览状态
    ├── screens/     # browse / detail / help
    └── widgets/     # CategoryTabs / TopicList / PostView / StatusBar
```

## 架构约定

- `client.py` 只负责论坛话题 / 分类 / 详情 API
- `connect_client.py` 只负责 Connect OAuth 与用户信息 API
- `services/auth.py` 负责编排登录流程，`auth.py` 只保留 CLI 壳
- `tui/screens/*` 只负责交互编排与状态推进，不直接访问底层 transport 私有细节
- `tui/widgets/*` 只负责渲染，不发起网络请求

## 依赖

- [Textual](https://github.com/Textualize/textual) — TUI 框架
- [curl-cffi](https://github.com/lexiforest/curl_cffi) — 伪装 Chrome 的 HTTP 客户端
- [Typer](https://typer.tiangolo.com/) — CLI 框架
- [Pydantic](https://docs.pydantic.dev/) — 数据校验
- [markdownify](https://github.com/matthewwithanm/python-markdownify) — HTML 转 Markdown
