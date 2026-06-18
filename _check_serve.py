import inspect
from prefect import flow
from prefect.schedules import Cron

# 查看 Flow.serve 签名
@flow
def test_flow():
    pass

print("=== Flow.serve 签名 ===")
sig = inspect.signature(test_flow.serve)
print(sig)
print()

# 查看 runner.add_flow 签名
from prefect.runner.runner import Runner
print("=== Runner.add_flow 签名 ===")
sig2 = inspect.signature(Runner.add_flow)
print(sig2)

# 看 runner.serve 签名
print("\n=== Runner.serve 签名 ===")
sig3 = inspect.signature(Runner.serve)
print(sig3)

# 看 deployment apply signature
from prefect.runner.runner import RunnerDeployment
print("\n=== RunnerDeployment 初始化 ===")
sig4 = inspect.signature(RunnerDeployment.__init__)
print(sig4)
