#!/usr/bin/env python3
"""RTT平均値のみを比較するシンプルなグラフ"""

import json
import warnings

import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
plt.rcParams['font.family'] = 'sans-serif'

# データ読み込み
with open('/Users/taihei/Downloads/data/4G/4G_irtt.json') as f:
    data_4g = json.load(f)
with open('/Users/taihei/Downloads/data/GW/GW_irtt.json') as f:
    data_gw = json.load(f)

# 平均RTT取得 (ナノ秒→ミリ秒)
mean_4g = data_4g['stats']['rtt']['mean'] / 1e6
mean_gw = data_gw['stats']['rtt']['mean'] / 1e6

# グラフ作成
fig, ax = plt.subplots(figsize=(8, 6))

labels = ['4G (Direct)', 'Gateway']
means = [mean_4g, mean_gw]
colors = ['#1f77b4', '#ff7f0e']

bars = ax.bar(labels, means, color=colors, alpha=0.8, width=0.5)

# 数値を棒の上に表示
for bar, val in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{val:.2f} ms', ha='center', va='bottom', fontsize=14, fontweight='bold')

ax.set_ylabel('RTT (ms)', fontsize=12)
ax.set_title('Average RTT Comparison: 4G vs Gateway', fontsize=14, fontweight='bold')
ax.set_ylim(0, max(means) * 1.2)
ax.grid(True, alpha=0.3, axis='y')

# 差分を注釈
diff = mean_gw - mean_4g
diff_pct = (diff / mean_4g) * 100
ax.annotate(f'Difference: +{diff:.2f} ms (+{diff_pct:.1f}%)',
            xy=(0.5, max(means) * 1.08), fontsize=11, ha='center')

plt.tight_layout()
plt.savefig('/Users/taihei/Downloads/data/IRTT_mean_comparison.png', dpi=150, bbox_inches='tight')

print(f'4G Mean RTT: {mean_4g:.2f} ms')
print(f'GW Mean RTT: {mean_gw:.2f} ms')
print(f'Difference: +{diff:.2f} ms (+{diff_pct:.1f}%)')
print()
print('Saved: /Users/taihei/Downloads/data/IRTT_mean_comparison.png')
