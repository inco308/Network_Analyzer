from flask import Flask, render_template, request, jsonify
import os
import network_analyzer as na

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

sessions = []
graph = None


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


if __name__ == '__main__':
    app.run(debug=True)
