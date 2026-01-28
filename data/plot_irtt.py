#!/usr/bin/env python3
"""
IRTT測定結果のプロットスクリプト
4GとGateway(GW)のRTT、遅延を比較するグラフを生成
"""

import json
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np

# フォント警告を抑制
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans', 'sans-serif']

def load_irtt_json(filepath):
    """irttのJSONファイルを読み込み"""
    with open(filepath, 'r') as f:
        return json.load(f)

def extract_round_trips(data):
    """round_tripsからRTT、send_delay、receive_delayを抽出"""
    round_trips = data.get('round_trips', [])

    results = []
    for rt in round_trips:
        if rt.get('lost') == 'true':
            continue

        delay = rt.get('delay', {})
        rtt_ns = delay.get('rtt', 0)
        send_delay_ns = delay.get('send', 0)
        receive_delay_ns = delay.get('receive', 0)

        results.append({
            'seqno': rt.get('seqno', 0),
            'rtt_ms': rtt_ns / 1e6,  # ナノ秒からミリ秒へ
            'send_delay_ms': send_delay_ns / 1e6,
            'receive_delay_ms': receive_delay_ns / 1e6,
        })

    return results

def get_stats(data):
    """統計情報を取得"""
    stats = data.get('stats', {})
    rtt_stats = stats.get('rtt', {})

    return {
        'rtt_mean_ms': rtt_stats.get('mean', 0) / 1e6,
        'rtt_min_ms': rtt_stats.get('min', 0) / 1e6,
        'rtt_max_ms': rtt_stats.get('max', 0) / 1e6,
        'rtt_median_ms': rtt_stats.get('median', 0) / 1e6,
        'rtt_stddev_ms': rtt_stats.get('stddev', 0) / 1e6,
        'n': rtt_stats.get('n', 0),
    }

def main():
    base_dir = '/Users/taihei/Downloads/data'

    path_4g = os.path.join(base_dir, '4G', '4G_irtt.json')
    path_gw = os.path.join(base_dir, 'GW', 'GW_irtt.json')

    # データ読み込み
    data_4g = load_irtt_json(path_4g)
    data_gw = load_irtt_json(path_gw)

    # Round trips抽出
    rt_4g = extract_round_trips(data_4g)
    rt_gw = extract_round_trips(data_gw)

    # 統計情報
    stats_4g = get_stats(data_4g)
    stats_gw = get_stats(data_gw)

    # サマリー表示
    print("=" * 60)
    print("IRTT測定結果サマリー")
    print("=" * 60)
    print(f"\n{'Metric':<20} {'4G (Direct)':<20} {'Gateway':<20}")
    print("-" * 60)
    print(f"{'RTT Mean':<20} {stats_4g['rtt_mean_ms']:.2f} ms{'':<10} {stats_gw['rtt_mean_ms']:.2f} ms")
    print(f"{'RTT Median':<20} {stats_4g['rtt_median_ms']:.2f} ms{'':<10} {stats_gw['rtt_median_ms']:.2f} ms")
    print(f"{'RTT Min':<20} {stats_4g['rtt_min_ms']:.2f} ms{'':<10} {stats_gw['rtt_min_ms']:.2f} ms")
    print(f"{'RTT Max':<20} {stats_4g['rtt_max_ms']:.2f} ms{'':<10} {stats_gw['rtt_max_ms']:.2f} ms")
    print(f"{'RTT Stddev':<20} {stats_4g['rtt_stddev_ms']:.2f} ms{'':<10} {stats_gw['rtt_stddev_ms']:.2f} ms")
    print(f"{'Packets':<20} {stats_4g['n']:<20} {stats_gw['n']}")

    diff = stats_gw['rtt_mean_ms'] - stats_4g['rtt_mean_ms']
    diff_pct = (diff / stats_4g['rtt_mean_ms']) * 100 if stats_4g['rtt_mean_ms'] > 0 else 0
    print(f"\nGateway overhead: {diff:+.2f} ms ({diff_pct:+.1f}%)")

    # データ抽出
    seqno_4g = [r['seqno'] for r in rt_4g]
    rtt_4g = [r['rtt_ms'] for r in rt_4g]

    seqno_gw = [r['seqno'] for r in rt_gw]
    rtt_gw = [r['rtt_ms'] for r in rt_gw]

    # ============================================
    # グラフ1: RTT時系列比較
    # ============================================
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('IRTT Measurement Results: 4G vs Gateway', fontsize=14, fontweight='bold')

    # RTT Time Series
    ax1 = axes[0, 0]
    ax1.plot(seqno_4g, rtt_4g, label='4G (Direct)', alpha=0.8, linewidth=1)
    ax1.plot(seqno_gw, rtt_gw, label='Gateway', alpha=0.8, linewidth=1)
    ax1.axhline(y=stats_4g['rtt_mean_ms'], color='C0', linestyle='--', alpha=0.5, label=f'4G mean ({stats_4g["rtt_mean_ms"]:.1f}ms)')
    ax1.axhline(y=stats_gw['rtt_mean_ms'], color='C1', linestyle='--', alpha=0.5, label=f'GW mean ({stats_gw["rtt_mean_ms"]:.1f}ms)')
    ax1.set_xlabel('Sequence Number')
    ax1.set_ylabel('RTT (ms)')
    ax1.set_title('RTT Time Series')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # RTT Histogram
    ax2 = axes[0, 1]
    ax2.hist(rtt_4g, bins=30, alpha=0.6, label='4G (Direct)', density=True)
    ax2.hist(rtt_gw, bins=30, alpha=0.6, label='Gateway', density=True)
    ax2.axvline(x=stats_4g['rtt_mean_ms'], color='C0', linestyle='--', alpha=0.8)
    ax2.axvline(x=stats_gw['rtt_mean_ms'], color='C1', linestyle='--', alpha=0.8)
    ax2.set_xlabel('RTT (ms)')
    ax2.set_ylabel('Density')
    ax2.set_title('RTT Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # RTT Box Plot
    ax3 = axes[1, 0]
    box_data = [rtt_4g, rtt_gw]
    bp = ax3.boxplot(box_data, labels=['4G (Direct)', 'Gateway'], patch_artist=True)
    colors = ['C0', 'C1']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax3.set_ylabel('RTT (ms)')
    ax3.set_title('RTT Box Plot')
    ax3.grid(True, alpha=0.3, axis='y')

    # RTT CDF
    ax4 = axes[1, 1]
    sorted_4g = np.sort(rtt_4g)
    sorted_gw = np.sort(rtt_gw)
    cdf_4g = np.arange(1, len(sorted_4g) + 1) / len(sorted_4g)
    cdf_gw = np.arange(1, len(sorted_gw) + 1) / len(sorted_gw)

    ax4.plot(sorted_4g, cdf_4g, label='4G (Direct)', linewidth=2)
    ax4.plot(sorted_gw, cdf_gw, label='Gateway', linewidth=2)
    ax4.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='Median (50%)')
    ax4.axhline(y=0.95, color='gray', linestyle=':', alpha=0.5, label='95th percentile')
    ax4.set_xlabel('RTT (ms)')
    ax4.set_ylabel('CDF')
    ax4.set_title('RTT Cumulative Distribution Function')
    ax4.legend(loc='lower right')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(base_dir, 'IRTT_comparison.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ 保存: {output_path}")

    # ============================================
    # グラフ2: 統計バー比較
    # ============================================
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('IRTT Statistics Comparison', fontsize=14, fontweight='bold')

    # Mean, Median, Min, Max
    ax1 = axes[0]
    metrics = ['Mean', 'Median', 'Min', 'Max']
    values_4g = [stats_4g['rtt_mean_ms'], stats_4g['rtt_median_ms'],
                 stats_4g['rtt_min_ms'], stats_4g['rtt_max_ms']]
    values_gw = [stats_gw['rtt_mean_ms'], stats_gw['rtt_median_ms'],
                 stats_gw['rtt_min_ms'], stats_gw['rtt_max_ms']]

    x = np.arange(len(metrics))
    width = 0.35

    ax1.bar(x - width/2, values_4g, width, label='4G (Direct)', alpha=0.8)
    ax1.bar(x + width/2, values_gw, width, label='Gateway', alpha=0.8)
    ax1.set_ylabel('RTT (ms)')
    ax1.set_title('RTT Statistics')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')

    # Stddev comparison
    ax2 = axes[1]
    stddevs = [stats_4g['rtt_stddev_ms'], stats_gw['rtt_stddev_ms']]
    labels = ['4G (Direct)', 'Gateway']
    colors = ['C0', 'C1']
    bars = ax2.bar(labels, stddevs, color=colors, alpha=0.8)
    ax2.set_ylabel('Standard Deviation (ms)')
    ax2.set_title('RTT Variability (Stddev)')
    ax2.grid(True, alpha=0.3, axis='y')

    # 数値を棒の上に表示
    for bar, val in zip(bars, stddevs):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=11)

    plt.tight_layout()
    output_path2 = os.path.join(base_dir, 'IRTT_stats_comparison.png')
    plt.savefig(output_path2, dpi=150, bbox_inches='tight')
    print(f"✓ 保存: {output_path2}")

    print("\n" + "=" * 60)
    print("グラフの生成が完了しました")
    print("=" * 60)

    plt.show()

if __name__ == '__main__':
    main()
