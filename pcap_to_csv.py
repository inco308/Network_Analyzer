from scapy.all import rdpcap, IP, TCP, UDP
import csv
from collections import defaultdict


def extract_from_pcap(pcap_file, output_csv):
    print(f"正在读取 pcap 文件: {pcap_file}")
    packets = rdpcap(pcap_file)
    print(f"共读取到 {len(packets)} 个数据包")

    sessions = defaultdict(lambda: {
        'protocol': 0,
        'src_port': 0,
        'dst_port': 0,
        'data_size': 0,
        'start_time': None,
        'end_time': None
    })

    print("正在解析数据包...")
    for i, pkt in enumerate(packets):
        if IP in pkt:
            ip = pkt[IP]
            source = ip.src
            destination = ip.dst

            protocol = ip.proto
            src_port = 0
            dst_port = 0

            if TCP in pkt:
                tcp = pkt[TCP]
                src_port = tcp.sport
                dst_port = tcp.dport
            elif UDP in pkt:
                udp = pkt[UDP]
                src_port = udp.sport
                dst_port = udp.dport

            key = (source, destination, src_port, dst_port, protocol)
            session = sessions[key]

            if session['protocol'] == 0:
                session['protocol'] = protocol
                session['src_port'] = src_port
                session['dst_port'] = dst_port

            session['data_size'] += len(pkt)

            pkt_time = pkt.time
            if session['start_time'] is None or pkt_time < session['start_time']:
                session['start_time'] = pkt_time
            if session['end_time'] is None or pkt_time > session['end_time']:
                session['end_time'] = pkt_time

    print(f"共提取到 {len(sessions)} 个会话")

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Source', 'Destination', 'Protocol',
            'SrcPort', 'DstPort', 'DataSize', 'Duration'
        ])
        writer.writeheader()

        for (source, destination, src_port, dst_port, protocol), session in sessions.items():
            duration = 0.0
            if session['start_time'] is not None and session['end_time'] is not None:
                duration = session['end_time'] - session['start_time']

            writer.writerow({
                'Source': source,
                'Destination': destination,
                'Protocol': protocol,
                'SrcPort': src_port,
                'DstPort': dst_port,
                'DataSize': session['data_size'],
                'Duration': max(0.001, duration)
            })

    print(f"数据已保存到: {output_csv}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python pcap_to_csv.py <pcap文件> [输出CSV文件]")
        print("示例: python pcap_to_csv.py network.pcap network_data.csv")
    else:
        pcap_file = sys.argv[1]
        output_csv = sys.argv[2] if len(sys.argv) > 2 else 'network_data.csv'
        extract_from_pcap(pcap_file, output_csv)