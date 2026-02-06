#!/usr/bin/env python3
"""
AI编程助手MCP服务器主程序

基于Model Context Protocol (MCP)的AI编程助手服务器，
提供代码分析、生成、诊断、测试、文档等智能化服务。
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional
import argparse

from mcp import Tool
from mcp.server.fastmcp import FastMCP

from .config import config, load_config_from_file
from .core.data_storage import DataStorage
from .tools.code_analyzer import CodeAnalyzer
from .tools.code_generator import CodeGenerator
from .tools.error_diagnoser import ErrorDiagnoser
from .tools.test_generator import TestGenerator
from .tools.doc_generator import DocGenerator


class CodingAssistantServer:
    """
    AI编程助手MCP服务器

    集成多个工具提供全面的编程辅助功能：
    - 代码分析和质量评估
    - 智能代码生成
    - 错误诊断和修复建议
    - 自动测试生成
    - 文档自动生成
    """

    def __init__(self):
        self.server = FastMCP(
            name="coding-assistant",
            version="1.0.0",
            instructions=self._get_server_instructions()
        )

        # 初始化核心组件
        self.data_storage = DataStorage()
        self.tools = self._initialize_tools()

        # 注册工具
        self._register_tools()

        # 设置日志
        self._setup_logging()

    def _get_server_instructions(self) -> str:
        """获取服务器指令"""
        return """
你是一个专业的AI编程助手，可以帮助开发者进行代码分析、生成、调试和优化。

可用工具包括：
- analyze_codebase: 代码库深度分析，依赖关系识别，质量评估
- generate_code: 基于需求智能生成代码，支持多种语言
- diagnose_error: 智能错误定位和修复建议
- generate_tests: 自动生成单元测试，提高覆盖率
- generate_docs: 基于代码生成规范文档

使用时请提供清晰的需求描述，我会根据上下文选择最合适的工具。
"""

    def _initialize_tools(self) -> Dict[str, Any]:
        """初始化工具"""
        return {
            "code_analyzer": CodeAnalyzer(),
            "code_generator": CodeGenerator(),
            "error_diagnoser": ErrorDiagnoser(),
            "test_generator": TestGenerator(),
            "doc_generator": DocGenerator()
        }

    def _register_tools(self):
        """注册MCP工具"""

        @self.server.tool()
        async def analyze_codebase(code: str, language: str = "python",
                                 analysis_type: str = "general") -> Dict[str, Any]:
            """
            代码库深度分析工具

            对代码进行全面的质量分析，包括：
            - 代码度量统计（复杂度、行数等）
            - 依赖关系分析
            - 代码质量评估
            - 改进建议生成

            Args:
                code: 要分析的代码内容
                language: 编程语言（python, javascript, java等）
                analysis_type: 分析类型（general, security, performance, quality）

            Returns:
                包含分析结果的字典
            """
            tool = self.tools["code_analyzer"]
            result = await tool.execute({
                "code": code,
                "language": language,
                "analysis_type": analysis_type
            })

            if result.success:
                return result.data
            else:
                raise Exception(f"代码分析失败: {result.error}")

        @self.server.tool()
        async def generate_code(requirements: str, language: str = "python",
                              framework: Optional[str] = None) -> Dict[str, Any]:
            """
            智能代码生成工具

            基于自然语言需求生成高质量代码：
            - 支持多种编程语言
            - 自动添加注释和文档
            - 包含错误处理
            - 遵循最佳实践

            Args:
                requirements: 需求描述
                language: 目标编程语言
                framework: 使用的框架（可选）

            Returns:
                包含生成代码的字典
            """
            tool = self.tools["code_generator"]
            params = {
                "requirements": requirements,
                "language": language
            }
            if framework:
                params["framework"] = framework

            result = await tool.execute(params)

            if result.success:
                return result.data
            else:
                raise Exception(f"代码生成失败: {result.error}")

        @self.server.tool()
        async def diagnose_error(error_message: str,
                               language: str = "python",
                               code_context: Optional[str] = None) -> Dict[str, Any]:
            """
            智能错误诊断工具

            分析错误信息并提供修复建议：
            - 自动错误分类
            - 根因分析
            - 修复方案建议
            - 预防措施指导

            Args:
                error_message: 错误信息
                language: 编程语言
                code_context: 相关代码上下文（可选）

            Returns:
                包含诊断结果的字典
            """
            tool = self.tools["error_diagnoser"]
            params = {
                "error_message": error_message,
                "language": language
            }
            if code_context:
                params["code_context"] = code_context

            result = await tool.execute(params)

            if result.success:
                return result.data
            else:
                raise Exception(f"错误诊断失败: {result.error}")

        @self.server.tool()
        async def generate_tests(code: str, language: str = "python",
                               framework: Optional[str] = None) -> Dict[str, Any]:
            """
            自动测试生成工具

            为代码生成全面的单元测试：
            - 覆盖正常流程和异常情况
            - 包含边界条件测试
            - 支持多种测试框架
            - 生成测试数据

            Args:
                code: 要测试的代码
                language: 编程语言
                framework: 测试框架（可选）

            Returns:
                包含测试代码的字典
            """
            tool = self.tools["test_generator"]
            params = {
                "code": code,
                "language": language
            }
            if framework:
                params["framework"] = framework

            result = await tool.execute(params)

            if result.success:
                return result.data
            else:
                raise Exception(f"测试生成失败: {result.error}")

        @self.server.tool()
        async def generate_docs(code: str, language: str = "python",
                              format: str = "markdown") -> Dict[str, Any]:
            """
            自动文档生成工具

            为代码生成规范的文档：
            - 功能描述和参数说明
            - 使用示例
            - 注意事项和最佳实践
            - 支持多种文档格式

            Args:
                code: 要文档化的代码
                language: 编程语言
                format: 文档格式（markdown, html等）

            Returns:
                包含生成文档的字典
            """
            tool = self.tools["doc_generator"]
            result = await tool.execute({
                "code": code,
                "language": language,
                "format": format
            })

            if result.success:
                return result.data
            else:
                raise Exception(f"文档生成失败: {result.error}")

    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=getattr(logging, config.logging.level.upper()),
            format=config.logging.format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(config.logging.file_path) if config.logging.file_path else logging.NullHandler()
            ]
        )

        # 减少第三方库的日志
        logging.getLogger("aiohttp").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    async def initialize(self):
        """初始化服务器"""
        await self.data_storage.initialize()

    async def shutdown(self):
        """关闭服务器"""
        await self.data_storage.shutdown()

    async def run(self):
        """运行服务器"""
        try:
            # 初始化
            await self.initialize()

            print("🚀 AI编程助手MCP服务器启动中..."            print(f"📍 服务器地址: {config.server.host}:{config.server.port}")
            print(f"🤖 AI模型: {config.ai.model}")
            print(f"🛠️  已加载工具: {len(self.tools)}")
            print("📝 服务器已就绪，等待连接...")

            # 启动服务器
            await self.server.run()

        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，正在关闭服务器...")
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            logging.error(f"Server startup failed: {e}", exc_info=True)
            raise
        finally:
            await self.shutdown()


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI编程助手MCP服务器")

    parser.add_argument(
        "--host",
        default=config.server.host,
        help=f"服务器主机地址 (默认: {config.server.host})"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=config.server.port,
        help=f"服务器端口 (默认: {config.server.port})"
    )

    parser.add_argument(
        "--config",
        help="配置文件路径"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )

    parser.add_argument(
        "--env",
        choices=["development", "production", "testing"],
        help="运行环境"
    )

    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_arguments()

    # 加载配置
    if args.config:
        global config
        config = load_config_from_file(args.config)

    # 覆盖命令行参数
    if args.host:
        config.server.host = args.host
    if args.port:
        config.server.port = args.port
    if args.debug:
        config.server.debug = True
        config.logging.level = "DEBUG"
    if args.env:
        # 这里可以根据环境设置不同的配置
        pass

    # 创建并运行服务器
    server = CodingAssistantServer()
    await server.run()


if __name__ == "__main__":
    # Windows兼容性处理
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 运行主函数
    asyncio.run(main())



