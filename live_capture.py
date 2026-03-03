from scapy.all import rdpcap, IP, TCP, UDP
import csv
from collections import defaultdict
import subprocess
import os
import time
import sys


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
    for pkt in packets:
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


def capture_and_extract(interface, duration, output_csv, temp_pcap='temp_capture.pcap'):
    try:
        tshark_path = 'tshark'

        tshark_cmd = [
            tshark_path,
            '-i', str(interface),
            '-a', f'duration:{duration}',
            '-w', temp_pcap
        ]

        print(f"🎯 开始在接口 {interface} 上捕获流量，持续 {duration} 秒...")
        print("💡 提示：请先使用 'python live_capture.py list' 查看可用接口编号")
        print("按 Ctrl+C 可以提前停止捕获")

        process = subprocess.Popen(tshark_cmd)
        process.wait()

        print("✅ 捕获完成！")

        if os.path.exists(temp_pcap):
            file_size = os.path.getsize(temp_pcap)
            print(f"捕获文件大小: {file_size} 字节")

            if file_size > 0:
                extract_from_pcap(temp_pcap, output_csv)
            else:
                print("⚠️  捕获到的文件为空，请检查网络连接")
        else:
            print("❌ 未生成捕获文件")

    except FileNotFoundError:
        print("❌ 未找到 tshark，请确保已安装 Wireshark 并添加到系统 PATH")
        print("💡 Wireshark 下载地址: https://www.wireshark.org/download.html")
    except KeyboardInterrupt:
        print("\n⚠️  用户中断捕获")
    except Exception as e:
        print(f"❌ 错误: {e}")


def list_interfaces():
    try:
        result = subprocess.run(
            ['tshark', '-D'], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        print("可用网络接口:")
        print(result.stdout)
    except FileNotFoundError:
        print("未找到 tshark，请安装 Wireshark")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  1. 列出可用接口: python live_capture.py list")
        print("  2. 实时捕获并提取: python live_capture.py capture <接口编号> <持续秒数> [输出CSV]")
        print("  3. 只转换 pcap: python live_capture.py convert <pcap文件> [输出CSV]")
        print("\n示例:")
        print("  python live_capture.py list")
        print("  python live_capture.py capture 1 60 output.csv")
        print("  python live_capture.py convert capture.pcap output.csv")
        print("\n⚠️  注意：请使用接口编号（如 1, 2, 3...）而不是接口名称！")
    else:
        mode = sys.argv[1]

        if mode == 'list':
            list_interfaces()
        elif mode == 'capture' and len(sys.argv) >= 4:
            interface = sys.argv[2]
            duration = int(sys.argv[3])
            output_csv = sys.argv[4] if len(sys.argv) > 4 else 'network_data.csv'
            capture_and_extract(interface, duration, output_csv)
        elif mode == 'convert' and len(sys.argv) >= 3:
            pcap_file = sys.argv[2]
            output_csv = sys.argv[3] if len(sys.argv) > 3 else 'network_data.csv'
            extract_from_pcap(pcap_file, output_csv)
        else:
            print("参数错误，请查看使用方法")