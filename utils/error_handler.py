"""
错误处理工具
提供统一的错误处理和用户友好的错误信息
"""

import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

from ..config import config


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误分类"""
    NETWORK = "network"
    SECURITY = "security"
    VALIDATION = "validation"
    PROCESSING = "processing"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL_ERROR = "internal_error"


@dataclass
class ErrorInfo:
    """错误信息"""
    code: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    suggestions: List[str]
    log_level: int = logging.ERROR


class ErrorTranslator:
    """
    错误翻译器

    将技术错误转换为用户友好的信息
    """

    def __init__(self):
        self.error_map = self._initialize_error_map()

    def _initialize_error_map(self) -> Dict[str, ErrorInfo]:
        """初始化错误映射"""
        return {
            # 网络错误
            "CONNECTION_ERROR": ErrorInfo(
                code="CONNECTION_ERROR",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message="Network connection failed",
                user_message="网络连接失败，请检查网络设置",
                suggestions=[
                    "检查网络连接是否正常",
                    "确认服务器地址是否正确",
                    "尝试稍后重试"
                ]
            ),

            "TIMEOUT_ERROR": ErrorInfo(
                code="TIMEOUT_ERROR",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message="Request timeout",
                user_message="请求超时，请稍后重试",
                suggestions=[
                    "检查网络连接速度",
                    "尝试减少请求数据量",
                    "联系技术支持"
                ]
            ),

            # 安全错误
            "SECURITY_VIOLATION": ErrorInfo(
                code="SECURITY_VIOLATION",
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.HIGH,
                message="Security violation detected",
                user_message="检测到安全违规，操作已被阻止",
                suggestions=[
                    "请勿尝试访问未授权的资源",
                    "检查输入数据的安全性",
                    "联系管理员获取权限"
                ]
            ),

            "INVALID_FILE_PATH": ErrorInfo(
                code="INVALID_FILE_PATH",
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.MEDIUM,
                message="Invalid file path",
                user_message="文件路径无效或不安全",
                suggestions=[
                    "检查文件路径格式",
                    "确保路径在允许的范围内",
                    "避免使用特殊字符"
                ]
            ),

            # 验证错误
            "MISSING_PARAMETER": ErrorInfo(
                code="MISSING_PARAMETER",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message="Required parameter missing",
                user_message="缺少必需的参数",
                suggestions=[
                    "检查API文档确认必需参数",
                    "提供所有必需的输入参数",
                    "查看错误详情了解缺少的参数"
                ]
            ),

            "INVALID_PARAMETER": ErrorInfo(
                code="INVALID_PARAMETER",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message="Parameter validation failed",
                user_message="参数格式或值无效",
                suggestions=[
                    "检查参数类型和格式",
                    "参考API文档的参数说明",
                    "使用有效的参数值"
                ]
            ),

            # 处理错误
            "CODE_ANALYSIS_FAILED": ErrorInfo(
                code="CODE_ANALYSIS_FAILED",
                category=ErrorCategory.PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                message="Code analysis failed",
                user_message="代码分析失败",
                suggestions=[
                    "检查代码语法是否正确",
                    "确保代码文件未损坏",
                    "尝试重新提交代码"
                ]
            ),

            "AI_SERVICE_ERROR": ErrorInfo(
                code="AI_SERVICE_ERROR",
                category=ErrorCategory.EXTERNAL_SERVICE,
                severity=ErrorSeverity.HIGH,
                message="AI service unavailable",
                user_message="AI服务暂时不可用",
                suggestions=[
                    "检查AI服务配置",
                    "稍后重试",
                    "联系技术支持"
                ]
            ),

            # 配置错误
            "CONFIGURATION_ERROR": ErrorInfo(
                code="CONFIGURATION_ERROR",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.HIGH,
                message="Configuration error",
                user_message="配置错误，服务无法正常工作",
                suggestions=[
                    "检查配置文件格式",
                    "验证配置参数的有效性",
                    "参考配置文档"
                ]
            ),

            # 内部错误
            "INTERNAL_ERROR": ErrorInfo(
                code="INTERNAL_ERROR",
                category=ErrorCategory.INTERNAL_ERROR,
                severity=ErrorSeverity.CRITICAL,
                message="Internal server error",
                user_message="服务器内部错误",
                suggestions=[
                    "请稍后重试",
                    "收集错误信息反馈给开发团队",
                    "查看系统日志了解详情"
                ]
            )
        }

    def translate(self, error_code: str, context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """
        翻译错误代码为用户友好的信息

        Args:
            error_code: 错误代码
            context: 错误上下文

        Returns:
            ErrorInfo: 错误信息
        """
        error_info = self.error_map.get(error_code)

        if not error_info:
            # 未知错误，使用通用错误信息
            error_info = ErrorInfo(
                code=error_code,
                category=ErrorCategory.INTERNAL_ERROR,
                severity=ErrorSeverity.MEDIUM,
                message=f"Unknown error: {error_code}",
                user_message="发生未知错误",
                suggestions=[
                    "请稍后重试",
                    "联系技术支持获取帮助",
                    "提供错误详情以便诊断"
                ]
            )

        # 根据上下文定制消息
        if context:
            error_info = self._customize_error_info(error_info, context)

        return error_info

    def _customize_error_info(self, error_info: ErrorInfo, context: Dict[str, Any]) -> ErrorInfo:
        """根据上下文定制错误信息"""
        customized = ErrorInfo(
            code=error_info.code,
            category=error_info.category,
            severity=error_info.severity,
            message=error_info.message,
            user_message=error_info.user_message,
            suggestions=error_info.suggestions.copy(),
            log_level=error_info.log_level
        )

        # 添加上下文特定的建议
        if "tool_name" in context:
            tool_name = context["tool_name"]
            customized.suggestions.append(f"尝试使用其他工具代替 {tool_name}")

        if "retry_count" in context and context["retry_count"] > 0:
            customized.suggestions.append("已自动重试多次，建议检查输入参数")

        return customized


class ErrorHandler:
    """
    错误处理器

    提供统一的错误处理机制：
    - 错误分类和记录
    - 用户友好错误信息
    - 错误恢复策略
    - 监控和告警
    """

    def __init__(self):
        self.translator = ErrorTranslator()
        self.logger = logging.getLogger(__name__)

    async def handle_error(self, error: Exception,
                          context: Optional[Dict[str, Any]] = None,
                          user_friendly: bool = True) -> Dict[str, Any]:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文
            user_friendly: 是否返回用户友好的信息

        Returns:
            Dict[str, Any]: 错误响应
        """
        # 确定错误代码
        error_code = self._classify_error(error)

        # 获取错误信息
        error_info = self.translator.translate(error_code, context)

        # 记录错误日志
        await self._log_error(error, error_info, context)

        # 构建响应
        response = {
            "error": {
                "code": error_info.code,
                "category": error_info.category.value,
                "severity": error_info.severity.value,
            },
            "suggestions": error_info.suggestions
        }

        if user_friendly:
            response["message"] = error_info.user_message
        else:
            response["message"] = error_info.message
            response["details"] = str(error)

        # 检查是否需要告警
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            await self._send_alert(error_info, context)

        return response

    def _classify_error(self, error: Exception) -> str:
        """
        分类错误

        Args:
            error: 异常对象

        Returns:
            str: 错误代码
        """
        error_type = type(error).__name__
        error_message = str(error).lower()

        # 网络相关错误
        if any(keyword in error_message for keyword in ["connection", "network", "timeout"]):
            if "timeout" in error_message:
                return "TIMEOUT_ERROR"
            else:
                return "CONNECTION_ERROR"

        # 安全相关错误
        if any(keyword in error_message for keyword in ["security", "violation", "unsafe"]):
            return "SECURITY_VIOLATION"

        if "path" in error_message and any(keyword in error_message for keyword in ["invalid", "traversal"]):
            return "INVALID_FILE_PATH"

        # 验证相关错误
        if any(keyword in error_message for keyword in ["missing", "required"]):
            return "MISSING_PARAMETER"

        if any(keyword in error_message for keyword in ["invalid", "validation"]):
            return "INVALID_PARAMETER"

        # AI服务错误
        if any(keyword in error_message for keyword in ["ai", "openai", "anthropic", "model"]):
            return "AI_SERVICE_ERROR"

        # 配置错误
        if "config" in error_message:
            return "CONFIGURATION_ERROR"

        # 默认内部错误
        return "INTERNAL_ERROR"

    async def _log_error(self, error: Exception, error_info: ErrorInfo,
                        context: Optional[Dict[str, Any]]):
        """记录错误日志"""
        log_data = {
            "error_code": error_info.code,
            "error_category": error_info.category.value,
            "error_severity": error_info.severity.value,
            "error_message": str(error),
            "context": context or {}
        }

        self.logger.log(
            error_info.log_level,
            f"Error handled: {error_info.code}",
            extra=log_data
        )

    async def _send_alert(self, error_info: ErrorInfo, context: Optional[Dict[str, Any]]):
        """
        发送告警（简化实现，实际项目中可以集成监控系统）

        Args:
            error_info: 错误信息
            context: 上下文
        """
        alert_message = f"""
高严重度错误告警:
错误代码: {error_info.code}
错误类别: {error_info.category.value}
严重程度: {error_info.severity.value}
消息: {error_info.message}
上下文: {context or {}}
        """.strip()

        # 这里可以发送邮件、Slack通知等
        self.logger.warning(f"ALERT: {alert_message}")

    async def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息（简化实现）"""
        # 实际项目中可以从日志系统或数据库获取统计信息
        return {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recent_errors": []
        }


# 全局错误处理器实例
error_handler = ErrorHandler()



