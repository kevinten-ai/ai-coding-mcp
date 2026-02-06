"""
MCP工具抽象基类
提供统一的工具执行接口和生命周期管理
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum

from ..config import config


class ToolExecutionStatus(Enum):
    """工具执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolExecutionContext:
    """工具执行上下文"""
    tool_name: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: Optional[float] = None
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T')


class BaseTool(ABC, Generic[T]):
    """
    MCP工具抽象基类

    提供统一的工具执行生命周期：
    1. 参数验证 (validate_params)
    2. 预处理 (preprocess)
    3. 核心执行 (_execute_core)
    4. 后处理 (postprocess)
    5. 错误处理 (handle_error)
    """

    def __init__(self, name: str, description: str = ""):
        """
        初始化工具

        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
        self._execution_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._total_execution_time = 0.0

    @property
    def tool_config(self) -> Any:
        """获取工具配置"""
        # 子类可以重写此方法来返回特定的配置对象
        return getattr(config, self.name.replace('-', '_'), None)

    async def execute(self, params: Dict[str, Any],
                     context: Optional[ToolExecutionContext] = None) -> ToolExecutionResult:
        """
        执行工具的主入口

        Args:
            params: 工具参数
            context: 执行上下文

        Returns:
            ToolExecutionResult: 执行结果
        """
        start_time = time.time()

        # 创建执行上下文
        if context is None:
            context = ToolExecutionContext(
                tool_name=self.name,
                parameters=params,
                start_time=start_time,
                timeout=self.tool_config.timeout if self.tool_config else 30
            )

        try:
            # 参数验证
            validated_params = await self.validate_params(params)

            # 预处理
            processed_params = await self.preprocess(validated_params, context)

            # 核心执行（带超时控制）
            if context.timeout:
                result = await asyncio.wait_for(
                    self._execute_core(processed_params, context),
                    timeout=context.timeout
                )
            else:
                result = await self._execute_core(processed_params, context)

            # 后处理
            final_result = await self.postprocess(result, context)

            # 更新统计信息
            execution_time = time.time() - start_time
            self._update_statistics(success=True, execution_time=execution_time)

            return ToolExecutionResult(
                success=True,
                data=final_result,
                execution_time=execution_time,
                metadata={
                    "tool_name": self.name,
                    "execution_count": self._execution_count
                }
            )

        except asyncio.TimeoutError:
            error_msg = f"Tool execution timed out after {context.timeout} seconds"
            self._update_statistics(success=False, execution_time=time.time() - start_time)
            return await self.handle_error(params, TimeoutError(error_msg), context)

        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            self._update_statistics(success=False, execution_time=time.time() - start_time)
            return await self.handle_error(params, e, context)

    async def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        参数验证

        Args:
            params: 原始参数

        Returns:
            Dict[str, Any]: 验证后的参数

        Raises:
            ValueError: 参数验证失败
        """
        # 默认实现：检查必需参数
        required_params = getattr(self, 'required_params', [])
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        return params

    async def preprocess(self, params: Dict[str, Any],
                        context: ToolExecutionContext) -> Dict[str, Any]:
        """
        预处理参数

        Args:
            params: 验证后的参数
            context: 执行上下文

        Returns:
            Dict[str, Any]: 处理后的参数
        """
        # 默认实现：直接返回参数
        return params

    @abstractmethod
    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> T:
        """
        核心执行逻辑（子类必须实现）

        Args:
            params: 处理后的参数
            context: 执行上下文

        Returns:
            T: 执行结果
        """
        pass

    async def postprocess(self, result: T,
                         context: ToolExecutionContext) -> Any:
        """
        后处理结果

        Args:
            result: 核心执行结果
            context: 执行上下文

        Returns:
            Any: 最终结果
        """
        # 默认实现：直接返回结果
        return result

    async def handle_error(self, params: Dict[str, Any], error: Exception,
                          context: ToolExecutionContext) -> ToolExecutionResult:
        """
        错误处理

        Args:
            params: 原始参数
            error: 异常对象
            context: 执行上下文

        Returns:
            ToolExecutionResult: 错误结果
        """
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Tool {self.name} execution failed: {str(error)}",
                    extra={"tool": self.name, "params": params, "error": str(error)})

        # 返回错误结果
        return ToolExecutionResult(
            success=False,
            error=str(error),
            execution_time=time.time() - (context.start_time or time.time()),
            metadata={
                "tool_name": self.name,
                "error_type": type(error).__name__
            }
        )

    def _update_statistics(self, success: bool, execution_time: float):
        """更新执行统计信息"""
        self._execution_count += 1
        self._total_execution_time += execution_time

        if success:
            self._success_count += 1
        else:
            self._failure_count += 1

    def get_statistics(self) -> Dict[str, Any]:
        """获取工具执行统计信息"""
        return {
            "tool_name": self.name,
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "success_rate": self._success_count / max(self._execution_count, 1),
            "average_execution_time": self._total_execution_time / max(self._execution_count, 1)
        }

    def cancel(self):
        """取消工具执行（如果支持）"""
        # 默认实现：不支持取消
        pass

    def cleanup(self):
        """清理资源"""
        # 默认实现：无资源需要清理
        pass

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        return self.__str__()


class AsyncToolMixin:
    """
    异步工具混入类
    为不支持异步的工具提供适配器
    """

    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> T:
        """异步包装器"""
        # 在线程池中执行同步方法
        import concurrent.futures
        import functools

        loop = asyncio.get_event_loop()
        func = functools.partial(self._execute_sync, params, context)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func)

    @abstractmethod
    def _execute_sync(self, params: Dict[str, Any],
                     context: ToolExecutionContext) -> T:
        """同步执行方法（子类实现）"""
        pass



