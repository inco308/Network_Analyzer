# 网络流量分析与异常检测系统

一个功能完整的网络流量分析系统，提供Python和C两种实现，支持从CSV/PCAP文件读取网络流量数据，构建图结构进行分析，并提供图形界面和Web界面两种使用方式。

## 功能特性

### 核心功能
1. **数据读取**：从CSV文件读取网络流量数据，支持PCAP文件转换
2. **图结构构建**：使用CSR（压缩稀疏行）格式高效存储稀疏图
3. **流量排序**：按流量大小排序节点，流量相同时按IP地址排序
4. **筛选功能**：
   - HTTPS连接筛选（protocol=6且dst_port=443）
   - 单向流量占比>80%的可疑节点筛选
5. **路径查找**：拥塞程度最小和跳数最小路径
6. **星型结构检测**：识别网络中的星型拓扑结构
7. **安全规则检测**：检查网络流量是否符合安全规则
8. **子图分析**：使用并查集快速确定连通分量，支持子图可视化
9. **实时捕获**：使用Wireshark实时捕获网络流量
10. **图可视化**：基于D3.js的交互式图可视化，支持缩放、平移

## 实现版本

### Python版本
- 使用NetworkX库构建图结构
- 提供Flask Web界面
- 提供Tkinter图形界面

### C版本
- 使用CSR格式高效存储图
- 性能优化，适合处理大规模数据
- 与Python GUI无缝集成

## 安装

### 开发环境安装

```bash
pip install -r requirements.txt
```

### 使用打包版本

1. 下载 `release` 文件夹
2. 直接运行 `网络流量分析器.exe` 即可（无需Python环境）

## 使用方式

### 方式一：Web界面

```bash
python app.py
```

然后在浏览器中访问 http://localhost:5000

### 方式二：Tkinter图形界面

```bash
python c_analyzer_gui.py
```

或直接运行打包后的 `网络流量分析器.exe`

### 方式三：Python命令行

```bash
python network_analyzer.py
```

### 方式四：C命令行

```bash
network_analyzer.exe load network_data.csv
network_analyzer.exe info
network_analyzer.exe sort_traffic
```

详细命令参考 `c_src/README.md`

## 项目结构

```
Project/
├── app.py                  # Flask Web应用
├── c_analyzer_gui.py       # Tkinter图形界面
├── network_analyzer.py     # Python分析器
├── c_network_analyzer.py   # Python调用C程序的接口
├── graph_visualizer.py     # 图可视化模块
├── capture_utils.py        # 流量捕获工具
├── network_analyzer.exe    # C语言编译的可执行文件
├── requirements.txt        # Python依赖
├── c_src/                 # C语言源码
│   ├── common.h           # 通用定义
│   ├── dynamic_array.h/c  # 动态数组
│   ├── hash_map.h/c       # 哈希表
│   ├── csr_graph.h/c      # CSR图结构
│   ├── csv_reader.h/c     # CSV读取
│   ├── analysis.h/c       # 分析算法
│   └── main.c             # 主程序
├── templates/             # Web模板
└── release/               # 打包发布版本
```

## 数据格式要求

CSV文件应包含以下列：
- source_ip: 源IP地址
- dest_ip: 目的IP地址
- protocol: 协议号（TCP=6, UDP=17等）
- src_port: 源端口
- dst_port: 目的端口
- data_size: 数据大小（字节）
- duration: 持续时间（秒）

## 开发说明

### 代码规范
- C源码按模块组织到不同的.h和.c文件中
- 所有函数有统一的函数头注释，说明功能、输入输出
- 函数内部关键步骤有注释说明

### 编译C程序

Windows:
```bash
cd c_src
build.bat
```

Linux/Mac:
```bash
cd c_src
gcc -O2 -o ../network_analyzer \
    hash_map.c dynamic_array.c csr_graph.c csv_reader.c analysis.c main.c
```

### 打包可执行文件

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "网络流量分析器" \
    --add-data "network_analyzer.exe;." \
    --add-data "network_data.csv;." \
    c_analyzer_gui.py
```

打包后的文件在 `dist` 目录中。

## 文档

- `项目架构说明.md` - 详细的项目架构和模块说明
- `修复记录.md` - 开发过程中遇到的问题和解决方案
- `c_src/README.md` - C语言实现的详细说明
- `release/README_使用说明.md` - 打包版本的使用说明