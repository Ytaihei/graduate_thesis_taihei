#!/usr/bin/env python3
"""
UDP測定結果のプロットスクリプト
4GとGateway(GW)のUDPスループットとジッターを比較するグラフを生成
"""

import glob
import json
import os
import warnings

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

# フォント警告を抑制
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# フォント設定（macOS用）
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans', 'sans-serif']

def parse_iperf_json(filepath):
    """iperf3のJSONL形式のファイルを解析"""
    intervals = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if data.get('event') == 'interval':
                    interval_data = data['data']['sum']
                    intervals.append({
                        'time': interval_data['end'],
                        'throughput_mbps': interval_data['bits_per_second'] / 1e6,
                        'jitter_ms': interval_data.get('jitter_ms', 0),
                        'lost_percent': interval_data.get('lost_percent', 0),
                        'packets': interval_data.get('packets', 0),
                        'lost_packets': interval_data.get('lost_packets', 0)
                    })
            except json.JSONDecodeError:
                continue
    return intervals

def get_summary_stats(intervals):
    """統計情報を計算"""
    throughputs = [i['throughput_mbps'] for i in intervals]
    jitters = [i['jitter_ms'] for i in intervals]
    lost_percents = [i['lost_percent'] for i in intervals]

    return {
        'avg_throughput': np.mean(throughputs),
        'std_throughput': np.std(throughputs),
        'min_throughput': np.min(throughputs),
        'max_throughput': np.max(throughputs),
        'avg_jitter': np.mean(jitters),
        'std_jitter': np.std(jitters),
        'avg_loss': np.mean(lost_percents),
        'total_lost': sum(i['lost_packets'] for i in intervals),
        'total_packets': sum(i['packets'] for i in intervals)
    }

def plot_throughput_comparison(data_4g, data_gw, target_bitrate, direction, ax):
    """スループット比較をプロット"""
    times_4g = [d['time'] for d in data_4g]
    throughput_4g = [d['throughput_mbps'] for d in data_4g]

    times_gw = [d['time'] for d in data_gw]
    throughput_gw = [d['throughput_mbps'] for d in data_gw]

    ax.plot(times_4g, throughput_4g, label='4G (Direct)', alpha=0.8, linewidth=1)
    ax.plot(times_gw, throughput_gw, label='Gateway', alpha=0.8, linewidth=1)
    ax.axhline(y=target_bitrate, color='r', linestyle='--', alpha=0.5, label=f'Target ({target_bitrate} Mbps)')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Throughput (Mbps)')
    ax.set_title(f'UDP {direction} Throughput Comparison ({target_bitrate}M target)')
    ax.legend()
    ax.grid(True, alpha=0.3)

def plot_jitter_comparison(data_4g, data_gw, target_bitrate, direction, ax):
    """ジッター比較をプロット"""
    times_4g = [d['time'] for d in data_4g]
    jitter_4g = [d['jitter_ms'] for d in data_4g]

    times_gw = [d['time'] for d in data_gw]
    jitter_gw = [d['jitter_ms'] for d in data_gw]

    ax.plot(times_4g, jitter_4g, label='4G (Direct)', alpha=0.8, linewidth=1)
    ax.plot(times_gw, jitter_gw, label='Gateway', alpha=0.8, linewidth=1)

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Jitter (ms)')
    ax.set_title(f'UDP {direction} Jitter Comparison ({target_bitrate}M target)')
    ax.legend()
    ax.grid(True, alpha=0.3)

def main():
    base_dir = '/Users/taihei/Downloads/data'

    # UDPファイルのパターンを定義
    # DL: Downlink, UL: Uplink
    patterns = {
        'DL': [
            ('5M', '4G_UDP_DL_5M.json', 'GW_UDP_DL_5M.json'),
            ('10M', '4G_UDP_DL_10M.json', 'GW_UDP_DL_10M.json'),
            ('15M', '4G_UDP_DL_15M.json', 'GW_UDP_DL_15M.json'),
            ('16M', '4G_UDP_DL_16M.json', 'GW_UDP_DL_16M.json'),
            ('20M', '4G_UDP_DL_20M.json', 'GW_UDP_DL_20M.json'),
        ],
        'UL': [
            ('3M', '4G_UDP_UL_3M.json', 'GW_UDP_UL_3M.json'),
            ('5M', '4G_UDP_UL_5M.json', 'GW_UDP_UL_5M.json'),
            ('10M', '4G_UDP_UL_10M.json', 'GW_UDP_UL_10M.json'),
        ]
    }

    # 存在するファイルのみ処理
    available_tests = {'DL': [], 'UL': []}

    for direction, tests in patterns.items():
        for target, f4g, fgw in tests:
            path_4g = os.path.join(base_dir, '4G', f4g)
            path_gw = os.path.join(base_dir, 'GW', fgw)
            if os.path.exists(path_4g) and os.path.exists(path_gw):
                available_tests[direction].append((target, path_4g, path_gw))

    print("=" * 60)
    print("UDP測定結果の統計サマリー")
    print("=" * 60)

    all_stats = {}

    for direction in ['DL', 'UL']:
        if not available_tests[direction]:
            continue

        print(f"\n【{direction} ({'ダウンリンク' if direction == 'DL' else 'アップリンク'})】")
        print("-" * 60)

        for target, path_4g, path_gw in available_tests[direction]:
            data_4g = parse_iperf_json(path_4g)
            data_gw = parse_iperf_json(path_gw)

            stats_4g = get_summary_stats(data_4g)
            stats_gw = get_summary_stats(data_gw)

            all_stats[f'{direction}_{target}'] = {
                '4G': {'data': data_4g, 'stats': stats_4g},
                'GW': {'data': data_gw, 'stats': stats_gw}
            }

            target_mbps = float(target.replace('M', ''))
            print(f"\n  Target: {target} Mbps")
            print(f"  {'Metric':<20} {'4G (Direct)':<20} {'Gateway':<20}")
            print(f"  {'-'*58}")
            print(f"  {'Avg Throughput':<20} {stats_4g['avg_throughput']:.2f} Mbps{'':<7} {stats_gw['avg_throughput']:.2f} Mbps")
            print(f"  {'Std Throughput':<20} {stats_4g['std_throughput']:.2f} Mbps{'':<7} {stats_gw['std_throughput']:.2f} Mbps")
            print(f"  {'Avg Jitter':<20} {stats_4g['avg_jitter']:.2f} ms{'':<10} {stats_gw['avg_jitter']:.2f} ms")
            print(f"  {'Avg Loss':<20} {stats_4g['avg_loss']:.2f} %{'':<11} {stats_gw['avg_loss']:.2f} %")

    # ============================================
    # グラフ1: 全てのDLスループット時系列
    # ============================================
    if available_tests['DL']:
        n_dl = len(available_tests['DL'])
        fig, axes = plt.subplots(n_dl, 2, figsize=(14, 4*n_dl))
        if n_dl == 1:
            axes = [axes]

        fig.suptitle('UDP Downlink Performance Comparison (4G vs Gateway)', fontsize=14, fontweight='bold')

        for i, (target, path_4g, path_gw) in enumerate(available_tests['DL']):
            data_4g = all_stats[f'DL_{target}']['4G']['data']
            data_gw = all_stats[f'DL_{target}']['GW']['data']
            target_mbps = float(target.replace('M', ''))

            plot_throughput_comparison(data_4g, data_gw, target_mbps, 'DL', axes[i][0])
            plot_jitter_comparison(data_4g, data_gw, target_mbps, 'DL', axes[i][1])

        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, 'UDP_DL_comparison.png'), dpi=150, bbox_inches='tight')
        print(f"\n✓ 保存: {os.path.join(base_dir, 'UDP_DL_comparison.png')}")

    # ============================================
    # グラフ2: 全てのULスループット時系列
    # ============================================
    if available_tests['UL']:
        n_ul = len(available_tests['UL'])
        fig, axes = plt.subplots(n_ul, 2, figsize=(14, 4*n_ul))
        if n_ul == 1:
            axes = [axes]

        fig.suptitle('UDP Uplink Performance Comparison (4G vs Gateway)', fontsize=14, fontweight='bold')

        for i, (target, path_4g, path_gw) in enumerate(available_tests['UL']):
            data_4g = all_stats[f'UL_{target}']['4G']['data']
            data_gw = all_stats[f'UL_{target}']['GW']['data']
            target_mbps = float(target.replace('M', ''))

            plot_throughput_comparison(data_4g, data_gw, target_mbps, 'UL', axes[i][0])
            plot_jitter_comparison(data_4g, data_gw, target_mbps, 'UL', axes[i][1])

        plt.tight_layout()
        plt.savefig(os.path.join(base_dir, 'UDP_UL_comparison.png'), dpi=150, bbox_inches='tight')
        print(f"✓ 保存: {os.path.join(base_dir, 'UDP_UL_comparison.png')}")

    # ============================================
    # グラフ3: バー表示の平均スループット比較
    # ============================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # DL
    if available_tests['DL']:
        targets_dl = [t[0] for t in available_tests['DL']]
        targets_dl_mbps = [float(t.replace('M', '')) for t in targets_dl]
        avg_4g_dl = [all_stats[f'DL_{t}']['4G']['stats']['avg_throughput'] for t in targets_dl]
        avg_gw_dl = [all_stats[f'DL_{t}']['GW']['stats']['avg_throughput'] for t in targets_dl]

        x = np.arange(len(targets_dl))
        width = 0.35

        bars1 = axes[0].bar(x - width/2, avg_4g_dl, width, label='4G (Direct)', alpha=0.8)
        bars2 = axes[0].bar(x + width/2, avg_gw_dl, width, label='Gateway', alpha=0.8)
        axes[0].plot(x, targets_dl_mbps, 'r--', marker='o', label='Target', alpha=0.7)

        axes[0].set_xlabel('Target Bitrate')
        axes[0].set_ylabel('Average Throughput (Mbps)')
        axes[0].set_title('UDP Downlink - Average Throughput')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(targets_dl)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3, axis='y')

    # UL
    if available_tests['UL']:
        targets_ul = [t[0] for t in available_tests['UL']]
        targets_ul_mbps = [float(t.replace('M', '')) for t in targets_ul]
        avg_4g_ul = [all_stats[f'UL_{t}']['4G']['stats']['avg_throughput'] for t in targets_ul]
        avg_gw_ul = [all_stats[f'UL_{t}']['GW']['stats']['avg_throughput'] for t in targets_ul]

        x = np.arange(len(targets_ul))
        width = 0.35

        bars1 = axes[1].bar(x - width/2, avg_4g_ul, width, label='4G (Direct)', alpha=0.8)
        bars2 = axes[1].bar(x + width/2, avg_gw_ul, width, label='Gateway', alpha=0.8)
        axes[1].plot(x, targets_ul_mbps, 'r--', marker='o', label='Target', alpha=0.7)

        axes[1].set_xlabel('Target Bitrate')
        axes[1].set_ylabel('Average Throughput (Mbps)')
        axes[1].set_title('UDP Uplink - Average Throughput')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(targets_ul)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'UDP_avg_throughput_comparison.png'), dpi=150, bbox_inches='tight')
    print(f"✓ 保存: {os.path.join(base_dir, 'UDP_avg_throughput_comparison.png')}")

    # ============================================
    # グラフ4: ジッター比較バー
    # ============================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # DL Jitter
    if available_tests['DL']:
        targets_dl = [t[0] for t in available_tests['DL']]
        jitter_4g_dl = [all_stats[f'DL_{t}']['4G']['stats']['avg_jitter'] for t in targets_dl]
        jitter_gw_dl = [all_stats[f'DL_{t}']['GW']['stats']['avg_jitter'] for t in targets_dl]

        x = np.arange(len(targets_dl))
        width = 0.35

        axes[0].bar(x - width/2, jitter_4g_dl, width, label='4G (Direct)', alpha=0.8)
        axes[0].bar(x + width/2, jitter_gw_dl, width, label='Gateway', alpha=0.8)

        axes[0].set_xlabel('Target Bitrate')
        axes[0].set_ylabel('Average Jitter (ms)')
        axes[0].set_title('UDP Downlink - Average Jitter')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(targets_dl)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3, axis='y')

    # UL Jitter
    if available_tests['UL']:
        targets_ul = [t[0] for t in available_tests['UL']]
        jitter_4g_ul = [all_stats[f'UL_{t}']['4G']['stats']['avg_jitter'] for t in targets_ul]
        jitter_gw_ul = [all_stats[f'UL_{t}']['GW']['stats']['avg_jitter'] for t in targets_ul]

        x = np.arange(len(targets_ul))
        width = 0.35

        axes[1].bar(x - width/2, jitter_4g_ul, width, label='4G (Direct)', alpha=0.8)
        axes[1].bar(x + width/2, jitter_gw_ul, width, label='Gateway', alpha=0.8)

        axes[1].set_xlabel('Target Bitrate')
        axes[1].set_ylabel('Average Jitter (ms)')
        axes[1].set_title('UDP Uplink - Average Jitter')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(targets_ul)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'UDP_avg_jitter_comparison.png'), dpi=150, bbox_inches='tight')
    print(f"✓ 保存: {os.path.join(base_dir, 'UDP_avg_jitter_comparison.png')}")

    # ============================================
    # グラフ5: パケットロス比較
    # ============================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # DL Loss
    if available_tests['DL']:
        targets_dl = [t[0] for t in available_tests['DL']]
        loss_4g_dl = [all_stats[f'DL_{t}']['4G']['stats']['avg_loss'] for t in targets_dl]
        loss_gw_dl = [all_stats[f'DL_{t}']['GW']['stats']['avg_loss'] for t in targets_dl]

        x = np.arange(len(targets_dl))
        width = 0.35

        axes[0].bar(x - width/2, loss_4g_dl, width, label='4G (Direct)', alpha=0.8)
        axes[0].bar(x + width/2, loss_gw_dl, width, label='Gateway', alpha=0.8)

        axes[0].set_xlabel('Target Bitrate')
        axes[0].set_ylabel('Average Packet Loss (%)')
        axes[0].set_title('UDP Downlink - Average Packet Loss')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(targets_dl)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3, axis='y')

    # UL Loss
    if available_tests['UL']:
        targets_ul = [t[0] for t in available_tests['UL']]
        loss_4g_ul = [all_stats[f'UL_{t}']['4G']['stats']['avg_loss'] for t in targets_ul]
        loss_gw_ul = [all_stats[f'UL_{t}']['GW']['stats']['avg_loss'] for t in targets_ul]

        x = np.arange(len(targets_ul))
        width = 0.35

        axes[1].bar(x - width/2, loss_4g_ul, width, label='4G (Direct)', alpha=0.8)
        axes[1].bar(x + width/2, loss_gw_ul, width, label='Gateway', alpha=0.8)

        axes[1].set_xlabel('Target Bitrate')
        axes[1].set_ylabel('Average Packet Loss (%)')
        axes[1].set_title('UDP Uplink - Average Packet Loss')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(targets_ul)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(os.path.join(base_dir, 'UDP_packet_loss_comparison.png'), dpi=150, bbox_inches='tight')
    print(f"✓ 保存: {os.path.join(base_dir, 'UDP_packet_loss_comparison.png')}")

    print("\n" + "=" * 60)
    print("グラフの生成が完了しました")
    print("=" * 60)

    # プロットを表示
    plt.show()

if __name__ == '__main__':
    main()
