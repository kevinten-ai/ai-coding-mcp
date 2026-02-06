"""
数据获取器
统一管理对外部MCP服务的调用和数据聚合
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time

from ..config import config


@dataclass
class FetchRequest:
    """数据获取请求"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None
    timeout: Optional[float] = None
    retries: int = 3


@dataclass
class FetchResult:
    """数据获取结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    response_time: float = 0.0
    metadata: Dict[str, Any] = None


class ConnectionPool:
    """连接池管理"""

    def __init__(self, max_connections: int = 10, timeout: float = 30.0):
        self.max_connections = max_connections
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections // 2,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True  # 使用环境变量中的代理设置
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("ConnectionPool not initialized")
        return self._session


class DataFetcher:
    """
    数据获取器

    提供高效的数据获取和聚合能力：
    - 连接池管理避免资源泄漏
    - 并发调用提升数据获取效率
    - 完善的错误处理和降级机制
    """

    def __init__(self):
        self.connection_pool = ConnectionPool(
            max_connections=config.server.workers * 2,
            timeout=config.ai.timeout
        )
        self._rate_limiter = asyncio.Semaphore(config.security.rate_limit_requests)
        self._active_requests = 0

    async def __aenter__(self):
        await self.connection_pool.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection_pool.__aexit__(exc_type, exc_val, exc_tb)

    async def fetch_single(self, request: FetchRequest) -> FetchResult:
        """
        获取单个数据

        Args:
            request: 获取请求

        Returns:
            FetchResult: 获取结果
        """
        start_time = time.time()

        try:
            # 速率限制
            await self._rate_limiter.acquire()

            async with self.connection_pool.session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                params=request.params,
                data=request.data,
                timeout=aiohttp.ClientTimeout(total=request.timeout or config.ai.timeout)
            ) as response:
                self._active_requests += 1

                # 检查响应状态
                if response.status >= 400:
                    error_msg = f"HTTP {response.status}: {response.reason}"
                    return FetchResult(
                        success=False,
                        error=error_msg,
                        status_code=response.status,
                        response_time=time.time() - start_time
                    )

                # 解析响应数据
                content_type = response.headers.get('Content-Type', '').lower()

                if 'application/json' in content_type:
                    data = await response.json()
                elif 'text/' in content_type:
                    data = await response.text()
                else:
                    data = await response.read()

                return FetchResult(
                    success=True,
                    data=data,
                    status_code=response.status,
                    response_time=time.time() - start_time,
                    metadata={
                        "content_type": content_type,
                        "headers": dict(response.headers)
                    }
                )

        except asyncio.TimeoutError:
            return FetchResult(
                success=False,
                error="Request timeout",
                response_time=time.time() - start_time
            )

        except aiohttp.ClientError as e:
            return FetchResult(
                success=False,
                error=f"Client error: {str(e)}",
                response_time=time.time() - start_time
            )

        except Exception as e:
            return FetchResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                response_time=time.time() - start_time
            )

        finally:
            self._rate_limiter.release()
            self._active_requests = max(0, self._active_requests - 1)

    async def fetch_multiple(self, requests: List[FetchRequest],
                           concurrency_limit: Optional[int] = None) -> List[FetchResult]:
        """
        并发获取多个数据

        Args:
            requests: 获取请求列表
            concurrency_limit: 并发限制

        Returns:
            List[FetchResult]: 获取结果列表
        """
        if concurrency_limit is None:
            concurrency_limit = config.code_analyzer.max_concurrent

        semaphore = asyncio.Semaphore(concurrency_limit)

        async def fetch_with_semaphore(request: FetchRequest) -> FetchResult:
            async with semaphore:
                return await self.fetch_single(request)

        # 创建并发任务
        tasks = [fetch_with_semaphore(req) for req in requests]

        # 执行并发请求
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(FetchResult(
                    success=False,
                    error=f"Task failed: {str(result)}",
                    metadata={"request_index": i}
                ))
            else:
                final_results.append(result)

        return final_results

    async def fetch_mcp_service(self, service_url: str,
                               tool_name: str,
                               params: Dict[str, Any]) -> FetchResult:
        """
        调用MCP服务

        Args:
            service_url: 服务URL
            tool_name: 工具名称
            params: 参数

        Returns:
            FetchResult: 调用结果
        """
        request = FetchRequest(
            url=urljoin(service_url, f"/tools/{tool_name}"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.ai.api_key}"
            },
            data=json.dumps(params),
            timeout=config.ai.timeout
        )

        return await self.fetch_single(request)

    async def aggregate_data(self, sources: List[Dict[str, Any]],
                           aggregation_strategy: str = "merge") -> Dict[str, Any]:
        """
        数据聚合

        Args:
            sources: 数据源配置列表
            aggregation_strategy: 聚合策略 ("merge", "concat", "average")

        Returns:
            Dict[str, Any]: 聚合后的数据
        """
        if not sources:
            return {}

        # 并发获取所有数据源
        requests = []
        for source in sources:
            request = FetchRequest(
                url=source["url"],
                method=source.get("method", "GET"),
                headers=source.get("headers"),
                params=source.get("params"),
                timeout=source.get("timeout", config.ai.timeout)
            )
            requests.append(request)

        results = await self.fetch_multiple(requests)

        # 根据策略聚合数据
        valid_results = [r for r in results if r.success]

        if not valid_results:
            return {"error": "No valid data sources", "results": results}

        if aggregation_strategy == "merge":
            return self._merge_results(valid_results)
        elif aggregation_strategy == "concat":
            return self._concat_results(valid_results)
        elif aggregation_strategy == "average":
            return self._average_results(valid_results)
        else:
            return {"error": f"Unknown aggregation strategy: {aggregation_strategy}"}

    def _merge_results(self, results: List[FetchResult]) -> Dict[str, Any]:
        """合并结果"""
        merged = {}
        for result in results:
            if isinstance(result.data, dict):
                merged.update(result.data)
            else:
                # 为非字典数据创建键
                key = f"data_{len(merged)}"
                merged[key] = result.data

        return {
            "aggregated_data": merged,
            "source_count": len(results),
            "aggregation_strategy": "merge"
        }

    def _concat_results(self, results: List[FetchResult]) -> Dict[str, Any]:
        """连接结果"""
        concatenated = []
        for result in results:
            if isinstance(result.data, list):
                concatenated.extend(result.data)
            else:
                concatenated.append(result.data)

        return {
            "aggregated_data": concatenated,
            "source_count": len(results),
            "aggregation_strategy": "concat"
        }

    def _average_results(self, results: List[FetchResult]) -> Dict[str, Any]:
        """平均结果（适用于数值数据）"""
        numeric_values = []
        for result in results:
            if isinstance(result.data, (int, float)):
                numeric_values.append(result.data)

        if not numeric_values:
            return {"error": "No numeric data to average"}

        average = sum(numeric_values) / len(numeric_values)

        return {
            "aggregated_data": average,
            "source_count": len(results),
            "numeric_sources": len(numeric_values),
            "aggregation_strategy": "average"
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "active_requests": self._active_requests,
            "rate_limiter_available": self._rate_limiter._value,
            "connection_pool_active": self.connection_pool._session is not None
        }



