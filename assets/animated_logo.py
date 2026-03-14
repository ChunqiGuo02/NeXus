#!/usr/bin/env python3
"""
Nexus 终端动态 Logo — 像素风 Q'bert 动画
在 agent 启动时播放，支持 Windows / macOS / Linux 终端。

用法:
    python assets/animated_logo.py          # 直接运行预览
    from assets.animated_logo import play   # 在代码中调用
"""

from __future__ import annotations

import os
import sys
import time
import random

# ── 颜色定义（ANSI 256‑color） ──────────────────────────────────────
# 使用 \033[38;5;Xm 前景色

RESET  = "\033[0m"
BOLD   = "\033[1m"

# Q'bert 身体
ORANGE     = "\033[38;5;208m"
DARK_ORANGE = "\033[38;5;166m"
# 眼睛 / 高光
WHITE      = "\033[38;5;255m"
BLACK      = "\033[38;5;16m"
# 方块颜色
RED        = "\033[38;5;196m"
BLUE       = "\033[38;5;27m"
YELLOW     = "\033[38;5;226m"
GOLD       = "\033[38;5;220m"
MAGENTA    = "\033[38;5;199m"
CYAN       = "\033[38;5;51m"
GREEN      = "\033[38;5;46m"
# 文字
DIM        = "\033[38;5;240m"
ACCENT     = "\033[38;5;75m"

# ── 像素块字符 ──────────────────────────────────────────────────────
FULL  = "██"
HALF  = "▄▄"
UPPER = "▀▀"
SPC   = "  "

# ── Q'bert 角色帧 (用颜色代号矩阵表示) ─────────────────────────────
# 0=空 1=orange 2=dark_orange 3=white 4=black 5=gold/nose
# 帧 1：正常站立
QBERT_FRAME_1 = [
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 3, 4, 1, 1, 0],
    [0, 1, 1, 1, 5, 5, 0],
    [0, 0, 1, 1, 0, 5, 0],
    [0, 0, 2, 2, 0, 0, 0],
    [0, 0, 4, 4, 0, 0, 0],
]

# 帧 2：跳跃（身体上移 + 脚收起）
QBERT_FRAME_2 = [
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 3, 4, 1, 1, 0],
    [0, 1, 1, 1, 5, 5, 0],
    [0, 0, 1, 1, 0, 5, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0],
]

# 帧 3：落地（身体压扁 + 冒汗）
QBERT_FRAME_3 = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 0],
    [0, 1, 3, 4, 1, 1, 0],
    [0, 1, 1, 1, 5, 5, 0],
    [0, 0, 2, 2, 0, 5, 0],
    [0, 4, 0, 0, 4, 0, 0],
]

QBERT_FRAMES = [QBERT_FRAME_1, QBERT_FRAME_2, QBERT_FRAME_1, QBERT_FRAME_3]

COLOR_MAP = {
    0: (RESET, SPC),
    1: (ORANGE, FULL),
    2: (DARK_ORANGE, FULL),
    3: (WHITE, FULL),
    4: (BLACK, FULL),
    5: (GOLD, FULL),
}

# ── 等距方块金字塔 ──────────────────────────────────────────────────
# 4 层金字塔，每个方块用 3 行 x 4 列字符表示

CUBE_COLORS_INITIAL = [
    [RED, BLUE, YELLOW, RED],
    [BLUE, YELLOW, RED, 0],
    [YELLOW, RED, 0, 0],
    [BLUE, 0, 0, 0],
]

CUBE_COLORS_LIT = [
    [CYAN, GREEN, MAGENTA, CYAN],
    [GREEN, MAGENTA, CYAN, 0],
    [MAGENTA, CYAN, 0, 0],
    [GREEN, 0, 0, 0],
]


def _render_qbert(frame_idx: int) -> list[str]:
    """将 Q'bert 帧渲染为带 ANSI 颜色的字符串行列表."""
    frame = QBERT_FRAMES[frame_idx % len(QBERT_FRAMES)]
    lines = []
    for row in frame:
        line = ""
        for cell in row:
            color, char = COLOR_MAP[cell]
            line += f"{color}{char}"
        line += RESET
        lines.append(line)
    return lines


def _render_cube_row(colors: list, row_idx: int, num_cubes: int) -> str:
    """渲染一行等距方块."""
    indent = "    " * (3 - row_idx)
    cubes = ""
    for i in range(num_cubes):
        c = colors[row_idx][i] if colors[row_idx][i] else ""
        if not c:
            continue
        cubes += f"{c}{FULL}{FULL}{RESET} "
    return indent + cubes


def _render_pyramid(colors: list) -> list[str]:
    """渲染整个金字塔."""
    lines = []
    for row_idx in range(4):
        num_cubes = 4 - row_idx
        # 方块顶部
        indent = "      " * row_idx
        top = indent
        mid = indent
        for i in range(num_cubes):
            c = colors[row_idx][i] if colors[row_idx][i] else ""
            if not c:
                continue
            top += f"{c}▗{FULL}▖{RESET}  "
            mid += f"{c}{FULL}{FULL}{RESET}  "
        lines.append(top)
        lines.append(mid)
    return lines


# ── 逐行出现动画 ───────────────────────────────────────────────────
def _clear_screen():
    """清屏."""
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _move_cursor(row: int, col: int = 0):
    """移动光标到指定位置."""
    sys.stdout.write(f"\033[{row};{col}H")
    sys.stdout.flush()


def _hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def _show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ── 主标题文字 ─────────────────────────────────────────────────────
TITLE_ART = [
    f"{ACCENT}{BOLD}  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗{RESET}",
    f"{ACCENT}{BOLD}  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝{RESET}",
    f"{ACCENT}{BOLD}  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗{RESET}",
    f"{ACCENT}{BOLD}  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║{RESET}",
    f"{ACCENT}{BOLD}  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║{RESET}",
    f"{ACCENT}{BOLD}  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝{RESET}",
]

SUBTITLE = f"{DIM}  The Autonomous AI Co-Scientist{RESET}"
TAGLINE  = f"{DIM}  Survey → Ideate → Experiment → Write → Review{RESET}"


def _sparkle_effect(lines: list[str], row_start: int, duration: float = 0.6):
    """方块颜色闪烁效果."""
    steps = int(duration / 0.08)
    colors_seq = [CUBE_COLORS_INITIAL, CUBE_COLORS_LIT]
    for step in range(steps):
        pyramid_lines = _render_pyramid(colors_seq[step % 2])
        for i, line in enumerate(pyramid_lines):
            _move_cursor(row_start + i, 1)
            sys.stdout.write(line + "    ")
        sys.stdout.flush()
        time.sleep(0.08)
    # 最终恢复原色
    pyramid_lines = _render_pyramid(CUBE_COLORS_INITIAL)
    for i, line in enumerate(pyramid_lines):
        _move_cursor(row_start + i, 1)
        sys.stdout.write(line + "    ")
    sys.stdout.flush()


def play(speed: float = 1.0):
    """
    播放 Nexus 动态 Logo。

    Parameters
    ----------
    speed : float
        动画速度倍率，1.0 为默认，越大越快。
    """
    delay = lambda s: time.sleep(s / speed)

    # 启用 Windows ANSI 支持
    if sys.platform == "win32":
        os.system("")  # 激活 VT100

    _hide_cursor()
    _clear_screen()

    try:
        row = 2

        # ── 阶段 1：Q'bert 跳入（逐行出现） ──
        qbert_lines = _render_qbert(0)
        qbert_start = row
        indent = "        "
        for i, line in enumerate(qbert_lines):
            _move_cursor(qbert_start + i, 1)
            sys.stdout.write(indent + line)
            sys.stdout.flush()
            delay(0.06)

        delay(0.15)

        # ── 阶段 2：金字塔逐层从底部堆叠 ──
        pyramid_start = qbert_start + len(qbert_lines)
        pyramid_lines = _render_pyramid(CUBE_COLORS_INITIAL)
        # 从底层开始向上显示
        for i in range(len(pyramid_lines) - 1, -1, -1):
            _move_cursor(pyramid_start + i, 1)
            sys.stdout.write(pyramid_lines[i])
            sys.stdout.flush()
            delay(0.05)

        delay(0.15)

        # ── 阶段 3：Q'bert 跳跃动画（2 个循环） ──
        for cycle in range(2):
            for frame_idx in range(len(QBERT_FRAMES)):
                qbert_lines = _render_qbert(frame_idx)
                # 跳跃帧上移 1 行
                offset = -1 if frame_idx == 1 else 0
                # 先清除区域
                for i in range(len(qbert_lines) + 1):
                    _move_cursor(qbert_start + i - 1, 1)
                    sys.stdout.write(" " * 40)
                # 绘制
                for i, line in enumerate(qbert_lines):
                    _move_cursor(qbert_start + i + offset, 1)
                    sys.stdout.write(indent + line)
                sys.stdout.flush()
                delay(0.1)

        # 恢复站立帧
        qbert_lines = _render_qbert(0)
        for i in range(len(qbert_lines) + 1):
            _move_cursor(qbert_start + i - 1, 1)
            sys.stdout.write(" " * 40)
        for i, line in enumerate(qbert_lines):
            _move_cursor(qbert_start + i, 1)
            sys.stdout.write(indent + line)
        sys.stdout.flush()

        delay(0.1)

        # ── 阶段 4：方块闪烁 ──
        _sparkle_effect(pyramid_lines, pyramid_start, duration=0.5)

        delay(0.2)

        # ── 阶段 5：标题文字打字机效果 ──
        title_start = pyramid_start + len(pyramid_lines) + 1
        for i, line in enumerate(TITLE_ART):
            _move_cursor(title_start + i, 1)
            sys.stdout.write(line)
            sys.stdout.flush()
            delay(0.04)

        delay(0.15)

        # ── 阶段 6：副标题淡入 ──
        sub_row = title_start + len(TITLE_ART) + 1
        _move_cursor(sub_row, 1)
        sys.stdout.write(SUBTITLE)
        sys.stdout.flush()
        delay(0.3)

        _move_cursor(sub_row + 1, 1)
        sys.stdout.write(TAGLINE)
        sys.stdout.flush()
        delay(0.2)

        # ── 分隔线 ──
        _move_cursor(sub_row + 3, 1)
        sep = f"{DIM}  {'─' * 48}{RESET}"
        sys.stdout.write(sep)
        sys.stdout.flush()

        # 将光标移到动画下方，留出空间给后续输出
        _move_cursor(sub_row + 5, 1)

    finally:
        _show_cursor()
        sys.stdout.write(RESET)
        sys.stdout.flush()


# ── CLI 入口 ───────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
        play(speed=speed)
    except KeyboardInterrupt:
        _show_cursor()
        sys.stdout.write(RESET + "\n")
