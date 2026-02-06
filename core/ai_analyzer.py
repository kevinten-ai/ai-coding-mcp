"""
AI分析器
集成大语言模型进行智能分析和报告生成
"""

import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import time

from ..config import config
from .prompt_manager import PromptManager


class AIModel(Enum):
    """AI模型类型"""
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    CLAUDE_3 = "claude-3"
    CLAUDE_2 = "claude-2"


@dataclass
class AIRequest:
    """AI请求"""
    prompt: str
    model: AIModel = AIModel.GPT_4
    temperature: float = 0.7
    max_tokens: int = 2000
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """AI响应"""
    content: str
    model: str
    usage: Dict[str, int]  # token使用统计
    finish_reason: str
    response_time: float
    metadata: Dict[str, Any]


class LLMClient:
    """LLM客户端抽象接口"""

    async def generate(self, request: AIRequest) -> AIResponse:
        """
        生成响应

        Args:
            request: AI请求

        Returns:
            AIResponse: AI响应
        """
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI客户端"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url
            )
        except ImportError:
            raise ImportError("openai package not installed")

    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()

        messages = [{"role": "user", "content": request.prompt}]

        # 添加上下文信息
        if request.context:
            system_message = self._build_system_message(request.context)
            messages.insert(0, {"role": "system", "content": system_message})

        response = await self.client.chat.completions.create(
            model=request.model.value,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            timeout=config.ai.timeout
        )

        response_time = time.time() - start_time

        return AIResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            finish_reason=response.choices[0].finish_reason,
            response_time=response_time,
            metadata=request.metadata or {}
        )

    def _build_system_message(self, context: Dict[str, Any]) -> str:
        """构建系统消息"""
        system_parts = []

        if "role" in context:
            system_parts.append(f"You are a {context['role']}.")

        if "expertise" in context:
            system_parts.append(f"You specialize in {context['expertise']}.")

        if "guidelines" in context:
            system_parts.append(f"Follow these guidelines: {context['guidelines']}")

        return " ".join(system_parts)


class AnthropicClient(LLMClient):
    """Anthropic客户端"""

    def __init__(self, api_key: str):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed")

    async def generate(self, request: AIRequest) -> AIResponse:
        start_time = time.time()

        system_message = ""
        if request.context:
            system_message = self._build_system_message(request.context)

        response = await self.client.messages.create(
            model=request.model.value,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=system_message,
            messages=[{"role": "user", "content": request.prompt}]
        )

        response_time = time.time() - start_time

        # 计算token使用量（近似值）
        prompt_tokens = len(request.prompt.split()) * 1.3  # 粗略估算
        completion_tokens = len(response.content.split()) * 1.3

        return AIResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "prompt_tokens": int(prompt_tokens),
                "completion_tokens": int(completion_tokens),
                "total_tokens": int(prompt_tokens + completion_tokens)
            },
            finish_reason=response.stop_reason,
            response_time=response_time,
            metadata=request.metadata or {}
        )

    def _build_system_message(self, context: Dict[str, Any]) -> str:
        """构建系统消息"""
        system_parts = []

        if "role" in context:
            system_parts.append(f"You are a {context['role']}.")

        if "expertise" in context:
            system_parts.append(f"You specialize in {context['expertise']}.")

        return " ".join(system_parts)


class AIAnalyzer:
    """
    AI分析器

    集成大语言模型进行智能分析和报告生成：
    - 支持多种AI模型（GPT、Claude等）
    - 提供结构化的分析结果
    - 支持上下文感知的分析
    """

    def __init__(self):
        self.prompt_manager = PromptManager()
        self._clients: Dict[str, LLMClient] = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """初始化AI客户端"""
        # OpenAI客户端
        if config.ai.api_key and config.ai.provider.lower() == "openai":
            try:
                self._clients["openai"] = OpenAIClient(
                    api_key=config.ai.api_key,
                    base_url=config.ai.base_url
                )
            except ImportError:
                print("Warning: OpenAI client not available")

        # Anthropic客户端
        if config.ai.provider.lower() == "anthropic":
            try:
                self._clients["anthropic"] = AnthropicClient(
                    api_key=config.ai.api_key
                )
            except ImportError:
                print("Warning: Anthropic client not available")

    async def analyze_code(self, code: str, language: str,
                          analysis_type: str = "general") -> Dict[str, Any]:
        """
        代码分析

        Args:
            code: 代码内容
            language: 编程语言
            analysis_type: 分析类型

        Returns:
            Dict[str, Any]: 分析结果
        """
        context = {
            "role": "professional code analyzer",
            "expertise": f"{language} development and best practices",
            "analysis_type": analysis_type
        }

        if analysis_type == "security":
            prompt = self._build_security_analysis_prompt(code, language)
        elif analysis_type == "performance":
            prompt = self._build_performance_analysis_prompt(code, language)
        elif analysis_type == "quality":
            prompt = self._build_quality_analysis_prompt(code, language)
        else:
            prompt = self._build_general_analysis_prompt(code, language)

        request = AIRequest(
            prompt=prompt,
            model=AIModel(config.ai.model),
            temperature=config.ai.temperature,
            max_tokens=config.ai.max_tokens,
            context=context,
            metadata={"analysis_type": analysis_type, "language": language}
        )

        response = await self._generate_response(request)

        return {
            "analysis": response.content,
            "language": language,
            "type": analysis_type,
            "model": response.model,
            "usage": response.usage,
            "response_time": response.response_time
        }

    async def generate_code(self, requirements: str, language: str,
                           framework: Optional[str] = None) -> Dict[str, Any]:
        """
        代码生成

        Args:
            requirements: 需求描述
            language: 编程语言
            framework: 框架

        Returns:
            Dict[str, Any]: 生成结果
        """
        variables = {
            "task": requirements,
            "language": language,
            "framework": framework or language,
            "requirements": requirements
        }

        prompt = self.prompt_manager.generate_prompt(
            "code_development",
            variables
        )

        context = {
            "role": "expert software developer",
            "expertise": f"{language} development with {framework or 'modern practices'}"
        }

        request = AIRequest(
            prompt=prompt,
            context=context,
            metadata={"task": "code_generation", "language": language}
        )

        response = await self._generate_response(request)

        return {
            "code": response.content,
            "language": language,
            "framework": framework,
            "requirements": requirements,
            "usage": response.usage,
            "response_time": response.response_time
        }

    async def diagnose_error(self, error_message: str,
                           code_context: Optional[str] = None,
                           language: str = "python") -> Dict[str, Any]:
        """
        错误诊断

        Args:
            error_message: 错误信息
            code_context: 代码上下文
            language: 编程语言

        Returns:
            Dict[str, Any]: 诊断结果
        """
        variables = {
            "error_message": error_message,
            "code_context": code_context or "No context provided",
            "language": language
        }

        prompt = self.prompt_manager.generate_prompt(
            "debug_diagnosis",
            variables
        )

        context = {
            "role": "expert debugger and troubleshooter",
            "expertise": f"{language} debugging and error resolution"
        }

        request = AIRequest(
            prompt=prompt,
            context=context,
            metadata={"task": "error_diagnosis", "language": language}
        )

        response = await self._generate_response(request)

        return {
            "diagnosis": response.content,
            "error_message": error_message,
            "language": language,
            "code_context": code_context,
            "usage": response.usage,
            "response_time": response.response_time
        }

    async def generate_tests(self, function_code: str, language: str,
                           framework: str = "unittest") -> Dict[str, Any]:
        """
        测试生成

        Args:
            function_code: 函数代码
            language: 编程语言
            framework: 测试框架

        Returns:
            Dict[str, Any]: 测试代码
        """
        variables = {
            "function_name": "target_function",  # 可以从代码中提取
            "language": language,
            "framework": framework
        }

        prompt = self.prompt_manager.generate_prompt(
            "unit_testing",
            variables,
            context={"code": function_code}
        )

        context = {
            "role": "expert test engineer",
            "expertise": f"{language} testing with {framework}"
        }

        request = AIRequest(
            prompt=prompt,
            context=context,
            metadata={"task": "test_generation", "language": language, "framework": framework}
        )

        response = await self._generate_response(request)

        return {
            "test_code": response.content,
            "language": language,
            "framework": framework,
            "target_code": function_code,
            "usage": response.usage,
            "response_time": response.response_time
        }

    async def generate_documentation(self, code: str, language: str,
                                   format: str = "markdown") -> Dict[str, Any]:
        """
        文档生成

        Args:
            code: 代码内容
            language: 编程语言
            format: 文档格式

        Returns:
            Dict[str, Any]: 生成的文档
        """
        variables = {
            "code_element": code[:500],  # 限制长度
            "language": language,
            "doc_format": format
        }

        prompt = self.prompt_manager.generate_prompt(
            "documentation",
            variables
        )

        context = {
            "role": "technical writer and documentation expert",
            "expertise": f"{language} documentation in {format} format"
        }

        request = AIRequest(
            prompt=prompt,
            context=context,
            metadata={"task": "documentation", "language": language, "format": format}
        )

        response = await self._generate_response(request)

        return {
            "documentation": response.content,
            "language": language,
            "format": format,
            "source_code": code,
            "usage": response.usage,
            "response_time": response.response_time
        }

    async def review_code(self, code: str, language: str,
                         focus_areas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        代码审查

        Args:
            code: 代码内容
            language: 编程语言
            focus_areas: 重点关注领域

        Returns:
            Dict[str, Any]: 审查结果
        """
        review_focus = ", ".join(focus_areas) if focus_areas else "general quality"

        variables = {
            "code_snippet": code,
            "language": language,
            "review_focus": review_focus
        }

        prompt = self.prompt_manager.generate_prompt(
            "code_review",
            variables
        )

        context = {
            "role": "senior code reviewer and software architect",
            "expertise": f"{language} code quality and best practices"
        }

        request = AIRequest(
            prompt=prompt,
            context=context,
            metadata={"task": "code_review", "language": language, "focus": review_focus}
        )

        response = await self._generate_response(request)

        return {
            "review": response.content,
            "language": language,
            "focus_areas": focus_areas,
            "source_code": code,
            "usage": response.usage,
            "response_time": response.response_time
        }

    async def _generate_response(self, request: AIRequest) -> AIResponse:
        """生成AI响应"""
        provider = config.ai.provider.lower()

        if provider not in self._clients:
            raise ValueError(f"AI provider '{provider}' not configured")

        client = self._clients[provider]
        return await client.generate(request)

    def _build_general_analysis_prompt(self, code: str, language: str) -> str:
        """构建通用分析提示"""
        return f"""
请分析以下{language}代码：

```python
{code}
```

请提供：
1. 代码功能概述
2. 代码质量评估
3. 潜在改进建议
4. 最佳实践检查

分析结果请以结构化格式呈现。
"""

    def _build_security_analysis_prompt(self, code: str, language: str) -> str:
        """构建安全分析提示"""
        return f"""
请从安全角度分析以下{language}代码：

```python
{code}
```

重点检查：
1. 输入验证漏洞
2. 注入攻击风险
3. 权限控制问题
4. 数据泄露风险
5. 其他安全隐患

请提供详细的安全评估报告。
"""

    def _build_performance_analysis_prompt(self, code: str, language: str) -> str:
        """构建性能分析提示"""
        return f"""
请分析以下{language}代码的性能特征：

```python
{code}
```

分析内容：
1. 算法复杂度分析
2. 性能瓶颈识别
3. 内存使用评估
4. 优化建议

请提供具体的性能改进方案。
"""

    def _build_quality_analysis_prompt(self, code: str, language: str) -> str:
        """构建质量分析提示"""
        return f"""
请评估以下{language}代码的质量：

```python
{code}
```

质量维度：
1. 可读性
2. 可维护性
3. 代码结构
4. 命名规范
5. 注释完整性
6. 测试覆盖

请给出综合质量评分和改进建议。
"""

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return [model.value for model in AIModel]

    def get_client_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "available_providers": list(self._clients.keys()),
            "configured_provider": config.ai.provider,
            "model": config.ai.model
        }



