import csv
import random

def generate_sample_data(file_path='network_data.csv', num_sessions=1000):
    protocols = [1, 6, 17]
    ports = [80, 443, 22, 21, 53, 8080, 3306, 27017]

    ips = []
    for i in range(1, 51):
        ips.append(f'192.168.1.{i}')
    for i in range(1, 31):
        ips.append(f'10.0.0.{i}')
    for i in range(1, 21):
        ips.append(f'172.16.0.{i}')

    star_center = '192.168.1.254'

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Source', 'Destination', 'Protocol', 'SrcPort', 'DstPort', 'DataSize', 'Duration'])
        writer.writeheader()

        for i in range(1, 25):
            leaf_ip = f'192.168.100.{i}'
            writer.writerow({
                'Source': leaf_ip,
                'Destination': star_center,
                'Protocol': random.choice([6, 17]),
                'SrcPort': random.randint(10000, 65535),
                'DstPort': random.choice(ports),
                'DataSize': random.randint(100, 10000),
                'Duration': round(random.uniform(0.001, 5.0), 6)
            })

        for _ in range(num_sessions):
            source = random.choice(ips)
            destination = random.choice(ips)
            while destination == source:
                destination = random.choice(ips)

            protocol = random.choice(protocols)
            src_port = random.randint(10000, 65535)
            dst_port = random.choice(ports)
            data_size = random.randint(64, 1000000)
            duration = round(random.uniform(0.0001, 10.0), 6)

            writer.writerow({
                'Source': source,
                'Destination': destination,
                'Protocol': protocol,
                'SrcPort': src_port,
                'DstPort': dst_port,
                'DataSize': data_size,
                'Duration': duration
            })

        for _ in range(200):
            source = random.choice(ips)
            destination = random.choice(ips)
            while destination == source:
                destination = random.choice(ips)

            writer.writerow({
                'Source': source,
                'Destination': destination,
                'Protocol': 6,
                'SrcPort': random.randint(10000, 65535),
                'DstPort': 443,
                'DataSize': random.randint(512, 500000),
                'Duration': round(random.uniform(0.01, 30.0), 6)
            })

        scanner_ip = '10.0.0.99'
        for i in range(1, 101):
            target = f'192.168.200.{i}'
            writer.writerow({
                'Source': scanner_ip,
                'Destination': target,
                'Protocol': 6,
                'SrcPort': random.randint(10000, 65535),
                'DstPort': random.randint(1, 1000),
                'DataSize': random.randint(40, 200),
                'Duration': round(random.uniform(0.0001, 0.1), 6)
            })

    print(f'示例数据已生成: {file_path}')
    print(f'共生成 {num_sessions + 224 + 24} 条会话记录')


if __name__ == '__main__':
    generate_sample_data()
