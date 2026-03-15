#!/usr/bin/env python3
"""
生成 NeXus README 动画头部 SVG（v8 - 平衡居中版）。
紧凑布局 + 物理同步跳跃 + 合理的元素比例。
"""

import base64
import os


def parabolic_hop(x0, y0, x1, y1, hop_height, n_samples=10):
    points = []
    for i in range(1, n_samples):
        t = i / n_samples
        x = x0 + (x1 - x0) * t
        y_linear = y0 + (y1 - y0) * t
        y_arc = -4 * hop_height * t * (1 - t)
        y = y_linear + y_arc
        points.append((x, y))
    return points


def generate_header_svg():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gif_path = os.path.join(script_dir, "nexus_logo.gif")
    with open(gif_path, "rb") as f:
        gif_b64 = base64.b64encode(f.read()).decode("ascii")

    # ── 画布和 Q*bert 尺寸 ──
    W = 800
    H = 120
    gif_w = 56
    gif_h = 68

    # ── 标题与跳跃参数 ──
    title_y = 88

    # 浏览器实测 getBBox() 值：
    # NeXus: top=48, bottom=97   (x: 175~310)
    # 副标题: top=69, bottom=93  (x: 326~626)
    nexus_top = 78   # Q*bert 脚底对齐 NeXus (48+25)
    sub_top = 86     # Q*bert 脚底对齐副标题 (69+25)
    nexus_right_edge = 215  # NeXus+冒号 的右边界

    bottom_y = 150
    hop_h = 28
    big_hop_h = 20

    # 水平范围
    right_x = 580
    left_x = 140
    bottom_x = 150
    n_hops = 10
    hop_w = (right_x - left_x) / n_hops




    def landing_y(x):
        """根据 x 位置返回落脚 y：踩在当前位置文字的顶部"""
        if x < nexus_right_edge:
            return nexus_top  # 踩在 NeXus 大字上
        else:
            return sub_top    # 踩在副标题小字上

    # ── GIF 同步时间 ──
    T_CYCLE = 2.22
    T_AIR_START = 0.78
    T_AIR_END = 1.25
    AIR_DUR = T_AIR_END - T_AIR_START

    samples_per_hop = 10
    big_samples = 14

    # ── 跳跃路径数据 ──
    hops_data = []

    # Phase 1: 右→左
    for i in range(n_hops):
        x0 = right_x - i * hop_w
        x1 = right_x - (i + 1) * hop_w
        y0 = landing_y(x0)
        y1 = landing_y(x1)
        hops_data.append((x0, y0, x1, y1, False))

    # Phase 2: 跳下去
    hops_data.append((left_x, landing_y(left_x), bottom_x, bottom_y, True))

    # Phase 3: 跳回来
    hops_data.append((bottom_x, bottom_y, left_x, landing_y(left_x), True))

    # Phase 4: 左→右
    for i in range(n_hops):
        x0 = left_x + i * hop_w
        x1 = left_x + (i + 1) * hop_w
        y0 = landing_y(x0)
        y1 = landing_y(x1)
        hops_data.append((x0, y0, x1, y1, False))

    total_hops = len(hops_data)
    total_time = total_hops * T_CYCLE

    # ── 生成所有关键帧 ──
    all_points = []
    all_keytimes = []

    for hop_i, (x0, y0, x1, y1, is_big) in enumerate(hops_data):
        h = big_hop_h if is_big else hop_h
        ns = big_samples if is_big else samples_per_hop

        t_base = hop_i * T_CYCLE
        t_start_air = t_base + T_AIR_START
        t_end_air = t_base + T_AIR_END

        if hop_i == 0:
            all_points.append((x0, y0))
            all_keytimes.append(0.0)

        # 待命结束
        all_points.append((x0, y0))
        all_keytimes.append(t_start_air / total_time)

        # 飞行采样
        air_pts = parabolic_hop(x0, y0, x1, y1, h, ns)
        for j, (px, py) in enumerate(air_pts):
            frac = (j + 1) / ns
            kt = (t_start_air + frac * AIR_DUR) / total_time
            all_points.append((px, py))
            all_keytimes.append(kt)

        # 落地
        all_points.append((x1, y1))
        all_keytimes.append(t_end_air / total_time)

        # 最后一跳结束时间
        if hop_i == total_hops - 1:
            all_points.append((x1, y1))
            all_keytimes.append(1.0)

    values_str = ";".join(f"{x:.1f},{y:.1f}" for x, y in all_points)
    kt_str = ";".join(f"{t:.5f}" for t in all_keytimes)
    dur = f"{total_time:.2f}s"

    # 方向翻转：Phase 1 + Phase 2 完成后
    flip_t = ((n_hops + 1) * T_CYCLE) / total_time

    gy = -gif_h
    gx = gif_w / 2

    # ── 标题文字居中坐标 ──
    text_x = W / 2

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}"
     role="img" aria-label="NeXus : the Next-gen Unified Sub-researcher">

  <!-- 标题 -->
  <text x="{text_x}" y="{title_y}" text-anchor="middle">
    <tspan font-family="Cambria, Georgia, serif" font-weight="700" font-size="42" fill="#1a1a2e" letter-spacing="3">NeXus</tspan>
    <tspan font-family="Cambria, Georgia, serif" font-weight="400" font-size="26" fill="#aaa"> : </tspan>
    <tspan font-family="Cambria, Georgia, serif" font-style="italic" font-weight="500" font-size="30" fill="#555">the Next-gen Unified Sub-researcher</tspan>
  </text>

  <!-- Q*bert 面朝左 -->
  <g>
    <animate attributeName="opacity"
      values="1;1;0;0;0"
      keyTimes="0;{flip_t - 0.001:.5f};{flip_t:.5f};{flip_t + 0.001:.5f};1"
      dur="{dur}" repeatCount="indefinite" />
    <animateMotion
      values="{values_str}"
      keyTimes="{kt_str}"
      calcMode="linear"
      dur="{dur}" repeatCount="indefinite" />
    <g transform="translate({gx:.0f}, {gy}) scale(-1, 1)">
      <image href="data:image/gif;base64,{gif_b64}"
        width="{gif_w}" height="{gif_h}" />
    </g>
  </g>

  <!-- Q*bert 面朝右 -->
  <g>
    <animate attributeName="opacity"
      values="0;0;1;1;1"
      keyTimes="0;{flip_t - 0.001:.5f};{flip_t:.5f};{flip_t + 0.001:.5f};1"
      dur="{dur}" repeatCount="indefinite" />
    <animateMotion
      values="{values_str}"
      keyTimes="{kt_str}"
      calcMode="linear"
      dur="{dur}" repeatCount="indefinite" />
    <g transform="translate({-gx:.0f}, {gy})">
      <image href="data:image/gif;base64,{gif_b64}"
        width="{gif_w}" height="{gif_h}" />
    </g>
  </g>

</svg>
'''
    return svg


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(out_dir, "nexus_header.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(generate_header_svg())
    print(f"[OK] 动画头部 SVG (平衡居中版) → {svg_path}")


if __name__ == "__main__":
    main()
