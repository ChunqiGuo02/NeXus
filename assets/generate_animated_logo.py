#!/usr/bin/env python3
"""
生成极简扁平方块风格的Logo（静态 PNG + 动态 GIF）.

核心特征：
- 圆润的橙色身体
- 标志性的向前突出的长管状鼻子 / 嘴巴
- 两只大大的白色圆眼（黑色瞳孔）
- 两只短小的脚
- 没有手臂
"""

from PIL import Image, ImageDraw
import os

# ── 配色 ──────────────────────────────────────────────────────────
BODY       = (215, 120, 50)     # 橙色
BODY_DARK  = (180, 95, 35)      # 深橙（脚、鼻子底部）
NOSE       = (200, 108, 42)     # 鼻子色
EYE_WHITE  = (255, 255, 255)    # 眼白
PUPIL      = (20, 20, 20)       # 瞳孔
MOUTH      = (30, 30, 30)       # 嘴巴开口
OUTLINE    = (185, 95, 35)      # 比身体略深的橙色（像素描边）
BG         = (0, 0, 0, 0)       # 透明背景

# ── 网格参数 ──────────────────────────────────────────────────────
PX = 24       # 每个像素块大小
GW = 16       # 网格宽
GH = 18       # 网格高


def _fill(draw, blocks, color):
    for gx, gy in blocks:
        x0, y0 = gx * PX, gy * PX
        draw.rectangle([x0, y0, x0 + PX - 1, y0 + PX - 1], fill=color)


def _get_outline_blocks(blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """计算围绕填充块的一圈外部像素块坐标（仅上下左右 4 方向）。"""
    block_set = set(blocks)
    outline = set()
    for gx, gy in blocks:
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nb = (gx + dx, gy + dy)
            if nb not in block_set:
                outline.add(nb)
    return list(outline)


def draw_qbert(oy: int = 0, blink: bool = False, squash: bool = False,
               mouth_open: bool = False, nose_dy: int = 0) -> Image.Image:
    """
    在像素网格上绘制 Logo。

    nose_dy: 鼻子整体微小垂直偏移（-1=上移一格，+1=下移一格），
             保持朝右下的形状不变，只做位移。
    """
    img = Image.new("RGBA", (GW * PX, GH * PX), BG)
    draw = ImageDraw.Draw(img)

    o = oy

    if squash:
        # 压扁帧
        body = []
        body += [(x, 2+o) for x in range(5, 10)]
        for y in range(3, 8):
            body += [(x, y+o) for x in range(3, 12)]
        body += [(x, 8+o) for x in range(4, 11)]

        # 鼻子（压扁时缩短一阶）
        nose = [(11, 5+o), (12, 5+o),
                (12, 6+o), (13, 6+o)]

        eye_w = [(5, 3+o), (5, 4+o), (6, 3+o), (6, 4+o),
                 (8, 3+o), (8, 4+o), (9, 3+o), (9, 4+o)]
        pupils = [(6, 4+o), (9, 4+o)]
        mouth = [(13, 6+o)] if mouth_open else []

        feet = [(4, 10+o), (5, 10+o), (5, 11+o),
                (7, 10+o), (8, 10+o), (9, 10+o)]
        blink_line = [(5, 4+o), (6, 4+o), (8, 4+o), (9, 4+o)]
    else:
        # 正常帧
        body = []
        body += [(x, 1+o) for x in range(5, 10)]
        body += [(x, 2+o) for x in range(4, 11)]
        for y in range(3, 9):
            body += [(x, y+o) for x in range(3, 12)]
        body += [(x, 9+o) for x in range(5, 10)]

        # 鼻子（始终朝右下 ~45°，nose_dy 做微小上下偏移）
        nd = nose_dy
        if mouth_open:
            # 张嘴：鼻子末端水平伸出一格
            nose = [(11, 6+o+nd), (12, 6+o+nd),
                    (12, 7+o+nd), (13, 7+o+nd),
                    (13, 8+o+nd), (14, 8+o+nd), (15, 8+o+nd)]
            mouth = [(15, 8+o+nd)]
        else:
            # 正常鼻子
            nose = [(11, 6+o+nd), (12, 6+o+nd),
                    (12, 7+o+nd), (13, 7+o+nd),
                    (13, 8+o+nd), (14, 8+o+nd)]
            mouth = []

        eye_w = [(5, 4+o), (5, 5+o), (6, 4+o), (6, 5+o),
                 (8, 4+o), (8, 5+o), (9, 4+o), (9, 5+o)]
        pupils = [(6, 5+o), (9, 5+o)]

        feet = [(5, 10+o), (5, 11+o), (6, 11+o),
                (8, 10+o), (8, 11+o), (9, 11+o)]
        blink_line = [(5, 5+o), (6, 5+o), (8, 5+o), (9, 5+o)]

    # 描边
    body_outline = _get_outline_blocks(body + nose)
    feet_outline = _get_outline_blocks(feet)

    # 绘制：描边 → 填充 → 细节
    _fill(draw, body_outline, OUTLINE)
    _fill(draw, feet_outline, OUTLINE)
    _fill(draw, body, BODY)
    _fill(draw, nose, BODY)
    _fill(draw, feet, BODY)

    if blink:
        _fill(draw, blink_line, BODY_DARK)
    else:
        _fill(draw, eye_w, EYE_WHITE)
        _fill(draw, pupils, PUPIL)

    if mouth:
        _fill(draw, mouth, MOUTH)

    return img


def generate_static(output_path: str):
    img = draw_qbert()
    img.save(output_path, "PNG")
    print(f"[OK] 静态 Logo → {output_path}")


def generate_gif(output_path: str):
    """
    动画序列：
    站立 → 蓄力 → 跳起(鼻子微上移) → 滞空(张嘴+鼻子伸长) →
    下落(鼻子微下移) → 落地压扁(鼻子缩短) → 恢复 → 眨眼 → 循环
    """
    frames = []
    durations = []

    def add(oy=0, blink=False, squash=False, mouth=False, nose_dy=0, dur=200):
        frames.append(draw_qbert(oy, blink, squash, mouth, nose_dy))
        durations.append(dur)

    # 站立
    add(dur=400)
    add(dur=300)

    # 蓄力（微蹲）
    add(oy=1, dur=80)

    # 跳起（鼻子随惯性微微下垂 1 格）
    add(oy=-1, nose_dy=1, dur=70)
    add(oy=-2, nose_dy=1, dur=80)

    # 滞空（张嘴 + 鼻子伸长）
    add(oy=-3, mouth=True, dur=180)

    # 下落（鼻子因惯性微微上移 1 格）
    add(oy=-2, nose_dy=-1, dur=70)
    add(oy=-1, nose_dy=-1, dur=70)

    # 落地
    add(oy=0, dur=50)

    # 压扁（鼻子自动缩短）
    add(squash=True, dur=120)

    # 恢复
    add(dur=200)

    # 眨眼
    add(blink=True, dur=100)
    add(dur=500)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
    )
    print(f"[OK] 动态 Logo → {output_path}")


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    generate_static(os.path.join(out_dir, "logo.png"))
    generate_gif(os.path.join(out_dir, "logo.gif"))
    print("\n✅ Done!")
