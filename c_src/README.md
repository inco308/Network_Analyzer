# 网络流量分析器 - C语言实现

## 项目概述

高性能的网络流量分析器C语言实现，使用CSR（压缩稀疏行）格式高效存储和分析网络拓扑图。与Python GUI无缝集成，提供出色的性能表现。

## 项目结构

```
c_src/
├── common.h          # 通用类型和宏定义
├── hash_map.h/.c     # 字符串哈希表（IP到ID映射，使用DJB2算法和线性探测）
├── dynamic_array.h/.c # 动态数组实现（支持自动扩容）
├── csr_graph.h/.c    # CSR格式的图数据结构
├── csv_reader.h/.c   # CSV文件读取
├── analysis.h/.c     # 分析算法（流量排序、星型结构、子图、HTTPS筛选等）
├── main.c            # 主程序（命令行接口，与Python通信）
├── build.bat         # Windows编译脚本
└── README.md         # 本文档
```

## 代码规范

1. **模块化设计**：代码按功能组织到不同的.h和.c文件中
2. **函数注释**：所有函数有统一的函数头注释，说明：
   - 功能描述
   - 输入参数
   - 返回值
   - 前置条件
3. **关键步骤注释**：函数内部关键处理步骤有注释说明

## 核心功能

### 1. CSR图结构 (csr_graph)
- 使用CSR（Compressed Sparse Row）格式高效存储稀疏图
- 支持IP到ID的双向映射（使用哈希表）
- 合并相同源IP和目的IP的会话
- 按协议统计流量和持续时间
- 正确维护edges数组和row_ptr数组的对应关系

### 2. 会话合并
- 自动合并相同 (源IP, 目的IP) 的会话
- 累加总数据大小和持续时间
- 分别统计不同协议的流量

### 3. 数据结构

#### 动态数组 (dynamic_array)
- 支持任意类型元素
- 自动扩容（增长因子2）
- 提供append、get、size等基本操作

#### 哈希表 (hash_map)
- DJB2哈希算法
- 线性探测解决冲突
- 负载因子超过0.7时自动扩容
- 用于IP到ID的快速映射

### 4. 分析算法
- **流量排序**：按总流量大小排序节点，流量相同时按IP地址字典序排序
- **HTTPS筛选**：直接从原始会话数据筛选HTTPS节点（protocol=6且dst_port=443）
- **可疑节点筛选**：查找单向流量占比大于指定阈值的节点
- **星型结构查找**：找出中心节点与叶节点的星型拓扑
- **子图查找**：使用并查集（Union-Find）快速确定连通分量
- **路径查找**：查找两个节点之间的最短路径

## 编译

### Windows (MSVC)
使用build.bat脚本：
```batch
cd c_src
build.bat
```

或手动编译：
```batch
cd c_src
cl /O2 /Fe../network_analyzer.exe ^
    hash_map.c dynamic_array.c csr_graph.c csv_reader.c analysis.c main.c
```

### Linux/Mac (GCC)
```bash
cd c_src
gcc -O2 -o ../network_analyzer \
    hash_map.c dynamic_array.c csr_graph.c csv_reader.c analysis.c main.c
```

## 使用方式

### 直接命令行调用
```bash
# 加载CSV文件
network_analyzer load network_data.csv

# 获取图信息
network_analyzer info

# 按流量排序
network_analyzer sort_traffic

# HTTPS筛选
network_analyzer filter_https

# 可疑节点筛选（最小占比0.8）
network_analyzer filter_suspicious 0.8

# 查找星型结构（最小5条边）
network_analyzer find_stars 5

# 路径查找（源IP 目的IP）
network_analyzer find_path 192.168.1.1 192.168.1.100

# 获取指定IP的子图
network_analyzer get_subgraph 192.168.1.1

# 列出所有子图
network_analyzer list_subgraphs

# 安全规则检查
network_analyzer check_security
```

### 通过Python调用
C程序设计为与Python无缝集成，通过JSON格式进行数据交换。
详见 `c_network_analyzer.py` 模块和 `c_analyzer_gui.py` GUI程序。

## 数据结构说明

### CSR格式
```
row_ptr: [0, 2, 5, 5, 8]  # 每个节点的边起始位置
edges: [Edge0, Edge1, Edge2, Edge3, Edge4, Edge5, Edge6, Edge7]
```

### EdgeData
```c
typedef struct {
    int target_node;
    int64_t total_data_size;
    double total_duration;
    int protocol;
    int src_port;
    int dst_port;
    ProtocolTraffic protocol_traffic[MAX_PROTOCOLS];
} EdgeData;
```

### SubgraphEdge
```c
typedef struct {
    int source_node;
    int target_node;
    int64_t total_data_size;
} SubgraphEdge;
```

## 与Python实现的对比

| 特性 | Python实现 | C实现 |
|------|-----------|-------|
| 图结构 | NetworkX邻接表 | CSR压缩稀疏行 |
| 性能 | 适合中小规模数据 | 高性能，适合大规模数据 |
| 内存使用 | 较高 | 较低（CSR格式） |
| 开发效率 | 高 | 中等 |
| 部署 | 需要Python环境 | 独立可执行文件 |

## 已知问题修复

1. **HTTPS筛选结果不同**：修改为直接从原始会话数据筛选，而非依赖CSR图边数据
2. **边数不同**：修复csr_graph_add_edge函数，将新边插入到正确位置
3. **流量排序结果不同**：在流量相同时按IP地址字典序排序
4. **子图有向边缺失**：添加SubgraphEdge结构体保存源节点ID

详细修复记录请参考项目根目录的 `修复记录.md`。

## 相关文档

- `../项目架构说明.md` - 整体项目架构说明
- `../修复记录.md` - 开发过程中的问题和解决方案
- `../README.md` - 主项目README

