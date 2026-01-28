#!/usr/bin/env python3
"""ターゲット別 平均スループット比較グラフ"""

import json
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'sans-serif'

def parse_iperf_json(filepath):
    """iperf3のJSONL形式を解析して平均スループットを取得"""
    throughputs = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if data.get('event') == 'interval':
                    throughputs.append(data['data']['sum']['bits_per_second'] / 1e6)
            except:
                continue
    return np.mean(throughputs) if throughputs else 0

base_dir = '/Users/taihei/Downloads/data'

# ファイル定義
dl_tests = [
    ('5M', 5, '4G/4G_UDP_DL_5M.json', 'GW/GW_UDP_DL_5M.json'),
    ('10M', 10, '4G/4G_UDP_DL_10M.json', 'GW/GW_UDP_DL_10M.json'),
    ('15M', 15, '4G/4G_UDP_DL_15M.json', 'GW/GW_UDP_DL_15M.json'),
    ('16M', 16, '4G/4G_UDP_DL_16M.json', 'GW/GW_UDP_DL_16M.json'),
    ('20M', 20, '4G/4G_UDP_DL_20M.json', 'GW/GW_UDP_DL_20M.json'),
]

ul_tests = [
    ('3M', 3, '4G/4G_UDP_UL_3M.json', 'GW/GW_UDP_UL_3M.json'),
    ('5M', 5, '4G/4G_UDP_UL_5M.json', 'GW/GW_UDP_UL_5M.json'),
    ('10M', 10, '4G/4G_UDP_UL_10M.json', 'GW/GW_UDP_UL_10M.json'),
]

# データ収集
def collect_data(tests):
    labels, targets, avg_4g, avg_gw = [], [], [], []
    for label, target, f4g, fgw in tests:
        path_4g = os.path.join(base_dir, f4g)
        path_gw = os.path.join(base_dir, fgw)
        if os.path.exists(path_4g) and os.path.exists(path_gw):
            labels.append(label)
            targets.append(target)
            avg_4g.append(parse_iperf_json(path_4g))
            avg_gw.append(parse_iperf_json(path_gw))
    return labels, targets, avg_4g, avg_gw

dl_labels, dl_targets, dl_4g, dl_gw = collect_data(dl_tests)
ul_labels, ul_targets, ul_4g, ul_gw = collect_data(ul_tests)

# グラフ作成
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# DL グラフ
ax = axes[0]
x = np.arange(len(dl_labels))
width = 0.35

bars1 = ax.bar(x - width/2, dl_4g, width, label='4G (Direct)', color='#1f77b4', alpha=0.8)
bars2 = ax.bar(x + width/2, dl_gw, width, label='Gateway', color='#ff7f0e', alpha=0.8)
ax.plot(x, dl_targets, 'r--', marker='o', markersize=8, label='Target', linewidth=2)

# 数値表示
for bar, val in zip(bars1, dl_4g):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9)
for bar, val in zip(bars2, dl_gw):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9)

ax.set_xlabel('Target Bitrate', fontsize=12)
ax.set_ylabel('Throughput (Mbps)', fontsize=12)
ax.set_title('UDP Downlink - Average Throughput', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(dl_labels)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, max(max(dl_4g), max(dl_gw), max(dl_targets)) * 1.15)

# UL グラフ
ax = axes[1]
x = np.arange(len(ul_labels))

bars1 = ax.bar(x - width/2, ul_4g, width, label='4G (Direct)', color='#1f77b4', alpha=0.8)
bars2 = ax.bar(x + width/2, ul_gw, width, label='Gateway', color='#ff7f0e', alpha=0.8)
ax.plot(x, ul_targets, 'r--', marker='o', markersize=8, label='Target', linewidth=2)

# 数値表示
for bar, val in zip(bars1, ul_4g):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9)
for bar, val in zip(bars2, ul_gw):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9)

ax.set_xlabel('Target Bitrate', fontsize=12)
ax.set_ylabel('Throughput (Mbps)', fontsize=12)
ax.set_title('UDP Uplink - Average Throughput', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(ul_labels)
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim(0, max(max(ul_4g), max(ul_gw), max(ul_targets)) * 1.15)

plt.tight_layout()
plt.savefig(os.path.join(base_dir, 'UDP_throughput_simple.png'), dpi=150, bbox_inches='tight')

print("UDP Average Throughput Comparison")
print("=" * 50)
print("\nDownlink:")
for l, t, v4, vg in zip(dl_labels, dl_targets, dl_4g, dl_gw):
    diff = vg - v4
    print(f"  {l}: 4G={v4:.2f}, GW={vg:.2f} (diff={diff:+.2f} Mbps)")

print("\nUplink:")
for l, t, v4, vg in zip(ul_labels, ul_targets, ul_4g, ul_gw):
    diff = vg - v4
    print(f"  {l}: 4G={v4:.2f}, GW={vg:.2f} (diff={diff:+.2f} Mbps)")

print(f"\nSaved: {os.path.join(base_dir, 'UDP_throughput_simple.png')}")
