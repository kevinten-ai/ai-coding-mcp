"""
测试生成工具
自动生成单元测试
"""

from typing import Dict, List, Optional, Any

from .base_tool import BaseTool, ToolExecutionResult, ToolExecutionContext
from ..core.ai_analyzer import AIAnalyzer
from ..config import config


class TestGenerator(BaseTool):
    """
    测试生成工具

    提供自动化的测试生成功能：
    - 基于代码生成单元测试
    - 支持多种测试框架
    - 覆盖边界条件和异常情况
    """

    def __init__(self):
        super().__init__("test_generator", "自动测试生成工具")
        self.ai_analyzer = AIAnalyzer()
        self.required_params = ["code", "language"]

    async def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated = await super().validate_params(params)

        language = params.get("language", "").lower()
        framework = params.get("framework", "").lower()

        # 检查框架支持
        supported_frameworks = self.tool_config.frameworks.get(language, [])
        if framework and framework not in supported_frameworks:
            raise ValueError(f"不支持的测试框架: {framework} for {language}")

        return validated

    async def preprocess(self, params: Dict[str, Any],
                        context: ToolExecutionContext) -> Dict[str, Any]:
        """预处理参数"""
        language = params.get("language", "python").lower()
        framework = params.get("framework", self.tool_config.frameworks.get(language, ["unittest"])[0])

        return {
            **params,
            "language": language,
            "framework": framework
        }

    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> Dict[str, Any]:
        """核心执行逻辑"""
        code = params["code"]
        language = params["language"]
        framework = params["framework"]

        # 使用AI生成测试
        test_result = await self.ai_analyzer.generate_tests(
            function_code=code,
            language=language,
            framework=framework
        )

        # 后处理测试代码
        processed_tests = self._postprocess_test_code(
            test_result["test_code"],
            language,
            framework
        )

        return {
            "test_code": processed_tests,
            "language": language,
            "framework": framework,
            "target_code": code,
            "coverage_estimate": self._estimate_coverage(code, language),
            "metadata": test_result.get("usage", {})
        }

    def _postprocess_test_code(self, test_code: str, language: str, framework: str) -> str:
        """后处理测试代码"""
        # 这里可以添加框架特定的格式化和优化
        return test_code

    def _estimate_coverage(self, code: str, language: str) -> float:
        """估算测试覆盖率"""
        # 简化估算逻辑
        return 0.85  # 默认85%

    async def postprocess(self, result: Dict[str, Any],
                         context: ToolExecutionContext) -> Dict[str, Any]:
        """后处理结果"""
        return result



