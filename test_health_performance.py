#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试脚本 - 验证 /api/health 响应时间优化效果

使用方法：
1. 启动服务：hypercorn main:app --bind 0.0.0.0:8000
2. 运行此脚本：python test_health_performance.py
"""

import time
import requests
import statistics

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint: str, iterations: int = 10) -> dict:
    """
    测试指定端点的响应时间

    Args:
        endpoint: API端点路径
        iterations: 测试次数

    Returns:
        包含响应时间统计的字典
    """
    url = f"{BASE_URL}{endpoint}"
    response_times = []
    successes = 0
    failures = 0

    print(f"\n{'='*60}")
    print(f"测试端点: {endpoint}")
    print(f"测试次数: {iterations}")
    print(f"{'='*60}")

    for i in range(iterations):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()

            response_time_ms = (end_time - start_time) * 1000
            response_times.append(response_time_ms)

            if response.status_code == 200:
                successes += 1
                status = "✓"
            else:
                failures += 1
                status = "✗"

            print(f"  第 {i+1:2d} 次请求: {response_time_ms:7.2f}ms {status} (HTTP {response.status_code})")

        except requests.exceptions.RequestException as e:
            failures += 1
            print(f"  第 {i+1:2d} 次请求: 失败 ({str(e)[:50]})")
        except Exception as e:
            failures += 1
            print(f"  第 {i+1:2d} 次请求: 异常 ({str(e)[:50]})")

    # 计算统计信息
    if response_times:
        stats = {
            'endpoint': endpoint,
            'iterations': iterations,
            'successes': successes,
            'failures': failures,
            'avg_ms': statistics.mean(response_times),
            'median_ms': statistics.median(response_times),
            'min_ms': min(response_times),
            'max_ms': max(response_times),
            'p95_ms': sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 1 else max(response_times),
            'std_dev_ms': statistics.stdev(response_times) if len(response_times) > 1 else 0
        }
    else:
        stats = {
            'endpoint': endpoint,
            'iterations': iterations,
            'successes': successes,
            'failures': failures,
            'avg_ms': 0,
            'median_ms': 0,
            'min_ms': 0,
            'max_ms': 0,
            'p95_ms': 0,
            'std_dev_ms': 0
        }

    # 打印统计结果
    print(f"\n{'─'*60}")
    print(f"统计结果:")
    print(f"  成功率:     {successes}/{iterations} ({successes/iterations*100:.1f}%)")
    print(f"  平均响应:   {stats['avg_ms']:.2f}ms")
    print(f"  中位数:     {stats['median_ms']:.2f}ms")
    print(f"  最小值:     {stats['min_ms']:.2f}ms")
    print(f"  最大值:     {stats['max_ms']:.2f}ms")
    print(f"  P95:        {stats['p95_ms']:.2f}ms")
    print(f"  标准差:     {stats['std_dev_ms']:.2f}ms")
    print(f"{'='*60}\n")

    return stats


def main():
    """主函数 - 执行所有性能测试"""
    print("\n" + "="*60)
    print("  性能测试 - /api/health 响应时间验证")
    print("="*60)
    print(f"\n目标地址: {BASE_URL}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 测试1：基础健康检查（应该最快）
    health_stats = test_endpoint("/api/health", iterations=5)

    # 测试2：详细健康检查（会触发服务初始化）
    detailed_stats = test_endpoint("/api/health/detailed", iterations=3)

    # 对比分析
    print("\n" + "="*60)
    print("  优化效果对比")
    print("="*60)

    if health_stats['avg_ms'] > 0 and detailed_stats['avg_ms'] > 0:
        speedup = detailed_stats['avg_ms'] / health_stats['avg_ms']
        print(f"\n  /api/health (轻量级):")
        print(f"    平均响应时间: {health_stats['avg_ms']:.2f}ms")
        print(f"    目标: <100ms {'✓ 达标' if health_stats['avg_ms'] < 100 else '✗ 未达标'}")

        print(f"\n  /api/health/detailed (重量级):")
        print(f"    平均响应时间: {detailed_stats['avg_ms']:.2f}ms")
        print(f"    说明: 此接口会初始化所有服务，首次调用较慢")

        print(f"\n  性能提升:")
        print(f"    轻量级接口比重型快 {speedup:.1f} 倍")

        # 判断是否达标
        if health_stats['avg_ms'] < 100:
            print(f"\n  ✅ 优化成功！/api/health 响应时间已降至 {health_stats['avg_ms']:.2f}ms (< 100ms)")
        elif health_stats['avg_ms'] < 1000:
            print(f"\n  ⚠️  部分优化，/api/health 响应时间为 {health_stats['avg_ms']:.2f}ms (< 1s)")
        else:
            print(f"\n  ❌ 仍需优化，/api/health 响应时间为 {health_stats['avg_ms']:.2f}ms (> 1s)")
    else:
        print("\n  无法计算对比数据（测试失败）")

    print("\n" + "="*60 + "\n")

    # 返回测试结果供后续使用
    return {
        'health': health_stats,
        'detailed': detailed_stats
    }


if __name__ == "__main__":
    try:
        results = main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
