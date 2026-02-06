"""
代码生成工具
基于需求智能生成代码
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .base_tool import BaseTool, ToolExecutionResult, ToolExecutionContext
from ..core.ai_analyzer import AIAnalyzer
from ..core.prompt_manager import PromptManager
from ..config import config


class CodeTemplate:
    """代码模板"""

    def __init__(self, name: str, language: str, framework: str,
                 template: str, variables: List[str]):
        self.name = name
        self.language = language
        self.framework = framework
        self.template = template
        self.variables = variables

    def render(self, variables: Dict[str, str]) -> str:
        """渲染模板"""
        result = self.template
        for var, value in variables.items():
            placeholder = f"{{{var}}}"
            result = result.replace(placeholder, value)
        return result


class CodeGenerator(BaseTool):
    """
    代码生成工具

    提供智能代码生成功能：
    - 基于自然语言需求生成代码
    - 支持多种编程语言和框架
    - 自动添加注释和文档
    - 代码质量保证
    """

    def __init__(self):
        super().__init__("code_generator", "智能代码生成工具")
        self.ai_analyzer = AIAnalyzer()
        self.prompt_manager = PromptManager()
        self.templates = self._load_templates()
        self.required_params = ["requirements", "language"]

    def _load_templates(self) -> Dict[str, CodeTemplate]:
        """加载代码模板"""
        return {
            "python_function": CodeTemplate(
                name="python_function",
                language="python",
                framework="standard",
                template=self._get_python_function_template(),
                variables=["function_name", "parameters", "return_type", "docstring", "body"]
            ),
            "python_class": CodeTemplate(
                name="python_class",
                language="python",
                framework="standard",
                template=self._get_python_class_template(),
                variables=["class_name", "methods", "docstring"]
            ),
            "javascript_function": CodeTemplate(
                name="javascript_function",
                language="javascript",
                framework="node",
                template=self._get_javascript_function_template(),
                variables=["function_name", "parameters", "body"]
            ),
            "java_class": CodeTemplate(
                name="java_class",
                language="java",
                framework="standard",
                template=self._get_java_class_template(),
                variables=["class_name", "package", "methods"]
            )
        }

    async def validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证参数"""
        validated = await super().validate_params(params)

        language = params.get("language", "").lower()
        if language not in self.tool_config.supported_languages:
            raise ValueError(f"不支持的语言: {language}")

        requirements = params.get("requirements", "").strip()
        if len(requirements) < 10:
            raise ValueError("需求描述太简短，请提供更详细的需求")

        return validated

    async def preprocess(self, params: Dict[str, Any],
                        context: ToolExecutionContext) -> Dict[str, Any]:
        """预处理参数"""
        language = params.get("language", "python").lower()
        framework = params.get("framework", language).lower()
        output_format = params.get("output_format", "complete")

        # 提取关键信息
        requirements = params["requirements"]
        complexity = self._estimate_complexity(requirements)

        return {
            **params,
            "language": language,
            "framework": framework,
            "output_format": output_format,
            "estimated_complexity": complexity
        }

    async def _execute_core(self, params: Dict[str, Any],
                           context: ToolExecutionContext) -> Dict[str, Any]:
        """核心执行逻辑"""
        requirements = params["requirements"]
        language = params["language"]
        framework = params["framework"]
        output_format = params["output_format"]

        # 使用AI生成代码
        generation_result = await self.ai_analyzer.generate_code(
            requirements=requirements,
            language=language,
            framework=framework
        )

        # 后处理生成的代码
        processed_code = await self._postprocess_code(
            generation_result["code"],
            language,
            output_format
        )

        # 验证代码质量
        quality_check = await self._validate_generated_code(
            processed_code,
            language
        )

        return {
            "generated_code": processed_code,
            "language": language,
            "framework": framework,
            "requirements": requirements,
            "quality_check": quality_check,
            "metadata": {
                "output_format": output_format,
                "estimated_complexity": params.get("estimated_complexity"),
                "ai_usage": generation_result.get("usage")
            }
        }

    async def _postprocess_code(self, code: str, language: str,
                               output_format: str) -> str:
        """后处理生成的代码"""
        # 移除可能的markdown代码块标记
        code = self._clean_code_markers(code)

        # 根据格式进行处理
        if output_format == "function":
            code = self._extract_function(code, language)
        elif output_format == "class":
            code = self._extract_class(code, language)

        # 添加语言特定的后处理
        if language == "python":
            code = self._postprocess_python_code(code)
        elif language == "javascript":
            code = self._postprocess_javascript_code(code)
        elif language == "java":
            code = self._postprocess_java_code(code)

        # 格式化代码
        code = self._format_code(code, language)

        return code

    def _clean_code_markers(self, code: str) -> str:
        """清理代码块标记"""
        # 移除markdown代码块
        code = re.sub(r'```\w*\n?', '', code)
        # 移除可能的语言标记
        code = re.sub(r'^\s*python\s*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'^\s*javascript\s*\n', '', code, flags=re.MULTILINE)
        code = re.sub(r'^\s*java\s*\n', '', code, flags=re.MULTILINE)
        return code.strip()

    def _extract_function(self, code: str, language: str) -> str:
        """提取函数代码"""
        if language == "python":
            # 查找def语句
            lines = code.split('\n')
            in_function = False
            indent_level = 0
            function_lines = []

            for line in lines:
                if line.strip().startswith('def '):
                    in_function = True
                    indent_level = len(line) - len(line.lstrip())
                    function_lines = [line]
                elif in_function:
                    current_indent = len(line) - len(line.lstrip())
                    if line.strip() and current_indent > indent_level:
                        function_lines.append(line)
                    elif line.strip() and current_indent <= indent_level:
                        break

            return '\n'.join(function_lines) if function_lines else code

        return code

    def _extract_class(self, code: str, language: str) -> str:
        """提取类代码"""
        if language == "python":
            # 查找class语句
            lines = code.split('\n')
            in_class = False
            indent_level = 0
            class_lines = []

            for line in lines:
                if line.strip().startswith('class '):
                    in_class = True
                    indent_level = len(line) - len(line.lstrip())
                    class_lines = [line]
                elif in_class:
                    current_indent = len(line) - len(line.lstrip())
                    if line.strip() and current_indent >= indent_level:
                        class_lines.append(line)
                    elif line.strip() and current_indent < indent_level:
                        break

            return '\n'.join(class_lines) if class_lines else code

        return code

    def _postprocess_python_code(self, code: str) -> str:
        """Python代码后处理"""
        lines = code.split('\n')
        processed_lines = []

        for line in lines:
            # 确保缩进正确
            if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                if any(keyword in line for keyword in ['def ', 'class ', 'if ', 'for ', 'while ']):
                    processed_lines.append(line)
                else:
                    processed_lines.append('    ' + line)
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def _postprocess_javascript_code(self, code: str) -> str:
        """JavaScript代码后处理"""
        # 基本清理
        return code

    def _postprocess_java_code(self, code: str) -> str:
        """Java代码后处理"""
        # 基本清理
        return code

    def _format_code(self, code: str, language: str) -> str:
        """格式化代码"""
        try:
            if language == "python":
                # 使用black格式化（如果可用）
                import black
                mode = black.FileMode()
                code = black.format_str(code, mode=mode)
            elif language == "javascript":
                # 可以使用prettier（这里简化处理）
                pass
        except ImportError:
            # 如果没有格式化工具，保持原样
            pass

        return code

    async def _validate_generated_code(self, code: str,
                                     language: str) -> Dict[str, Any]:
        """验证生成的代码"""
        validation_result = {
            "is_valid": True,
            "syntax_check": True,
            "warnings": [],
            "errors": []
        }

        try:
            if language == "python":
                compile(code, '<generated>', 'exec')
            elif language == "javascript":
                # 基本语法检查（简化）
                pass
            validation_result["syntax_check"] = True
        except SyntaxError as e:
            validation_result["is_valid"] = False
            validation_result["syntax_check"] = False
            validation_result["errors"].append(f"语法错误: {str(e)}")
        except Exception as e:
            validation_result["warnings"].append(f"验证警告: {str(e)}")

        # 检查代码长度
        if len(code) < 50:
            validation_result["warnings"].append("生成的代码可能太短")

        # 检查是否有基本的代码结构
        if language == "python":
            if not any(keyword in code for keyword in ['def ', 'class ', 'import ', 'from ']):
                validation_result["warnings"].append("代码缺少基本结构")

        return validation_result

    def _estimate_complexity(self, requirements: str) -> str:
        """估算需求复杂度"""
        complexity_score = 0

        # 关键词复杂度评估
        complex_keywords = [
            'database', 'api', 'authentication', 'security', 'concurrent',
            'async', 'machine learning', 'algorithm', 'optimization',
            'integration', 'microservice', 'distributed'
        ]

        for keyword in complex_keywords:
            if keyword.lower() in requirements.lower():
                complexity_score += 1

        # 长度复杂度
        if len(requirements) > 200:
            complexity_score += 1
        elif len(requirements) > 500:
            complexity_score += 2

        # 确定复杂度级别
        if complexity_score >= 5:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"

    def _get_python_function_template(self) -> str:
        """Python函数模板"""
        return '''
def {function_name}({parameters}) -> {return_type}:
    """
    {docstring}
    """
    {body}
'''

    def _get_python_class_template(self) -> str:
        """Python类模板"""
        return '''
class {class_name}:
    """
    {docstring}
    """

    def __init__(self):
        pass

    {methods}
'''

    def _get_javascript_function_template(self) -> str:
        """JavaScript函数模板"""
        return '''
function {function_name}({parameters}) {{
    {body}
}}
'''

    def _get_java_class_template(self) -> str:
        """Java类模板"""
        return '''
package {package};

public class {class_name} {{
    {methods}
}}
'''

    async def postprocess(self, result: Dict[str, Any],
                         context: ToolExecutionContext) -> Dict[str, Any]:
        """后处理结果"""
        # 可以在这里添加代码审查或进一步优化
        return result



