"""
工具基类测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

from ..tools.base_tool import BaseTool, ToolExecutionResult, ToolExecutionContext


class MockTool(BaseTool):
    """模拟工具"""

    def __init__(self):
        super().__init__("mock_tool", "Mock tool for testing")
        self.execution_count = 0

    async def _execute_core(self, params, context):
        self.execution_count += 1
        return {"result": "success", "params": params}


class TestBaseTool:
    """工具基类测试"""

    @pytest.fixture
    def mock_tool(self):
        return MockTool()

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_tool):
        """测试成功执行"""
        params = {"test": "value"}
        result = await mock_tool.execute(params)

        assert result.success is True
        assert result.data == {"result": "success", "params": params}
        assert result.execution_time >= 0
        assert mock_tool.execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_validation_error(self, mock_tool):
        """测试参数验证失败"""
        mock_tool.required_params = ["missing_param"]

        result = await mock_tool.execute({})

        assert result.success is False
        assert "Missing required parameter" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, mock_tool):
        """测试超时处理"""
        mock_tool.tool_config.timeout = 0.001  # 很短的超时

        # Mock一个耗时操作
        original_execute = mock_tool._execute_core
        async def slow_execute(params, context):
            await asyncio.sleep(0.01)  # 超过超时时间
            return await original_execute(params, context)

        mock_tool._execute_core = slow_execute

        result = await mock_tool.execute({"test": "value"})

        assert result.success is False
        assert "timed out" in result.error.lower()

    def test_statistics(self, mock_tool):
        """测试统计信息"""
        stats = mock_tool.get_statistics()
        assert "execution_count" in stats
        assert "success_count" in stats
        assert "failure_count" in stats
        assert "average_execution_time" in stats



