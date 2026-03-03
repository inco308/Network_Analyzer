import network_analyzer as na
import os

def test_all_functions():
    print('=' * 60)
    print('网络流量分析与异常检测系统 - 功能测试')
    print('=' * 60)

    csv_file = 'network_data.csv'
    if not os.path.exists(csv_file):
        print(f'\n❌ 数据文件 {csv_file} 不存在，请先运行 generate_sample_data.py')
        return

    print('\n1. 读取CSV数据...')
    sessions = na.read_csv(csv_file)
    print(f'   ✓ 成功读取 {len(sessions)} 条会话记录')

    print('\n2. 构建图结构...')
    graph = na.build_graph(sessions)
    print(f'   ✓ 图构建完成')
    print(f'   - 节点数: {len(graph.graph.nodes())}')
    print(f'   - 边数: {len(graph.graph.edges())}')

    print('\n3. 节点流量排序...')
    sorted_nodes = na.sort_nodes_by_traffic(graph)
    print(f'   ✓ 完成排序，前5个节点:')
    for i, (ip, total) in enumerate(sorted_nodes[:5], 1):
        print(f'     {i}. {ip}: {total:,} bytes')

    print('\n4. HTTPS节点筛选...')
    https_nodes = na.filter_https_nodes(sessions, graph)
    print(f'   ✓ 找到 {len(https_nodes)} 个HTTPS相关节点')
    for i, (ip, total) in enumerate(https_nodes[:5], 1):
        print(f'     {i}. {ip}: {total:,} bytes')

    print('\n5. 单向流量节点筛选 (阈值 > 80%)...')
    unidirectional_nodes = na.filter_unidirectional_nodes(graph, 0.8)
    print(f'   ✓ 找到 {len(unidirectional_nodes)} 个单向流量节点')
    for i, (ip, total, ratio) in enumerate(unidirectional_nodes[:5], 1):
        print(f'     {i}. {ip}: 总流量={total:,} bytes, 发出占比={ratio*100:.1f}%')

    print('\n6. 路径查找测试...')
    if len(sorted_nodes) >= 2:
        start_ip = sorted_nodes[0][0]
        end_ip = sorted_nodes[1][0]
        print(f'   查找路径: {start_ip} -> {end_ip}')

        min_congestion = na.find_min_congestion_path(graph, start_ip, end_ip)
        if min_congestion:
            print(f'   ✓ 拥塞最小路径:')
            print(f'     路径: {" -> ".join(min_congestion[0])}')
            print(f'     总拥塞: {min_congestion[1]:.2f}')
        else:
            print(f'   ✗ 未找到拥塞最小路径')

        min_hop = na.find_min_hop_path(graph, start_ip, end_ip)
        if min_hop:
            print(f'   ✓ 跳数最小路径:')
            print(f'     路径: {" -> ".join(min_hop[0])}')
            print(f'     跳数: {len(min_hop[0]) - 1}')
            print(f'     总拥塞: {min_hop[1]:.2f}')
        else:
            print(f'   ✗ 未找到跳数最小路径')

    print('\n7. 星型结构检测 (最小边数=20)...')
    stars = na.find_star_structures(graph, 20)
    print(f'   ✓ 找到 {len(stars)} 个星型结构')
    for i, (center, leaves) in enumerate(stars, 1):
        print(f'     {i}. 中心节点: {center}')
        print(f'        连接节点数: {len(leaves)}')
        print(f'        部分连接节点: {", ".join(leaves[:5])}{"..." if len(leaves) > 5 else ""}')

    print('\n8. 安全规则检查...')
    test_addr1 = '10.0.0.99'
    test_addr2 = '192.168.200.1'
    test_addr3 = '192.168.200.255'
    print(f'   检查规则: {test_addr1} 不允许与 {test_addr2}-{test_addr3} 通信')
    violating = na.check_security_rules(sessions, test_addr1, test_addr2, test_addr3, is_allowed=False)
    print(f'   ✓ 找到 {len(violating)} 条违规会话')

    print('\n' + '=' * 60)
    print('✓ 所有功能测试完成！')
    print('=' * 60)


if __name__ == '__main__':
    test_all_functions()
