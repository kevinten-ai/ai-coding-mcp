"""
代码分析工具
提供代码库深度分析功能
"""

import ast
import re
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict, Counter
import math

from .base_tool import BaseTool, ToolExecutionResult, ToolExecutionContext
from ..core.ai_analyzer import AIAnalyzer
from ..core.data_storage import DataStorage
from ..config import config


class CodeMetrics:
    """代码度量指标"""

    def __init__(self):
        self.loc = 0  # 代码行数
        self.sloc = 0  # 有效代码行数
        self.complexity = 0  # 圈复杂度
        self.functions = 0  # 函数数量
        self.classes = 0  # 类数量
        self.comments = 0  # 注释行数
        self.blank_lines = 0  # 空行数
        self.imports = 0  # 导入语句数
        self.duplicate_lines = 0  # 重复行数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "lines_of_code": self.loc,
            "source_lines_of_code": self.sloc,
            "cyclomatic_complexity": self.complexity,
            "function_count": self.functions,
            "class_count": self.classes,
            "comment_lines": self.comments,
            "blank_lines": self.blank_lines,
            "import_count": self.imports,
            "duplicate_lines": self.duplicate_lines,
            "comment_ratio": self.comments / max(self.sloc, 1),
            "complexity_per_function": self.complexity / max(self.functions, 1)
        }


class CodeAnalyzer(BaseTool):
    """
    代码分析工具

    提供全面的代码分析功能：
    - 代码度量统计
    - 依赖关系分析
    - 代码质量评估
    - 潜在问题识别
    """

    def __init__(self):
        super().__init__("code_analyzer", "代码分析和质量评估工具")
        self.ai_analyzer = AIAnalyzer()
        self.data_storage = DataStorage()
        self.required_params = ["code"]

    async def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated = await super().validate_params(params)

        # 检查代码长度
        code = params.get("code", "")
        if len(code) > self.tool_config.max_file_size:
            raise ValueError(f"代码长度超过限制: {len(code)} > {self.tool_config.max_file_size}")

        # 检查语言
        language = params.get("language", "python").lower()
        if language not in self.tool_config.languages:
            raise ValueError(f"不支持的语言: {language}")

        return validated

    async def preprocess(self, params: Dict[str, Any],
                        context: ToolExecutionContext) -> Dict[str, Any]:
        """预处理参数"""
        # 提取语言信息
        language = params.get("language", "python").lower()

        # 标准化分析类型
        analysis_type = params.get("analysis_type", "general")
        valid_types = ["general", "security", "performance", "quality"]
        if analysis_type not in valid_types:
            analysis_type = "general"

        return {
            **params,
            "language": language,
            "analysis_type": analysis_type
        }

    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> Dict[str, Any]:
        """核心执行逻辑"""
        code = params["code"]
        language = params["language"]
        analysis_type = params["analysis_type"]

        # 基础代码分析
        basic_analysis = await self._analyze_basic_metrics(code, language)

        # 高级AI分析
        ai_analysis = await self.ai_analyzer.analyze_code(
            code=code,
            language=language,
            analysis_type=analysis_type
        )

        # 依赖分析
        dependencies = await self._analyze_dependencies(code, language)

        # 质量评估
        quality_score = await self._calculate_quality_score(basic_analysis, ai_analysis)

        # 生成建议
        recommendations = await self._generate_recommendations(
            basic_analysis, ai_analysis, language
        )

        return {
            "basic_metrics": basic_analysis.to_dict(),
            "ai_analysis": ai_analysis,
            "dependencies": dependencies,
            "quality_score": quality_score,
            "recommendations": recommendations,
            "language": language,
            "analysis_type": analysis_type
        }

    async def _analyze_basic_metrics(self, code: str, language: str) -> CodeMetrics:
        """分析基础代码度量"""
        metrics = CodeMetrics()

        lines = code.split('\n')
        metrics.loc = len(lines)

        # 分析每一行
        for line in lines:
            stripped = line.strip()

            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith('#') or '"""' in line or "'''" in line:
                metrics.comments += 1
            elif stripped.startswith(('import ', 'from ')):
                metrics.imports += 1
            else:
                metrics.sloc += 1

        # 语言特定的分析
        if language == "python":
            metrics.complexity = self._calculate_python_complexity(code)
            metrics.functions = self._count_python_functions(code)
            metrics.classes = self._count_python_classes(code)
        else:
            # 其他语言的基础估算
            metrics.complexity = max(1, metrics.sloc // 10)
            metrics.functions = len(re.findall(r'\bfunction\b|\bdef\b|\bfunc\b', code))
            metrics.classes = len(re.findall(r'\bclass\b', code))

        # 检测重复代码（简单实现）
        metrics.duplicate_lines = self._detect_duplicate_lines(lines)

        return metrics

    def _calculate_python_complexity(self, code: str) -> int:
        """计算Python代码的圈复杂度"""
        try:
            tree = ast.parse(code)
            complexity = 1  # 基础复杂度

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except SyntaxError:
            return 1

    def _count_python_functions(self, code: str) -> int:
        """统计Python函数数量"""
        try:
            tree = ast.parse(code)
            return sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        except SyntaxError:
            return 0

    def _count_python_classes(self, code: str) -> int:
        """统计Python类数量"""
        try:
            tree = ast.parse(code)
            return sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        except SyntaxError:
            return 0

    def _detect_duplicate_lines(self, lines: List[str]) -> int:
        """检测重复行数"""
        line_counts = Counter(line.strip() for line in lines if line.strip())
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        return duplicate_lines

    async def _analyze_dependencies(self, code: str, language: str) -> Dict[str, Any]:
        """分析代码依赖"""
        dependencies = {
            "imports": [],
            "external_libraries": [],
            "internal_modules": [],
            "circular_dependencies": []
        }

        if language == "python":
            # 提取import语句
            import_pattern = r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))'
            matches = re.findall(import_pattern, code, re.MULTILINE)

            for match in matches:
                module = match[0] or match[1]
                dependencies["imports"].append(module)

                # 分类依赖
                if '.' in module:
                    parts = module.split('.')
                    if parts[0] in ['django', 'flask', 'fastapi', 'requests', 'pandas', 'numpy', 'matplotlib']:
                        dependencies["external_libraries"].append(module)
                    else:
                        dependencies["internal_modules"].append(module)
                else:
                    if module in ['os', 'sys', 'json', 'datetime', 're', 'math']:
                        pass  # 标准库
                    else:
                        dependencies["external_libraries"].append(module)

        return dependencies

    async def _calculate_quality_score(self, metrics: CodeMetrics,
                                     ai_analysis: Dict[str, Any]) -> float:
        """计算代码质量评分（0-100）"""
        score = 100.0

        # 基于基础度量的扣分
        if metrics.comment_ratio < 0.1:
            score -= 20  # 注释不足
        elif metrics.comment_ratio > 0.5:
            score -= 5   # 注释过多

        if metrics.complexity_per_function > 10:
            score -= 15  # 复杂度过高

        if metrics.duplicate_lines > metrics.sloc * 0.1:
            score -= 10  # 重复代码过多

        # 基于AI分析的调整
        analysis_text = ai_analysis.get("analysis", "").lower()
        if "error" in analysis_text or "bug" in analysis_text:
            score -= 10
        if "warning" in analysis_text:
            score -= 5
        if "good" in analysis_text or "excellent" in analysis_text:
            score += 5

        return max(0.0, min(100.0, score))

    async def _generate_recommendations(self, metrics: CodeMetrics,
                                      ai_analysis: Dict[str, Any],
                                      language: str) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于度量的建议
        if metrics.comment_ratio < 0.1:
            recommendations.append("增加代码注释，提高代码可读性")

        if metrics.complexity_per_function > 10:
            recommendations.append("降低函数复杂度，考虑拆分为多个小函数")

        if metrics.duplicate_lines > 0:
            recommendations.append("消除重复代码，提取公共逻辑")

        if metrics.functions == 0 and metrics.classes == 0:
            recommendations.append("考虑将代码组织为函数或类结构")

        # 基于AI分析的建议
        analysis_text = ai_analysis.get("analysis", "").lower()
        if "security" in analysis_text:
            recommendations.append("检查并修复安全漏洞")
        if "performance" in analysis_text:
            recommendations.append("优化代码性能，减少不必要的操作")
        if "maintainability" in analysis_text:
            recommendations.append("改进代码结构，提高可维护性")

        return recommendations[:5]  # 最多返回5条建议

    async def postprocess(self, result: Dict[str, Any],
                         context: ToolExecutionContext) -> Dict[str, Any]:
        """后处理结果"""
        # 缓存分析结果
        cache_key = f"analysis_{hash(result.get('code', ''))}"
        await self.data_storage.store(
            cache_key,
            result,
            ttl=3600,  # 缓存1小时
            metadata={"tool": "code_analyzer", "language": result.get("language")}
        )

        return result



