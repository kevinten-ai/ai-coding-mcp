"""
错误诊断工具
智能错误定位和修复建议
"""

import re
import traceback
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .base_tool import BaseTool, ToolExecutionResult, ToolExecutionContext
from ..core.ai_analyzer import AIAnalyzer
from ..config import config


@dataclass
class ErrorPattern:
    """错误模式"""
    name: str
    pattern: str
    language: str
    category: str
    severity: str
    description: str
    solution: str


@dataclass
class DiagnosticResult:
    """诊断结果"""
    error_type: str
    severity: str
    confidence: float
    location: Optional[Dict[str, Any]]
    description: str
    root_cause: str
    solutions: List[str]
    prevention_tips: List[str]


class ErrorDiagnoser(BaseTool):
    """
    错误诊断工具

    提供智能的错误诊断和修复功能：
    - 自动错误分类和分析
    - 根因定位
    - 修复方案建议
    - 预防措施指导
    """

    def __init__(self):
        super().__init__("error_diagnoser", "智能错误诊断和修复工具")
        self.ai_analyzer = AIAnalyzer()
        self.error_patterns = self._load_error_patterns()
        self.required_params = ["error_message"]

    def _load_error_patterns(self) -> Dict[str, ErrorPattern]:
        """加载错误模式"""
        return {
            # Python错误模式
            "python_syntax_error": ErrorPattern(
                name="python_syntax_error",
                pattern=r"SyntaxError: (.+)",
                language="python",
                category="syntax",
                severity="high",
                description="Python语法错误",
                solution="检查语法规则，修复语法错误"
            ),
            "python_import_error": ErrorPattern(
                name="python_import_error",
                pattern=r"ImportError: No module named '(.+)'",
                language="python",
                category="import",
                severity="medium",
                description="模块导入错误",
                solution="安装缺失的模块或检查导入路径"
            ),
            "python_name_error": ErrorPattern(
                name="python_name_error",
                pattern=r"NameError: name '(.+)' is not defined",
                language="python",
                category="variable",
                severity="medium",
                description="变量未定义错误",
                solution="检查变量定义和作用域"
            ),
            "python_type_error": ErrorPattern(
                name="python_type_error",
                pattern=r"TypeError: (.+)",
                language="python",
                category="type",
                severity="medium",
                description="类型错误",
                solution="检查数据类型和操作兼容性"
            ),
            "python_attribute_error": ErrorPattern(
                name="python_attribute_error",
                pattern=r"AttributeError: '(.+)' object has no attribute '(.+)'",
                language="python",
                category="attribute",
                severity="medium",
                description="属性错误",
                solution="检查对象属性和方法调用"
            ),

            # JavaScript错误模式
            "js_reference_error": ErrorPattern(
                name="js_reference_error",
                pattern=r"ReferenceError: (.+) is not defined",
                language="javascript",
                category="variable",
                severity="medium",
                description="引用错误",
                solution="检查变量声明和作用域"
            ),
            "js_type_error": ErrorPattern(
                name="js_type_error",
                pattern=r"TypeError: (.+)",
                language="javascript",
                category="type",
                severity="medium",
                description="类型错误",
                solution="检查数据类型和操作"
            ),

            # 通用错误模式
            "network_error": ErrorPattern(
                name="network_error",
                pattern=r"(ConnectionError|TimeoutError|HTTPError)",
                language="any",
                category="network",
                severity="medium",
                description="网络连接错误",
                solution="检查网络连接和配置"
            ),
            "file_not_found": ErrorPattern(
                name="file_not_found",
                pattern=r"(FileNotFoundError|ENOENT)",
                language="any",
                category="file",
                severity="medium",
                description="文件未找到错误",
                solution="检查文件路径和权限"
            )
        }

    async def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated = await super().validate_params(params)

        error_message = params.get("error_message", "").strip()
        if not error_message:
            raise ValueError("错误信息不能为空")

        return validated

    async def preprocess(self, params: Dict[str, Any],
                        context: ToolExecutionContext) -> Dict[str, Any]:
        """预处理参数"""
        language = params.get("language", "python").lower()
        code_context = params.get("code_context", "")
        stack_trace = params.get("stack_trace", "")

        # 清理和格式化错误信息
        error_message = self._clean_error_message(params["error_message"])

        return {
            **params,
            "language": language,
            "error_message": error_message,
            "code_context": code_context,
            "stack_trace": stack_trace
        }

    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> Dict[str, Any]:
        """核心执行逻辑"""
        error_message = params["error_message"]
        language = params["language"]
        code_context = params["code_context"]
        stack_trace = params["stack_trace"]

        # 模式匹配诊断
        pattern_diagnosis = self._pattern_based_diagnosis(
            error_message, language
        )

        # AI深度诊断
        ai_diagnosis = await self.ai_analyzer.diagnose_error(
            error_message=error_message,
            code_context=code_context,
            language=language
        )

        # 综合诊断结果
        combined_diagnosis = await self._combine_diagnoses(
            pattern_diagnosis, ai_diagnosis
        )

        # 生成修复方案
        solutions = await self._generate_solutions(
            combined_diagnosis, code_context, language
        )

        # 预防建议
        prevention_tips = await self._generate_prevention_tips(
            combined_diagnosis, language
        )

        return {
            "error_message": error_message,
            "language": language,
            "diagnosis": combined_diagnosis,
            "solutions": solutions,
            "prevention_tips": prevention_tips,
            "code_context": code_context,
            "stack_trace": stack_trace,
            "confidence": combined_diagnosis.confidence,
            "severity": combined_diagnosis.severity
        }

    def _clean_error_message(self, error_message: str) -> str:
        """清理错误信息"""
        # 移除ANSI颜色代码
        error_message = re.sub(r'\x1b\[[0-9;]*m', '', error_message)

        # 移除多余的换行和空格
        error_message = ' '.join(error_message.split())

        # 移除可能的日志前缀
        error_message = re.sub(r'^\[.*?\]\s*', '', error_message)

        return error_message.strip()

    def _pattern_based_diagnosis(self, error_message: str,
                               language: str) -> Optional[DiagnosticResult]:
        """基于模式的诊断"""
        for pattern in self.error_patterns.values():
            if pattern.language in [language, "any"]:
                match = re.search(pattern.pattern, error_message, re.IGNORECASE)
                if match:
                    return DiagnosticResult(
                        error_type=pattern.category,
                        severity=pattern.severity,
                        confidence=0.8,
                        location=None,
                        description=pattern.description,
                        root_cause=f"匹配到错误模式: {pattern.name}",
                        solutions=[pattern.solution],
                        prevention_tips=[]
                    )

        return None

    async def _combine_diagnoses(self, pattern_diagnosis: Optional[DiagnosticResult],
                               ai_diagnosis: Dict[str, Any]) -> DiagnosticResult:
        """综合诊断结果"""
        if pattern_diagnosis:
            # 有模式匹配结果，结合AI分析
            ai_text = ai_diagnosis.get("diagnosis", "")

            # 提高置信度如果AI分析确认
            confidence = pattern_diagnosis.confidence
            if any(word in ai_text.lower() for word in ["确认", "确实", "correct", "right"]):
                confidence = min(1.0, confidence + 0.2)

            # 合并解决方案
            ai_solutions = self._extract_solutions_from_ai(ai_text)
            all_solutions = pattern_diagnosis.solutions + ai_solutions

            return DiagnosticResult(
                error_type=pattern_diagnosis.error_type,
                severity=pattern_diagnosis.severity,
                confidence=confidence,
                location=pattern_diagnosis.location,
                description=pattern_diagnosis.description,
                root_cause=pattern_diagnosis.root_cause,
                solutions=list(set(all_solutions)),  # 去重
                prevention_tips=[]
            )
        else:
            # 只有AI诊断
            ai_text = ai_diagnosis.get("diagnosis", "")
            return DiagnosticResult(
                error_type=self._infer_error_type(ai_text),
                severity=self._infer_severity(ai_text),
                confidence=0.6,
                location=None,
                description=ai_text[:200],
                root_cause="AI分析结果",
                solutions=self._extract_solutions_from_ai(ai_text),
                prevention_tips=[]
            )

    def _infer_error_type(self, ai_text: str) -> str:
        """从AI文本推断错误类型"""
        text_lower = ai_text.lower()

        if any(word in text_lower for word in ["syntax", "语法"]):
            return "syntax"
        elif any(word in text_lower for word in ["import", "module", "导入"]):
            return "import"
        elif any(word in text_lower for word in ["type", "类型"]):
            return "type"
        elif any(word in text_lower for word in ["variable", "变量"]):
            return "variable"
        else:
            return "unknown"

    def _infer_severity(self, ai_text: str) -> str:
        """从AI文本推断严重程度"""
        text_lower = ai_text.lower()

        if any(word in text_lower for word in ["critical", "严重", "error"]):
            return "high"
        elif any(word in text_lower for word in ["warning", "警告"]):
            return "medium"
        else:
            return "low"

    def _extract_solutions_from_ai(self, ai_text: str) -> List[str]:
        """从AI文本提取解决方案"""
        solutions = []

        # 查找可能的解决方案模式
        lines = ai_text.split('\n')
        for line in lines:
            line = line.strip()
            if any(line.lower().startswith(prefix) for prefix in [
                "solution:", "解决", "fix:", "修复", "建议"
            ]):
                solutions.append(line)

        # 如果没有找到明确的解决方案，提取包含行动动词的句子
        if not solutions:
            action_verbs = ["检查", "修复", "修改", "添加", "删除", "更新", "设置"]
            for line in lines:
                if any(verb in line for verb in action_verbs):
                    solutions.append(line.strip())

        return solutions[:5]  # 最多返回5个解决方案

    async def _generate_solutions(self, diagnosis: DiagnosticResult,
                                code_context: str, language: str) -> List[Dict[str, Any]]:
        """生成修复方案"""
        solutions = []

        for solution_text in diagnosis.solutions:
            solution = {
                "description": solution_text,
                "difficulty": self._estimate_difficulty(solution_text),
                "code_changes": await self._generate_code_changes(
                    solution_text, code_context, language
                ),
                "test_suggestion": self._generate_test_suggestion(
                    solution_text, language
                )
            }
            solutions.append(solution)

        return solutions

    def _estimate_difficulty(self, solution: str) -> str:
        """估算解决方案难度"""
        difficulty_score = 0

        # 关键词难度评估
        hard_keywords = ["重构", "架构", "design", "refactor", "architecture"]
        medium_keywords = ["修改", "添加", "更新", "change", "add", "update"]

        for keyword in hard_keywords:
            if keyword in solution:
                difficulty_score += 2

        for keyword in medium_keywords:
            if keyword in solution:
                difficulty_score += 1

        if difficulty_score >= 3:
            return "high"
        elif difficulty_score >= 1:
            return "medium"
        else:
            return "low"

    async def _generate_code_changes(self, solution: str,
                                   code_context: str, language: str) -> List[Dict[str, Any]]:
        """生成代码变更建议"""
        # 这里可以根据解决方案生成具体的代码变更
        # 简化实现，返回基本的变更建议
        return [{
            "type": "modify",
            "description": f"根据解决方案修改代码: {solution}",
            "estimated_lines": 5
        }]

    def _generate_test_suggestion(self, solution: str, language: str) -> str:
        """生成测试建议"""
        if language == "python":
            return "添加单元测试验证修复效果"
        elif language == "javascript":
            return "添加Jest测试验证修复"
        else:
            return "添加相应测试验证修复效果"

    async def _generate_prevention_tips(self, diagnosis: DiagnosticResult,
                                      language: str) -> List[str]:
        """生成预防建议"""
        tips = []

        error_type = diagnosis.error_type

        if error_type == "syntax":
            tips.extend([
                "使用IDE的语法检查功能",
                "遵循代码格式化工具（如black、prettier）的建议",
                "编写代码时及时检查语法"
            ])
        elif error_type == "import":
            tips.extend([
                "使用requirements.txt管理依赖",
                "检查导入路径是否正确",
                "使用虚拟环境隔离项目依赖"
            ])
        elif error_type == "variable":
            tips.extend([
                "在使用变量前确保已定义",
                "注意变量作用域",
                "使用类型提示提高代码可读性"
            ])
        elif error_type == "type":
            tips.extend([
                f"使用{language}的类型检查工具",
                "添加适当的类型转换",
                "编写时考虑数据类型兼容性"
            ])

        return tips[:3]

    async def postprocess(self, result: Dict[str, Any],
                         context: ToolExecutionContext) -> Dict[str, Any]:
        """后处理结果"""
        # 添加额外的元数据
        result["processed_at"] = context.start_time.isoformat() if context.start_time else None
        result["tool_version"] = "1.0.0"

        return result



