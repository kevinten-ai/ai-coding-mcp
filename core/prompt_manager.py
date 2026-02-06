"""
提示词管理器
负责生成各种场景下的开发指导和操作流程
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..config import config


class PromptType(Enum):
    """提示词类型"""
    DEVELOPMENT = "development"  # 开发指导
    DEBUGGING = "debugging"     # 调试指导
    OPTIMIZATION = "optimization" # 优化指导
    TESTING = "testing"         # 测试指导
    DOCUMENTATION = "documentation" # 文档指导
    REVIEW = "review"          # 代码审查


@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    type: PromptType
    template: str
    variables: List[str]
    description: str = ""


class PromptManager:
    """
    提示词管理器

    提供智能提示词生成和管理功能：
    - 动态生成包含具体操作步骤的指导
    - 支持多种开发场景
    - 集成最佳实践和行业标准
    """

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """加载默认提示词模板"""
        self.templates = {
            "code_development": PromptTemplate(
                name="code_development",
                type=PromptType.DEVELOPMENT,
                template=self._get_development_template(),
                variables=["task", "language", "framework", "requirements"],
                description="通用代码开发指导"
            ),
            "debug_diagnosis": PromptTemplate(
                name="debug_diagnosis",
                type=PromptType.DEBUGGING,
                template=self._get_debug_template(),
                variables=["error_message", "code_context", "language"],
                description="错误诊断和调试指导"
            ),
            "performance_optimization": PromptTemplate(
                name="performance_optimization",
                type=PromptType.OPTIMIZATION,
                template=self._get_optimization_template(),
                variables=["code_type", "performance_issue", "language"],
                description="性能优化指导"
            ),
            "unit_testing": PromptTemplate(
                name="unit_testing",
                type=PromptType.TESTING,
                template=self._get_testing_template(),
                variables=["function_name", "language", "framework"],
                description="单元测试生成指导"
            ),
            "documentation": PromptTemplate(
                name="documentation",
                type=PromptType.DOCUMENTATION,
                template=self._get_documentation_template(),
                variables=["code_element", "language", "doc_format"],
                description="文档生成指导"
            ),
            "code_review": PromptTemplate(
                name="code_review",
                type=PromptType.REVIEW,
                template=self._get_review_template(),
                variables=["code_snippet", "language", "review_focus"],
                description="代码审查指导"
            )
        }

    def _get_development_template(self) -> str:
        """获取开发指导模板"""
        return """
请基于以下需求为{language}开发{framework}应用：

需求描述：
{requirements}

任务目标：
{task}

请提供完整的实现方案，包括：
1. 代码结构设计
2. 核心算法实现
3. 错误处理机制
4. 最佳实践应用

请确保代码：
- 遵循{language}编码规范
- 包含适当的注释
- 具有良好的可维护性
- 支持扩展和测试

实现步骤：
1. 分析需求并设计接口
2. 实现核心功能
3. 添加错误处理
4. 编写单元测试
5. 优化性能和代码质量
"""

    def _get_debug_template(self) -> str:
        """获取调试指导模板"""
        return """
请分析以下{language}代码中的错误：

错误信息：
{error_message}

代码上下文：
{code_context}

请提供：
1. 错误原因分析
2. 修复方案建议
3. 预防措施
4. 相关调试技巧

调试步骤：
1. 重现问题
2. 定位错误根源
3. 验证修复效果
4. 添加回归测试
"""

    def _get_optimization_template(self) -> str:
        """获取优化指导模板"""
        return """
请优化以下{language}代码的{performance_issue}问题：

代码类型：{code_type}

请提供：
1. 性能瓶颈识别
2. 优化策略建议
3. 具体的改进方案
4. 性能测试方法

优化原则：
1. 识别热点代码
2. 减少不必要的操作
3. 利用合适的数据结构
4. 考虑并发优化
"""

    def _get_testing_template(self) -> str:
        """获取测试指导模板"""
        return """
请为{language}函数{function_name}生成{framework}单元测试：

测试要求：
- 覆盖正常流程
- 覆盖异常情况
- 包含边界条件
- 确保代码覆盖率

测试结构：
1. 测试用例设计
2. Mock对象设置
3. 断言验证
4. 测试数据准备
"""

    def _get_documentation_template(self) -> str:
        """获取文档指导模板"""
        return """
请为以下{language}代码元素生成{doc_format}格式的文档：

代码元素：{code_element}

文档内容包括：
1. 功能描述
2. 参数说明
3. 返回值说明
4. 使用示例
5. 注意事项

文档标准：
- 清晰简洁的描述
- 完整的参数文档
- 实用的代码示例
- 错误处理说明
"""

    def _get_review_template(self) -> str:
        """获取代码审查指导模板"""
        return """
请审查以下{language}代码片段，重点关注{review_focus}：

代码内容：
{code_snippet}

审查要点：
1. 代码质量评估
2. 最佳实践检查
3. 安全漏洞扫描
4. 性能问题识别
5. 可维护性分析

改进建议：
- 代码结构优化
- 命名规范改进
- 注释完善
- 测试覆盖
"""

    def generate_prompt(self, template_name: str,
                       variables: Dict[str, Any],
                       context: Optional[Dict[str, Any]] = None) -> str:
        """
        生成提示词

        Args:
            template_name: 模板名称
            variables: 变量值
            context: 上下文信息

        Returns:
            str: 生成的提示词
        """
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.templates[template_name]

        # 验证必需变量
        missing_vars = set(template.variables) - set(variables.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        # 替换变量
        prompt = template.template
        for var, value in variables.items():
            placeholder = f"{{{var}}}"
            prompt = prompt.replace(placeholder, str(value))

        # 添加上下文信息
        if context:
            prompt += self._generate_context_section(context)

        return prompt.strip()

    def _generate_context_section(self, context: Dict[str, Any]) -> str:
        """生成上下文信息部分"""
        context_parts = []

        if "project_info" in context:
            context_parts.append(f"\n项目信息：{context['project_info']}")

        if "user_preferences" in context:
            context_parts.append(f"\n用户偏好：{context['user_preferences']}")

        if "constraints" in context:
            context_parts.append(f"\n约束条件：{context['constraints']}")

        if "best_practices" in context:
            context_parts.append(f"\n最佳实践：{context['best_practices']}")

        return "\n".join(context_parts)

    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有可用模板

        Returns:
            Dict[str, Dict[str, Any]]: 模板信息
        """
        return {
            name: {
                "type": template.type.value,
                "variables": template.variables,
                "description": template.description
            }
            for name, template in self.templates.items()
        }

    def add_custom_template(self, template: PromptTemplate):
        """
        添加自定义模板

        Args:
            template: 提示词模板
        """
        self.templates[template.name] = template

    def remove_template(self, template_name: str):
        """
        删除模板

        Args:
            template_name: 模板名称
        """
        if template_name in self.templates:
            del self.templates[template_name]

    def save_templates_to_file(self, file_path: str):
        """
        保存模板到文件

        Args:
            file_path: 保存路径
        """
        templates_data = {
            name: {
                "name": template.name,
                "type": template.type.value,
                "template": template.template,
                "variables": template.variables,
                "description": template.description
            }
            for name, template in self.templates.items()
        }

        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(templates_data, f, ensure_ascii=False, indent=2)

    def load_templates_from_file(self, file_path: str):
        """
        从文件加载模板

        Args:
            file_path: 文件路径
        """
        if not Path(file_path).exists():
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            templates_data = json.load(f)

        for name, data in templates_data.items():
            template = PromptTemplate(
                name=data["name"],
                type=PromptType(data["type"]),
                template=data["template"],
                variables=data["variables"],
                description=data.get("description", "")
            )
            self.templates[name] = template

    def get_template_suggestions(self, task_description: str) -> List[str]:
        """
        根据任务描述推荐模板

        Args:
            task_description: 任务描述

        Returns:
            List[str]: 推荐的模板名称列表
        """
        suggestions = []
        desc_lower = task_description.lower()

        # 关键词匹配
        if any(word in desc_lower for word in ["开发", "实现", "创建", "build", "develop"]):
            suggestions.append("code_development")

        if any(word in desc_lower for word in ["调试", "错误", "bug", "fix", "debug"]):
            suggestions.append("debug_diagnosis")

        if any(word in desc_lower for word in ["优化", "性能", "速度", "optimize", "performance"]):
            suggestions.append("performance_optimization")

        if any(word in desc_lower for word in ["测试", "test", "单元测试"]):
            suggestions.append("unit_testing")

        if any(word in desc_lower for word in ["文档", "注释", "doc", "document"]):
            suggestions.append("documentation")

        if any(word in desc_lower for word in ["审查", "检查", "review", "audit"]):
            suggestions.append("code_review")

        return suggestions[:3]  # 返回前3个建议



