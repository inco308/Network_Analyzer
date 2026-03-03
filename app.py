from flask import Flask, render_template, request, jsonify
import os
import subprocess
import network_analyzer as na
from scapy.all import rdpcap, IP, TCP, UDP
import csv
from collections import defaultdict
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

sessions = []
graph = None
capture_process = None
capture_thread = None
is_capturing = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    global sessions, graph

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            sessions = na.read_csv(filepath)
            graph = na.build_graph(sessions)
            return jsonify({
                'success': True,
                'node_count': len(graph.graph.nodes()),
                'edge_count': len(graph.graph.edges()),
                'session_count': len(sessions)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


@app.route('/sort_traffic', methods=['GET'])
def sort_traffic():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    sorted_nodes = na.sort_nodes_by_traffic(graph)
    return jsonify(sorted_nodes)


@app.route('/filter_https', methods=['GET'])
def filter_https():
    if graph is None or not sessions:
        return jsonify({'error': 'No data loaded'}), 400

    https_nodes = na.filter_https_nodes(sessions, graph)
    return jsonify(https_nodes)


@app.route('/filter_unidirectional', methods=['GET'])
def filter_unidirectional():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    threshold = request.args.get('threshold', 0.8, type=float)
    unidirectional_nodes = na.filter_unidirectional_nodes(graph, threshold)
    return jsonify([(ip, total, ratio) for ip, total, ratio in unidirectional_nodes])


@app.route('/find_path', methods=['POST'])
def find_path():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    data = request.get_json()
    start_ip = data.get('start_ip')
    end_ip = data.get('end_ip')

    min_congestion_path = na.find_min_congestion_path(graph, start_ip, end_ip)
    min_hop_path = na.find_min_hop_path(graph, start_ip, end_ip)

    return jsonify({
        'min_congestion': {
            'path': min_congestion_path[0] if min_congestion_path else None,
            'congestion': min_congestion_path[1] if min_congestion_path else None
        },
        'min_hop': {
            'path': min_hop_path[0] if min_hop_path else None,
            'congestion': min_hop_path[1] if min_hop_path else None
        }
    })


@app.route('/find_stars', methods=['GET'])
def find_stars():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    min_edges = request.args.get('min_edges', 20, type=int)
    stars = na.find_star_structures(graph, min_edges)
    return jsonify([{'center': s[0], 'leaves': s[1]} for s in stars])


@app.route('/check_security', methods=['POST'])
def check_security():
    if not sessions:
        return jsonify({'error': 'No data loaded'}), 400

    data = request.get_json()
    addr1 = data.get('addr1')
    addr2 = data.get('addr2')
    addr3 = data.get('addr3')
    is_allowed = data.get('is_allowed', True)

    violating = na.check_security_rules(sessions, addr1, addr2, addr3, is_allowed)
    return jsonify(violating)


@app.route('/get_graph_data', methods=['GET'])
def get_graph_data():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    nodes = []
    for node_id in graph.graph.nodes():
        ip = graph.id_to_ip[node_id]
        total = graph.get_node_total_traffic(node_id)
        nodes.append({'id': ip, 'label': ip, 'size': min(50, max(5, total / 1000000))})

    edges = []
    for u, v, data in graph.graph.edges(data=True):
        edges.append({
            'source': graph.id_to_ip[u],
            'target': graph.id_to_ip[v],
            'size': min(10, max(1, data['data'].total_data_size / 1000000))
        })

    return jsonify({'nodes': nodes, 'edges': edges})


def extract_from_pcap(pcap_file):
    sessions_data = []
    try:
        packets = rdpcap(pcap_file)
        session_dict = defaultdict(lambda: {
            'protocol': 0,
            'src_port': 0,
            'dst_port': 0,
            'data_size': 0,
            'start_time': None,
            'end_time': None
        })

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
                session = session_dict[key]

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

        for (source, destination, src_port, dst_port, protocol), session in session_dict.items():
            duration = 0.0
            if session['start_time'] is not None and session['end_time'] is not None:
                duration = session['end_time'] - session['start_time']

            sessions_data.append({
                'source': source,
                'destination': destination,
                'protocol': protocol,
                'src_port': src_port,
                'dst_port': dst_port,
                'data_size': session['data_size'],
                'duration': max(0.001, duration)
            })
    except Exception as e:
        print(f"提取 pcap 错误: {e}")
    
    return sessions_data


@app.route('/list_interfaces', methods=['GET'])
def list_interfaces():
    try:
        result = subprocess.run(
            ['tshark', '-D'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        interfaces = []
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.strip():
                interfaces.append(line.strip())
        return jsonify({'interfaces': interfaces})
    except FileNotFoundError:
        return jsonify({'error': '未找到 tshark，请安装 Wireshark'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/start_capture', methods=['POST'])
def start_capture():
    global capture_process, capture_thread, is_capturing, sessions, graph

    if is_capturing:
        return jsonify({'error': '已有捕获任务正在进行'}), 400

    data = request.get_json()
    interface = data.get('interface')
    duration = data.get('duration', 60)

    if not interface:
        return jsonify({'error': '请选择网络接口'}), 400

    temp_pcap = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_capture.pcap')

    def capture_worker():
        global capture_process, is_capturing, sessions, graph
        try:
            tshark_cmd = [
                'tshark',
                '-i', str(interface),
                '-a', f'duration:{duration}',
                '-w', temp_pcap
            ]
            capture_process = subprocess.Popen(tshark_cmd)
            capture_process.wait()

            if os.path.exists(temp_pcap) and os.path.getsize(temp_pcap) > 0:
                sessions = extract_from_pcap(temp_pcap)
                graph = na.build_graph(sessions)
        except Exception as e:
            print(f"捕获错误: {e}")
        finally:
            is_capturing = False
            capture_process = None

    is_capturing = True
    capture_thread = threading.Thread(target=capture_worker)
    capture_thread.start()

    return jsonify({'success': True, 'duration': duration})


@app.route('/capture_status', methods=['GET'])
def capture_status():
    global is_capturing, sessions, graph
    return jsonify({
        'capturing': is_capturing,
        'has_data': sessions is not None and len(sessions) > 0,
        'node_count': len(graph.graph.nodes()) if graph else 0,
        'edge_count': len(graph.graph.edges()) if graph else 0,
        'session_count': len(sessions) if sessions else 0
    })


@app.route('/stop_capture', methods=['POST'])
def stop_capture():
    global capture_process, is_capturing

    if capture_process:
        capture_process.terminate()
        is_capturing = False

    return jsonify({'success': True})


@app.route('/get_subgraph', methods=['POST'])
def get_subgraph():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    data = request.get_json()
    target_ip = data.get('target_ip')

    if not target_ip:
        return jsonify({'error': 'Please provide target IP'}), 400

    subgraph = na.get_subgraph(graph, target_ip)
    if subgraph is None:
        return jsonify({'error': 'IP not found in graph'}), 400

    return jsonify(subgraph)


@app.route('/list_subgraphs', methods=['GET'])
def list_subgraphs():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    subgraphs = na.get_all_subgraphs(graph)
    return jsonify(subgraphs)


@app.route('/get_star_subgraph', methods=['POST'])
def get_star_subgraph():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    data = request.get_json()
    center_ip = data.get('center_ip')

    if not center_ip:
        return jsonify({'error': 'Please provide center IP'}), 400

    subgraph = na.get_star_subgraph(graph, center_ip)
    if subgraph is None:
        return jsonify({'error': 'Center IP not found'}), 400

    return jsonify(subgraph)


@app.route('/get_subgraph_by_root', methods=['POST'])
def get_subgraph_by_root():
    if graph is None:
        return jsonify({'error': 'No data loaded'}), 400

    data = request.get_json()
    root_id = data.get('root_id')

    if root_id is None:
        return jsonify({'error': 'Please provide root ID'}), 400

    subgraph = na.get_subgraph_by_root(graph, root_id)
    return jsonify(subgraph)


if __name__ == '__main__':
    app.run(debug=True)
