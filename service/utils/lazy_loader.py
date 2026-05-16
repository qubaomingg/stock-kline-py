"""
延迟加载器 - 解决 /api/health 响应慢的问题

核心原理：
1. 将重型模块的导入推迟到实际使用时
2. 避免在模块级别进行耗时操作（如数据库连接）
3. 使用单例模式懒加载
"""

from typing import Any, Callable, TypeVar, Optional
import functools
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LazyImport:
    """
    延迟导入装饰器/类

    使用方法：
    @LazyImport('module_name')
    def get_module():
        pass

    或者：
    module = LazyImport('module.path')
    # 实际使用时才导入: module.instance.method()
    """

    def __init__(self, module_path: str):
        self.module_path = module_path
        self._module = None
        self._import_time = None
        self._loaded = False

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            if not self._loaded:
                start_time = time.time()
                try:
                    import importlib
                    self._module = importlib.import_module(self.module_path)
                    self._loaded = True
                    self._import_time = time.time() - start_time
                    logger.info(f"延迟导入 {self.module_path} 耗时 {self._import_time:.2f}s")
                except ImportError as e:
                    logger.error(f"延迟导入失败 {self.module_path}: {e}")
                    raise
            return func(self._module, *args, **kwargs)
        return wrapper

    @property
    def instance(self):
        """获取实际导入的模块实例"""
        if not self._loaded:
            start_time = time.time()
            try:
                import importlib
                self._module = importlib.import_module(self.module_path)
                self._loaded = True
                self._import_time = time.time() - start_time
                logger.info(f"延迟导入 {self.module_path} 耗时 {self._import_time:.2f}s")
            except ImportError as e:
                logger.error(f"延迟导入失败 {self.module_path}: {e}")
                raise
        return self._module


class LazyService:
    """
    服务延迟初始化器

    用于将耗时的服务初始化（如数据库连接）推迟到首次使用时
    """

    def __init__(self, factory: Callable[[], T]):
        """
        Args:
            factory: 创建服务实例的工厂函数
        """
        self._factory = factory
        self._instance: Optional[T] = None
        self._initialized = False
        self._init_time = None

    @property
    def instance(self) -> T:
        """获取服务实例（首次访问时初始化）"""
        if not self._initialized:
            start_time = time.time()
            try:
                self._instance = self._factory()
                self._initialized = True
                self._init_time = time.time() - start_time
                logger.info(f"服务初始化完成，耗时 {self._init_time:.2f}s")
            except Exception as e:
                logger.error(f"服务初始化失败: {e}")
                raise
        return self._instance

    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized

    def reset(self):
        """重置服务（用于测试或重新初始化）"""
        self._instance = None
        self._initialized = False
        self._init_time = None


def lazy_import(module_path: str):
    """
    延迟导入装饰器 - 简化用法

    示例：
    @lazy_import('pandas')
    def use_pd(pd):
        return pd.DataFrame()

    用法：
    result = use_pd()  # 此时才真正导入pandas
    """
    return LazyImport(module_path)


# 全局服务注册表
_services = {}


def register_service(name: str, factory: Callable[[], Any]) -> LazyService:
    """
    注册一个延迟初始化的服务

    Args:
        name: 服务名称
        factory: 工厂函数

    Returns:
        LazyService实例
    """
    service = LazyService(factory)
    _services[name] = service
    return service


def get_service(name: str) -> Any:
    """
    获取已注册的服务实例

    Args:
        name: 服务名称

    Returns:
        服务实例
    """
    if name not in _services:
        raise ValueError(f"服务 '{name}' 未注册")
    return _services[name].instance


def get_all_service_stats() -> dict:
    """
    获取所有服务的统计信息（用于监控）

    Returns:
        包含各服务状态的字典
    """
    stats = {}
    for name, service in _services.items():
        stats[name] = {
            'initialized': service.is_initialized(),
            'init_time': service._init_time
        }
    return stats
