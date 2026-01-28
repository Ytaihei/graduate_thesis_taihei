#!/usr/bin/env python3
"""4G と Gateway のスループット詳細比較"""

import json
import os

import numpy as np


def parse_iperf_json(filepath):
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
                    })
            except:
                continue
    return intervals

print('=' * 70)
print('UDP Throughput Comparison: 4G vs Gateway')
print('=' * 70)

base_dir = '/Users/taihei/Downloads/data'

# DL files
dl_files = [
    ('DL 5M', '4G/4G_UDP_DL_5M.json', 'GW/GW_UDP_DL_5M.json'),
    ('DL 10M', '4G/4G_UDP_DL_10M.json', 'GW/GW_UDP_DL_10M.json'),
    ('DL 15M', '4G/4G_UDP_DL_15M.json', 'GW/GW_UDP_DL_15M.json'),
    ('DL 16M', '4G/4G_UDP_DL_16M.json', 'GW/GW_UDP_DL_16M.json'),
    ('DL 20M', '4G/4G_UDP_DL_20M.json', 'GW/GW_UDP_DL_20M.json'),
]

ul_files = [
    ('UL 3M', '4G/4G_UDP_UL_3M.json', 'GW/GW_UDP_UL_3M.json'),
    ('UL 5M', '4G/4G_UDP_UL_5M.json', 'GW/GW_UDP_UL_5M.json'),
    ('UL 10M', '4G/4G_UDP_UL_10M.json', 'GW/GW_UDP_UL_10M.json'),
]

for name, f4g, fgw in dl_files + ul_files:
    path_4g = os.path.join(base_dir, f4g)
    path_gw = os.path.join(base_dir, fgw)

    if not os.path.exists(path_4g) or not os.path.exists(path_gw):
        continue

    data_4g = parse_iperf_json(path_4g)
    data_gw = parse_iperf_json(path_gw)

    tp_4g = [d['throughput_mbps'] for d in data_4g]
    tp_gw = [d['throughput_mbps'] for d in data_gw]

    avg_4g = np.mean(tp_4g)
    avg_gw = np.mean(tp_gw)

    # How many intervals GW > 4G?
    min_len = min(len(tp_4g), len(tp_gw))
    gw_higher = sum(1 for i in range(min_len) if tp_gw[i] > tp_4g[i])

    diff = avg_gw - avg_4g
    diff_pct = (diff / avg_4g) * 100 if avg_4g > 0 else 0

    winner = 'GW' if avg_gw > avg_4g else '4G'

    print(f'\n{name}:')
    print(f'  4G avg: {avg_4g:.2f} Mbps (std: {np.std(tp_4g):.2f})')
    print(f'  GW avg: {avg_gw:.2f} Mbps (std: {np.std(tp_gw):.2f})')
    print(f'  Diff:   {diff:+.2f} Mbps ({diff_pct:+.1f}%)')
    print(f'  Winner: {winner}')
    print(f'  GW > 4G in {gw_higher}/{min_len} intervals ({100*gw_higher/min_len:.1f}%)')

print('\n' + '=' * 70)
print('結論:')
print('=' * 70)
