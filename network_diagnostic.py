#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络诊断工具 - 分析访问延迟的各个组成部分

使用方法：
    python network_diagnostic.py [URL]

示例：
    python network_diagnostic.py https://kline.lanren.site/api/health
"""

import time
import socket
import requests
import statistics
from datetime import datetime
from urllib.parse import urlparse
import sys


class NetworkDiagnostic:
    """网络诊断工具类"""

    def __init__(self, url: str):
        self.url = url
        self.parsed_url = urlparse(url)
        self.hostname = self.parsed_url.hostname
        self.results = {}

    def test_dns_resolution(self) -> dict:
        """
        测试DNS解析时间

        Returns:
            DNS解析结果字典
        """
        print(f"\n{'='*60}")
        print("1️⃣  DNS解析测试")
        print(f"{'='*60}")
        print(f"域名: {self.hostname}")

        results = []
        resolved_ips = []

        for i in range(3):
            try:
                start_time = time.time()
                ip_address = socket.gethostbyname(self.hostname)
                end_time = time.time()

                resolve_time_ms = (end_time - start_time) * 1000
                results.append(resolve_time_ms)
                resolved_ips.append(ip_address)

                print(f"  第 {i+1} 次解析: {resolve_time_ms:.2f}ms → {ip_address}")

            except socket.gaierror as e:
                print(f"  第 {i+1} 次解析: 失败 - {e}")
                results.append(None)

        if results and any(r is not None for r in results):
            valid_results = [r for r in results if r is not None]
            result = {
                'test': 'DNS Resolution',
                'hostname': self.hostname,
                'resolved_ips': list(set(resolved_ips)),
                'avg_ms': statistics.mean(valid_results),
                'min_ms': min(valid_results),
                'max_ms': max(valid_results),
                'status': '✅ 正常' if statistics.mean(valid_results) < 100 else '⚠️ 较慢'
            }
        else:
            result = {
                'test': 'DNS Resolution',
                'hostname': self.hostname,
                'resolved_ips': [],
                'avg_ms': float('inf'),
                'min_ms': float('inf'),
                'max_ms': float('inf'),
                'status': '❌ 解析失败'
            }

        print(f"\n  统计:")
        print(f"    平均: {result['avg_ms']:.2f}ms")
        print(f"    范围: {result['min_ms']:.2f}ms - {result['max_ms']:.2f}ms")
        print(f"    解析到IP: {', '.join(result['resolved_ips'][:3])}")
        print(f"    状态: {result['status']}")

        self.results['dns'] = result
        return result

    def test_tcp_connection(self, port: int = 443) -> dict:
        """
        测试TCP连接时间

        Args:
            port: 端口号（默认443）

        Returns:
            TCP连接结果字典
        """
        print(f"\n{'='*60}")
        print("2️⃣  TCP连接测试")
        print(f"{'='*60}")
        print(f"目标: {self.hostname}:{port}")

        results = []

        for i in range(5):
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                sock.connect((self.hostname, port))
                end_time = time.time()

                connect_time_ms = (end_time - start_time) * 1000
                results.append(connect_time_ms)
                sock.close()

                print(f"  第 {i+1} 次连接: {connect_time_ms:.2f}ms")

            except socket.timeout:
                print(f"  第 {i+1} 次连接: 超时 (>10s)")
                results.append(10000)
            except Exception as e:
                print(f"  第 {i+1} 次连接: 失败 - {e}")
                results.append(None)

        if results and any(r is not None and r != 10000 for r in results):
            valid_results = [r for r in results if r is not None and r != 10000]
            result = {
                'test': 'TCP Connection',
                'target': f"{self.hostname}:{port}",
                'avg_ms': statistics.mean(valid_results),
                'min_ms': min(valid_results),
                'max_ms': max(valid_results),
                'status': '✅ 正常' if statistics.mean(valid_results) < 500 else '⚠️ 较慢'
            }
        else:
            result = {
                'test': 'TCP Connection',
                'target': f"{self.hostname}:{port}",
                'avg_ms': float('inf'),
                'min_ms': float('inf'),
                'max_ms': float('inf'),
                'status': '❌ 连接失败'
            }

        print(f"\n  统计:")
        print(f"    平均: {result['avg_ms']:.2f}ms")
        print(f"    范围: {result['min_ms']:.2f}ms - {result['max_ms']:.2f}ms")
        print(f"    状态: {result['status']}")

        # 判断服务器地理位置
        if result['avg_ms'] < 50:
            location_guess = "🇨🇳 国内或邻近地区"
        elif result['avg_ms'] < 150:
            location_guess = "🌏 亚太地区"
        elif result['avg_ms'] < 300:
            location_guess = "🇺🇸 美国西海岸"
        elif result['avg_ms'] < 500:
            location_guess = "🇺🇸 美国东海岸/欧洲"
        else:
            location_guess = "🌍 远距离或网络拥堵"

        print(f"    推测位置: {location_guess}")

        self.results['tcp'] = result
        return result

    def test_http_response(self, iterations: int = 10) -> dict:
        """
        测试HTTP响应时间

        Args:
            iterations: 测试次数

        Returns:
            HTTP响应结果字典
        """
        print(f"\n{'='*60}")
        print("3️⃣  HTTP响应测试")
        print(f"{'='*60}")
        print(f"URL: {self.url}")
        print(f"次数: {iterations}")

        response_times = []
        status_codes = []
        response_sizes = []

        headers = {
            'User-Agent': 'NetworkDiagnostic/1.0',
            'Accept': 'application/json'
        }

        for i in range(iterations):
            try:
                start_time = time.time()
                response = requests.get(self.url, headers=headers, timeout=30)
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                status_codes.append(response.status_code)
                response_sizes.append(len(response.content))

                status_icon = "✓" if response.status_code == 200 else "✗"
                print(f"  第 {i+1:2d} 次: {response_time_ms:7.2f}ms "
                      f"{status_icon} HTTP {response.status_code} "
                      f"({len(response.content)} bytes)")

            except requests.exceptions.Timeout:
                print(f"  第 {i+1:2d} 次: 超时 (>30s)")
                response_times.append(30000)
                status_codes.append(None)
            except Exception as e:
                print(f"  第 {i+1:2d} 次: 错误 - {str(e)[:50]}")
                response_times.append(None)
                status_codes.append(None)

        valid_results = [r for r in response_times if r is not None and r != 30000]

        if valid_results:
            sorted_times = sorted(valid_results)
            p95_idx = int(len(sorted_times) * 0.95)

            result = {
                'test': 'HTTP Response',
                'url': self.url,
                'iterations': iterations,
                'successes': len(valid_results),
                'failures': iterations - len(valid_results),
                'avg_ms': statistics.mean(valid_results),
                'median_ms': statistics.median(valid_results),
                'min_ms': min(valid_results),
                'max_ms': max(valid_results),
                'p95_ms': sorted_times[p95_idx] if p95_idx > 0 else max(valid_results),
                'p99_ms': sorted_times[min(int(len(sorted_times) * 0.99), len(sorted_times)-1)],
                'std_dev_ms': statistics.stdev(valid_results) if len(valid_results) > 1 else 0,
                'avg_size_bytes': statistics.mean(response_sizes) if response_sizes else 0
            }
        else:
            result = {
                'test': 'HTTP Response',
                'url': self.url,
                'iterations': iterations,
                'successes': 0,
                'failures': iterations,
                'avg_ms': float('inf'),
                'median_ms': float('inf'),
                'min_ms': float('inf'),
                'max_ms': float('inf'),
                'p95_ms': float('inf'),
                'p99_ms': float('inf'),
                'std_dev_ms': 0,
                'avg_size_bytes': 0
            }

        print(f"\n  统计结果:")
        print(f"    成功率:     {result['successes']}/{result['iterations']} "
              f"({result['successes']/result['iterations']*100:.1f}%)")
        print(f"    平均响应:   {result['avg_ms']:.2f}ms")
        print(f"    中位数:     {result['median_ms']:.2f}ms")
        print(f"    最小值:     {result['min_ms']:.2f}ms")
        print(f"    最大值:     {result['max_ms']:.2f}ms")
        print(f"    P95:        {result['p95_ms']:.2f}ms")
        print(f"    P99:        {result['p99_ms']:.2f}ms")
        print(f"    标准差:     {result['std_dev_ms']:.2f}ms")
        print(f"    平均大小:   {result['avg_size_bytes']:.0f} bytes")

        # 性能评级
        if result['avg_ms'] < 100:
            rating = "⚡ 极快 (<100ms)"
        elif result['avg_ms'] < 500:
            rating = "✅ 快速 (100-500ms)"
        elif result['avg_ms'] < 1000:
            rating = "⚠️ 一般 (500ms-1s)"
        elif result['avg_ms'] < 5000:
            rating = "❌ 较慢 (1-5s)"
        elif result['avg_ms'] < 30000:
            rating = "💀 很慢 (5-30s)"
        else:
            rating = "☠️ 不可接受 (>30s)"

        print(f"    性能评级:   {rating}")

        self.results['http'] = result
        return result

    def analyze_bottleneck(self) -> dict:
        """
        分析性能瓶颈

        Returns:
            瓶颈分析结果
        """
        print(f"\n{'='*60}")
        print("🔍  瓶颈分析")
        print(f"{'='*60}")

        bottlenecks = []
        total_estimated = 0

        # DNS分析
        if 'dns' in self.results:
            dns = self.results['dns']
            if dns['avg_ms'] > 100:
                bottlenecks.append({
                    'component': 'DNS解析',
                    'time_ms': dns['avg_ms'],
                    'severity': '⚠️ 高' if dns['avg_ms'] > 500 else '⚡ 中',
                    'recommendation': '使用更快的DNS或添加本地缓存'
                })
                total_estimated += dns['avg_ms']

        # TCP分析
        if 'tcp' in self.results:
            tcp = self.results['tcp']
            if tcp['avg_ms'] > 200:
                bottlenecks.append({
                    'component': '网络连接',
                    'time_ms': tcp['avg_ms'],
                    'severity': '🔴 高' if tcp['avg_ms'] > 500 else '⚠️ 中',
                    'recommendation': '服务器距离过远，考虑使用CDN或更换部署区域'
                })
                total_estimated += tcp['avg_ms']

        # HTTP分析
        if 'http' in self.results:
            http = self.results['http']
            server_time = http['avg_ms']

            if 'tcp' in self.results:
                server_time -= self.results['tcp']['avg_ms']
            if 'dns' in self.results:
                server_time -= self.results['dns']['avg_ms']

            server_time = max(server_time, 0)

            if server_time > 1000:
                bottlenecks.append({
                    'component': '服务器处理',
                    'time_ms': server_time,
                    'severity': '💀 高' if server_time > 10000 else '🔴 中',
                    'recommendation': '应用冷启动慢或代码效率低，需优化启动流程'
                })
                total_estimated += server_time

        # 输出分析结果
        print(f"\n  发现 {len(bottlenecks)} 个性能瓶颈:\n")

        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"  {i}. {bottleneck['component']}")
            print(f"     耗时: ~{bottleneck['time_ms']:.0f}ms ({bottleneck['severity']})")
            print(f"     建议: {bottleneck['recommendation']}\n")

        print(f"  预估总耗时: {total_estimated:.0f}ms ({total_estimated/1000:.1f}s)")

        # 根本原因判断
        print(f"\n  🎯 根本原因判断:")

        has_network_issue = any(b['component'] in ['DNS解析', '网络连接'] for b in bottlenecks)
        has_server_issue = any(b['component'] == '服务器处理' for b in bottlenecks)

        if has_network_issue and has_server_issue:
            root_cause = "🔴 网络 + 服务器双重问题（主要问题是网络）"
            solution_priority = "1. 使用CDN 2. 更换部署区域 3. 优化代码"
        elif has_network_issue:
            root_cause = "🔴 网络问题（服务器在国外或DNS慢）"
            solution_priority = "1. 使用CDN 2. 更换到亚太区域 3. 使用国内服务器"
        elif has_server_issue:
            root_cause = "🟠 服务器问题（冷启动慢或代码效率低）"
            solution_priority = "1. 优化启动流程 2. 预热容器 3. 升级硬件"
        else:
            root_cause = "🟢 性能正常"
            solution_priority = "无需特殊优化"

        print(f"     {root_cause}")
        print(f"\n  📋 解决方案优先级:")
        print(f"     {solution_priority}")

        analysis_result = {
            'bottlenecks': bottlenecks,
            'total_estimated_ms': total_estimated,
            'root_cause': root_cause,
            'solution_priority': solution_priority
        }

        self.results['analysis'] = analysis_result
        return analysis_result

    def generate_report(self) -> str:
        """
        生成诊断报告

        Returns:
            Markdown格式的报告字符串
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report = f"""
# 网络诊断报告

**生成时间**: {timestamp}
**目标地址**: {self.url}

---

## 测试结果摘要

| 测试项 | 平均耗时 | 状态 |
|--------|----------|------|
"""

        if 'dns' in self.results:
            report += f"| DNS解析 | {self.results['dns']['avg_ms']:.2f}ms | {self.results['dns']['status']} |\n"

        if 'tcp' in self.results:
            report += f"| TCP连接 | {self.results['tcp']['avg_ms']:.2f}ms | {self.results['tcp']['status']} |\n"

        if 'http' in self.results:
            http = self.results['http']
            report += f"| HTTP响应 | {http['avg_ms']:.2f}ms | P95: {http['p95_ms']:.2f}ms |\n"

        if 'analysis' in self.results:
            analysis = self.results['analysis']
            report += f"""
---

## 瓶颈分析

### 发现的问题

"""
            for i, bottleneck in enumerate(analysis['bottlenecks'], 1):
                report += f"""{i}. **{bottleneck['component']}** (~{bottleneck['time_ms']:.0f}ms)
   - 严重程度: {bottleneck['severity']}
   - 建议: {bottleneck['recommendation']}

"""

            report += f"""
### 根本原因

{analysis['root_cause']}

### 建议方案

{analysis['solution_priority']}

---

## 详细数据

"""
            if 'http' in self.results:
                http = self.results['http']
                report += f"""**HTTP响应统计**:
- 测试次数: {http['iterations']}
- 成功率: {http['successes']}/{http['iterations']} ({http['successes']/http['iterations']*100:.1f}%)
- 平均值: {http['avg_ms']:.2f}ms
- 中位数: {http['median_ms']:.2f}ms
- 最小值: {http['min_ms']:.2f}ms
- 最大值: {http['max_ms']:.2f}ms
- P95: {http['p95_ms']:.2f}ms
- P99: {http['p99_ms']:.2f}ms
- 标准差: {http['std_dev_ms']:.2f}ms

"""

        report += "---\n*报告由 NetworkDiagnostic 工具自动生成*\n"

        return report

    def run_full_diagnostic(self) -> dict:
        """
        运行完整诊断

        Returns:
            完整的诊断结果
        """
        print("\n" + "="*60)
        print("  🔍 网络诊断工具")
        print("="*60)
        print(f"\n目标: {self.url}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 运行各项测试
        self.test_dns_resolution()
        self.test_tcp_connection()
        self.test_http_response(iterations=5)
        self.analyze_bottleneck()

        # 生成报告
        report = self.generate_report()

        # 保存报告
        report_filename = f"network_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n{'='*60}")
        print("📊  诊断完成")
        print(f"{'='*60}")
        print(f"\n报告已保存到: {report_filename}")

        return self.results


def main():
    """主函数"""
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://kline.lanren.site/api/health"

    diagnostic = NetworkDiagnostic(url)

    try:
        results = diagnostic.run_full_diagnostic()

        # 返回退出码（用于CI/CD）
        if 'http' in results and results['http']['avg_ms'] < 1000:
            return 0  # 成功
        else:
            return 1  # 性能不达标

    except KeyboardInterrupt:
        print("\n\n诊断被用户中断")
        return 130
    except Exception as e:
        print(f"\n\n诊断出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
