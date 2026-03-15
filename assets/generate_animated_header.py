#!/usr/bin/env python3
"""
生成 NeXus README 动画头部 SVG（v7 - 完美物理与定格同步版）。
完全同步 `nexus_logo.gif` 内部动画帧率循环（2.22s）：
- 0.00s ~ 0.78s: 原地待命（站立、蓄力）
- 0.78s ~ 1.25s: 飞行抛物线（共 0.47s 滞空）
- 1.25s ~ 2.22s: 落地缓冲（压扁、恢复、眨眼）
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

    W = 980
    H = 180
    gif_w = 84
    gif_h = 100

    title_y = 115
    top_y = 80
    bottom_y = 150
    hop_h = 45
    big_hop_h = 25

    right_x = 760
    left_x = 220
    bottom_x = 100
    n_hops = 8
    hop_w = (right_x - left_x) / n_hops

    T_CYCLE = 2.22
    T_AIR_START = 0.78
    T_AIR_END = 1.25
    AIR_DUR = T_AIR_END - T_AIR_START

    hops_data = []  # list of (x0, y0, x1, y1, is_big)

    # Phase 1: 右→左
    for i in range(n_hops):
        x0 = right_x - i * hop_w
        x1 = right_x - (i + 1) * hop_w
        hops_data.append((x0, top_y, x1, top_y, False))

    # Phase 2: 跳下去
    hops_data.append((left_x, top_y, bottom_x, bottom_y, True))

    # Phase 3: 跳回来
    hops_data.append((bottom_x, bottom_y, left_x, top_y, True))

    # Phase 4: 左→右
    for i in range(n_hops):
        x0 = left_x + i * hop_w
        x1 = left_x + (i + 1) * hop_w
        hops_data.append((x0, top_y, x1, top_y, False))

    total_hops = len(hops_data)
    total_time = total_hops * T_CYCLE

    all_points = []
    all_keytimes = []
    
    samples_per_hop = 10

    for hop_i, (x0, y0, x1, y1, is_big) in enumerate(hops_data):
        h = big_hop_h if is_big else hop_h

        t_base = hop_i * T_CYCLE
        t_start_air = t_base + T_AIR_START
        t_end_air = t_base + T_AIR_END
        t_next = (hop_i + 1) * T_CYCLE

        if hop_i == 0:
            all_points.append((x0, y0))
            all_keytimes.append(0.0)

        # 待命结束（准备起跳）
        all_points.append((x0, y0))
        all_keytimes.append(t_start_air / total_time)

        # 飞行中途的多帧采样
        air_pts = parabolic_hop(x0, y0, x1, y1, h, samples_per_hop)
        for j, (px, py) in enumerate(air_pts):
            frac = (j + 1) / samples_per_hop
            kt = (t_start_air + frac * AIR_DUR) / total_time
            all_points.append((px, py))
            all_keytimes.append(kt)

        # 落地瞬间
        all_points.append((x1, y1))
        all_keytimes.append(t_end_air / total_time)

        # 如果是最后一个 hop，结束时间刚好是 total_time
        if hop_i == total_hops - 1:
            all_points.append((x1, y1))
            all_keytimes.append(1.0)

    # 格式化
    values_str = ";".join(f"{x:.1f},{y:.1f}" for x, y in all_points)
    kt_str = ";".join(f"{t:.5f}" for t in all_keytimes)

    dur = f"{total_time:.2f}s"

    # 左右翻转时间点
    # 左朝向: Phase 1 (n_hops) + Phase 2 (1 hop down) => 共 n_hops + 1 个 hop
    # 翻转发生在第 (n_hops + 1) 个 hop 的结尾，即 t = (n_hops + 1) * T_CYCLE
    flip_t = ((n_hops + 1) * T_CYCLE) / total_time

    gy = -gif_h
    gx = gif_w / 2

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}"
     role="img" aria-label="NeXus : the Next-gen Unified Sub-researcher">

  <text x="{W / 2}" y="{title_y}" text-anchor="middle"
    font-family="Segoe UI, Arial, sans-serif" fill="#0f172a">
    <tspan font-weight="800" font-size="46">NeXus</tspan>
    <tspan font-weight="600" font-size="34"> : </tspan>
    <tspan font-style="italic" font-weight="400" font-size="22" fill="#555">the Next-gen Unified Sub-researcher</tspan>
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
    print(f"[OK] 动画头部 SVG (完美同步版) → {svg_path}")


if __name__ == "__main__":
    main()
