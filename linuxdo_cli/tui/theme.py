from textual.theme import Theme

# --- DARK THEMES ---

# LINUX DO Theme (Original)
LINUX_DO_THEME = Theme(
    name="linuxdo",
    primary="#0088cc",
    secondary="#ffba00",
    accent="#e45735",
    background="#0a0a0a",    # 更深的背景
    surface="#161616",       # 稍微浅一点的表面
    boost="#262626",         # 明显的悬停/边框色
    foreground="#e9e9e9",
    success="#2ecc71",
    error="#e74c3c",
    warning="#f1c40f",
)

# GitHub Dark Theme
GITHUB_DARK_THEME = Theme(
    name="github-dark",
    primary="#58a6ff",
    secondary="#f0883e",
    accent="#bc8cff",
    background="#010409",
    surface="#0d1117",
    boost="#21262d",
    foreground="#c9d1d9",
    success="#3fb950",
    error="#f85149",
    warning="#d29922",
)

# VSCode Dark Theme
VSCODE_DARK_THEME = Theme(
    name="vscode-dark",
    primary="#007acc",
    secondary="#ce9178",
    accent="#4ec9b0",
    background="#181818",
    surface="#252526",
    boost="#37373d",
    foreground="#cccccc",
    success="#6a9955",
    error="#f44747",
    warning="#cca700",
)

# Nord Theme
NORD_THEME = Theme(
    name="nord",
    primary="#88c0d0",
    secondary="#ebcb8b",
    accent="#a3be8c",
    background="#242933",
    surface="#2e3440",
    boost="#3b4252",
    foreground="#eceff4",
    success="#a3be8c",
    error="#bf616a",
    warning="#ebcb8b",
)

# --- LIGHT THEMES ---

# GitHub Light Theme
GITHUB_LIGHT_THEME = Theme(
    name="github-light",
    primary="#0969da",
    secondary="#9a6700",
    accent="#8250df",
    background="#ffffff",
    surface="#f6f8fa",
    boost="#ebeff2",         # 浅色模式下 boost 应该比 surface 更深
    foreground="#24292f",
    success="#1a7f37",
    error="#cf222e",
    warning="#9a6700",
)

# Catppuccin Latte
CATPPUCCIN_LATTE = Theme(
    name="catppuccin-latte",
    primary="#1e66f5",
    secondary="#ea76cb",
    accent="#fe640b",
    background="#dce0e8",    # 背景稍深
    surface="#eff1f5",       # 表面亮起
    boost="#ccd0da",         # 辅助色深一些
    foreground="#4c4f69",
    success="#40a02b",
    error="#d20f39",
    warning="#df8e1d",
)

# Solarized Light
SOLARIZED_LIGHT = Theme(
    name="solarized-light",
    primary="#268bd2",
    secondary="#b58900",
    accent="#cb4b16",
    background="#fdf6e3",
    surface="#eee8d5",
    boost="#e3dbbc",
    foreground="#586e75",
    success="#859900",
    error="#dc322f",
    warning="#b58900",
)

THEMES = [
    LINUX_DO_THEME, 
    GITHUB_DARK_THEME, 
    VSCODE_DARK_THEME, 
    NORD_THEME,
    GITHUB_LIGHT_THEME,
    CATPPUCCIN_LATTE,
    SOLARIZED_LIGHT
]
