# AI编程助手MCP服务器

基于Model Context Protocol (MCP)的AI编程助手服务器，为开发者提供智能化的应用数据获取和分析服务。

## 功能特性

- **代码分析**：深度代码库分析，依赖关系识别，复杂度评估
- **代码生成**：基于需求智能生成代码，支持多种编程语言
- **错误诊断**：智能错误定位和修复建议
- **测试生成**：自动生成单元测试，提高代码覆盖率
- **文档生成**：基于代码自动生成规范文档
- **代码审查**：AI驱动的代码质量检查和改进建议

## 架构设计

采用分层架构设计：

- **提示词管理器**：生成各种场景下的开发指导
- **数据获取器**：统一管理外部MCP服务调用和数据聚合
- **数据存储器**：处理数据持久化和检索
- **AI分析器**：集成大语言模型进行智能分析

## 技术栈

- **框架**：FastMCP - MCP协议的标准实现
- **异步编程**：asyncio + aiohttp - 高效并发处理
- **AI集成**：支持多种LLM模型（GPT-4、Claude等）
- **配置管理**：Pydantic - 类型安全的配置验证

## 安装使用

### 环境要求

- Python 3.8+
- pip
- Git（可选，用于版本控制）

### 安装步骤

#### 1. 克隆项目（可选）

```bash
git clone <repository-url>
cd ai-coding-mcp
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境

##### 基本配置

复制并编辑配置文件：

```bash
cp config.py config.local.py  # 创建本地配置文件（可选）
```

编辑 `config.py` 或 `config.local.py` 配置以下参数：

```python
# 服务器配置
config.server.host = "0.0.0.0"  # 监听所有接口
config.server.port = 8080       # 服务端口
config.server.debug = True      # 调试模式

# AI配置
config.ai.api_key = "your-api-key-here"  # AI服务API密钥
config.ai.model = "gpt-4"                # 使用的AI模型
config.ai.provider = "openai"            # AI提供商

# 安全配置
config.security.allowed_paths = ["/path/to/allowed"]  # 允许的文件路径
config.security.max_file_size = 10*1024*1024         # 最大文件大小(10MB)
```

##### 环境变量配置

也可以通过环境变量配置：

```bash
export AI_API_KEY="your-api-key-here"
export ENV="development"  # 或 "production"
export MCP_HOST="0.0.0.0"
export MCP_PORT="8080"
```

#### 4. 启动服务

##### 基本启动

```bash
python main.py
```

##### 自定义启动参数

```bash
# 指定主机和端口
python main.py --host 0.0.0.0 --port 8080

# 启用调试模式
python main.py --debug

# 指定配置文件
python main.py --config config.local.py

# 指定运行环境
python main.py --env production
```

### 验证安装

启动服务后，访问以下端点验证：

```bash
curl http://localhost:8080/health  # 健康检查（如果实现）
```

查看日志确认服务正常运行：

```
🚀 AI编程助手MCP服务器启动中...
📍 服务器地址: localhost:8080
🤖 AI模型: gpt-4
🛠️  已加载工具: 5
📝 服务器已就绪，等待连接...
```

## 项目结构

```
ai-coding-mcp/
├── core/                 # 核心模块
│   ├── prompt_manager.py # 提示词管理器
│   ├── data_fetcher.py   # 数据获取器
│   ├── data_storage.py   # 数据存储器
│   └── ai_analyzer.py    # AI分析器
├── tools/                # 工具实现
│   ├── base_tool.py      # 工具抽象基类
│   ├── code_analyzer.py  # 代码分析工具
│   ├── code_generator.py # 代码生成工具
│   └── ...
├── utils/                # 工具函数
│   ├── error_handler.py  # 错误处理
│   ├── security.py       # 安全验证
│   └── ...
├── config.py             # 配置管理
├── main.py               # 服务器启动
├── requirements.txt      # 依赖包
└── README.md            # 项目文档
```

## API使用示例

### 连接到MCP服务器

使用MCP客户端连接到服务器：

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # 启动MCP服务器进程
    server_params = StdioServerParameters(
        command="python",
        args=["main.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()

            # 调用工具
            result = await session.call_tool(
                "analyze_codebase",
                arguments={
                    "code": "def hello():\n    print('Hello, World!')",
                    "language": "python"
                }
            )

            print("分析结果:", result)
```

### 工具使用示例

#### 1. 代码分析

```python
# 分析Python代码
result = await session.call_tool("analyze_codebase", {
    "code": """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
""",
    "language": "python",
    "analysis_type": "performance"
})

print("代码质量评分:", result["quality_score"])
print("改进建议:", result["recommendations"])
```

#### 2. 代码生成

```python
# 生成REST API代码
result = await session.call_tool("generate_code", {
    "requirements": "创建一个用户管理系统，提供注册、登录、获取用户信息的功能",
    "language": "python",
    "framework": "fastapi"
})

print("生成的代码:")
print(result["generated_code"])
```

#### 3. 错误诊断

```python
# 诊断错误
result = await session.call_tool("diagnose_error", {
    "error_message": "NameError: name 'undefined_variable' is not defined",
    "language": "python",
    "code_context": "print(undefined_variable)"
})

print("诊断结果:", result["diagnosis"])
print("解决方案:", result["solutions"])
```

#### 4. 测试生成

```python
# 生成单元测试
result = await session.call_tool("generate_tests", {
    "code": "def add_numbers(a, b):\n    return a + b",
    "language": "python",
    "framework": "pytest"
})

print("生成的测试:")
print(result["test_code"])
```

#### 5. 文档生成

```python
# 生成代码文档
result = await session.call_tool("generate_docs", {
    "code": "def process_data(data):\n    '''处理数据'''\n    return sorted(data)",
    "language": "python",
    "format": "markdown"
})

print("生成的文档:")
print(result["documentation"])
```

## 开发指南

### 项目结构说明

```
ai-coding-mcp/
├── config.py              # 全局配置
├── main.py               # 服务器启动入口
├── core/                 # 核心组件
│   ├── prompt_manager.py # 提示词管理
│   ├── data_fetcher.py   # 数据获取
│   ├── data_storage.py   # 数据存储
│   └── ai_analyzer.py    # AI分析器
├── tools/                # 工具实现
│   ├── base_tool.py      # 工具基类
│   ├── code_analyzer.py  # 代码分析工具
│   ├── code_generator.py # 代码生成工具
│   ├── error_diagnoser.py# 错误诊断工具
│   ├── test_generator.py # 测试生成工具
│   └── doc_generator.py  # 文档生成工具
├── utils/                # 工具函数
│   ├── security.py       # 安全验证
│   └── error_handler.py  # 错误处理
└── tests/                # 测试文件
    ├── __init__.py
    ├── test_config.py
    └── test_base_tool.py
```

### 添加新工具

1. **创建工具类**

在 `tools/` 目录下创建新的工具类，继承 `BaseTool`：

```python
from .base_tool import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__("my_custom_tool", "我的自定义工具")

    async def _execute_core(self, params, context):
        # 实现核心逻辑
        return {"result": "custom processing done"}
```

2. **注册工具**

在 `main.py` 中的 `CodingAssistantServer._register_tools()` 方法中添加：

```python
@self.server.tool()
async def my_custom_function(param1: str, param2: int = 0):
    tool = self.tools["my_custom_tool"]
    result = await tool.execute({"param1": param1, "param2": param2})
    if result.success:
        return result.data
    else:
        raise Exception(f"工具执行失败: {result.error}")
```

3. **更新配置**

在 `config.py` 中添加工具配置：

```python
class MyCustomToolConfig(ToolConfig):
    custom_setting: str = "default_value"

# 添加到MCPConfig
my_custom_tool: MyCustomToolConfig = Field(default_factory=MyCustomToolConfig)
```

### 测试运行

运行单元测试：

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_config.py

# 运行带覆盖率的测试
pytest --cov=. --cov-report=html
```

### 自定义配置

#### 配置文件

创建 `config.local.py`（不会被版本控制）：

```python
from config import config

# 自定义配置
config.server.debug = True
config.ai.api_key = "your-secret-key"
config.cache.enabled = False
```

#### 环境变量

支持的环境变量：

- `AI_API_KEY`: AI服务API密钥
- `ENV`: 运行环境（development/production）
- `MCP_HOST`: 服务器主机
- `MCP_PORT`: 服务器端口
- `LOG_LEVEL`: 日志级别

## 部署指南

### Docker部署

创建 `Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "main.py", "--host", "0.0.0.0"]
```

构建和运行：

```bash
# 构建镜像
docker build -t ai-coding-mcp .

# 运行容器
docker run -p 8080:8080 \
  -e AI_API_KEY="your-api-key" \
  -e ENV="production" \
  ai-coding-mcp
```

### 系统服务

创建systemd服务文件 `/etc/systemd/system/ai-coding-mcp.service`：

```ini
[Unit]
Description=AI Coding Assistant MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ai-coding-mcp
ExecStart=/usr/bin/python3 main.py --env production
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

管理服务：

```bash
# 启动服务
sudo systemctl start ai-coding-mcp

# 查看状态
sudo systemctl status ai-coding-mcp

# 设置开机自启
sudo systemctl enable ai-coding-mcp
```

## 故障排除

### 常见问题

#### 1. 端口被占用

```
错误: [Errno 48] Address already in use
```

解决方法：
```bash
# 查找占用端口的进程
lsof -i :8080

# 杀死进程或更换端口
python main.py --port 8081
```

#### 2. AI服务连接失败

```
错误: AI service unavailable
```

解决方法：
- 检查API密钥是否正确
- 验证网络连接
- 检查AI服务配额
- 尝试更换AI模型

#### 3. 依赖安装失败

```
错误: Could not find a version that satisfies the requirement
```

解决方法：
```bash
# 更新pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### 4. 内存不足

```
错误: Out of memory
```

解决方法：
- 减少并发请求数：`config.server.workers = 2`
- 启用缓存：`config.cache.enabled = True`
- 增加系统内存或使用交换分区

### 日志分析

查看应用日志：

```bash
# 查看最近的日志
tail -f logs/mcp_server.log

# 按错误级别过滤
grep "ERROR" logs/mcp_server.log

# 分析性能问题
grep "execution_time" logs/mcp_server.log | sort -n
```

### 性能监控

基本监控指标：

```python
# 在main.py中添加健康检查端点（示例）
@self.server.tool()
async def health_check():
    return {
        "status": "healthy",
        "uptime": "获取运行时间",
        "active_connections": "获取活动连接数",
        "memory_usage": "获取内存使用情况"
    }
```

### 升级指南

1. 备份当前配置和数据
2. 停止服务：`systemctl stop ai-coding-mcp`
3. 更新代码：`git pull`
4. 安装新依赖：`pip install -r requirements.txt`
5. 迁移配置（如有需要）
6. 启动服务：`systemctl start ai-coding-mcp`
7. 验证功能正常

## 贡献指南

### 代码规范

- 使用Black格式化代码：`black .`
- 使用isort整理导入：`isort .`
- 使用flake8检查代码质量：`flake8 .`
- 编写完整的单元测试
- 更新相关文档

### 提交规范

```bash
# 提交消息格式
<type>(<scope>): <subject>

# 示例
feat(code-generator): add support for React component generation
fix(error-handler): resolve memory leak in error logging
docs(readme): update installation instructions
```

### 发布流程

1. 更新版本号（`main.py`中的版本）
2. 更新CHANGELOG.md
3. 创建Git标签
4. 构建Docker镜像
5. 发布到包仓库

## 许可证

MIT License

## 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: your-email@example.com

---

**最后更新**: 2024年11月27日