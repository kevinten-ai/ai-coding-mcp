"""
文档生成工具
自动生成代码文档
"""

from typing import Dict, List, Optional, Any

from .base_tool import BaseTool, ToolExecutionResult, ToolExecutionContext
from ..core.ai_analyzer import AIAnalyzer
from ..config import config


class DocGenerator(BaseTool):
    """
    文档生成工具

    提供自动化的文档生成功能：
    - 基于代码生成规范文档
    - 支持多种文档格式
    - 包含使用示例和注意事项
    """

    def __init__(self):
        super().__init__("doc_generator", "自动文档生成工具")
        self.ai_analyzer = AIAnalyzer()
        self.required_params = ["code", "language"]

    async def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated = await super().validate_params(params)

        format_type = params.get("format", "markdown").lower()
        if format_type not in self.tool_config.formats:
            raise ValueError(f"不支持的文档格式: {format_type}")

        return validated

    async def preprocess(self, params: Dict[str, Any],
                        context: ToolExecutionContext) -> Dict[str, Any]:
        """预处理参数"""
        language = params.get("language", "python").lower()
        format_type = params.get("format", "markdown").lower()

        return {
            **params,
            "language": language,
            "format": format_type
        }

    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> Dict[str, Any]:
        """核心执行逻辑"""
        code = params["code"]
        language = params["language"]
        format_type = params["format"]

        # 使用AI生成文档
        doc_result = await self.ai_analyzer.generate_documentation(
            code=code,
            language=language,
            format=format_type
        )

        # 后处理文档
        processed_docs = self._postprocess_documentation(
            doc_result["documentation"],
            format_type
        )

        return {
            "documentation": processed_docs,
            "language": language,
            "format": format_type,
            "source_code": code,
            "metadata": doc_result.get("usage", {})
        }

    def _postprocess_documentation(self, documentation: str, format_type: str) -> str:
        """后处理文档"""
        # 这里可以添加格式特定的优化
        return documentation

    async def postprocess(self, result: Dict[str, Any],
                         context: ToolExecutionContext) -> Dict[str, Any]:
        """后处理结果"""
        return result



