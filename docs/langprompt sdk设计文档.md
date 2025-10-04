# LangPrompt Python SDK 设计文档

## 1. SDK 概述

### 1.1 定位与目标

LangPrompt Python SDK 是官方 Python 客户端库，专注于**提示词的获取和使用**，而非管理功能。SDK 设计遵循以下原则：

- **简洁易用**: Pythonic 风格，最少化配置
- **类型安全**: 完整的类型注解支持
- **高性能**: 支持异步操作和智能缓存
- **容错性强**: 内置重试机制和友好的错误处理
- **功能聚焦**: 优先专注于提示词获取，管理功能由 Web 端完成

### 1.2 核心功能边界

**SDK 主要功能**:
- 获取项目信息
- 查询提示词及其版本
- 按标签、版本号获取提示词内容
- 本地缓存优化

**非 SDK 职责**（由 Web 端完成）:
- 项目创建和配置
- 提示词内容编辑
- 版本管理和发布
- 成员和权限管理

---

## 2. 认证机制设计

### 2.1 API Key 认证

SDK **仅支持 API Key 认证**，不支持 JWT Token 认证。API Key 适合长期运行的服务和脚本集成。

**认证方式优先级**:
1. 构造函数参数 `api_key`
2. 环境变量 `LANGPROMPT_API_KEY`
3. 配置文件 `~/.langprompt/config`

### 2.2 安全最佳实践

- API Key 通过 HTTP Header `X-API-Key` 传递
- 所有请求强制使用 HTTPS
- 支持 API Key 作用域限制（服务端实现）
- 建议通过环境变量或密钥管理系统注入

---

## 3. 客户端初始化设计

### 3.1 初始化参数

```python
LangPrompt(
    project_name: str | None = None,      # 项目名称
    project_id: UUID | None = None,       # 项目 ID（优先级高于 project_name）
    api_key: str | None = None,           # API Key
    base_url: str | None = None,          # API 基础 URL
    timeout: float = 30.0,                # 请求超时（秒）
    max_retries: int = 3,                 # 最大重试次数
    retry_delay: float = 1.0,             # 重试延迟（秒）
    enable_cache: bool = False,           # 是否启用本地缓存
    cache_ttl: int = 3600                 # 缓存过期时间（秒）
)
```

### 3.2 环境变量支持

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `LANGPROMPT_PROJECT_NAME` | 默认项目名称 | - |
| `LANGPROMPT_PROJECT_ID` | 默认项目 ID（优先级更高） | - |
| `LANGPROMPT_API_KEY` | API Key | - |
| `LANGPROMPT_API_URL` | API 基础 URL | `https://api.langprompt.com/api/v1` |

### 3.3 简化初始化

支持多种初始化方式，适应不同使用场景：

```python
# 方式 1: 最小化配置（使用环境变量）
client = LangPrompt()

# 方式 2: 指定项目名称
client = LangPrompt("my-project")

# 方式 3: 完整配置
client = LangPrompt(
    project_name="my-project",
    api_key="your-api-key",
    timeout=60
)
```

---

## 4. 核心架构设计

### 4.1 模块划分

```
langprompt/
├── client.py           # 主客户端类 LangPrompt
├── resources/          # 资源模块
│   ├── projects.py     # 项目资源
│   ├── prompts.py      # 提示词资源
│   └── versions.py     # 版本资源
├── models/             # 数据模型
│   ├── project.py
│   ├── prompt.py
│   └── version.py
├── http/               # HTTP 客户端
│   ├── client.py       # 底层 HTTP 封装
│   └── retry.py        # 重试逻辑
├── exceptions.py       # 异常定义
├── cache.py            # 缓存机制（可选）
└── config.py           # 配置管理
```

### 4.2 资源访问模式

采用**资源命名空间模式**，清晰组织 API 调用：

```python
client.projects.get()                          # 获取当前项目信息
client.prompts.list()                          # 列出所有提示词
```

### 4.3 命名规范

- **参数命名一致性**:
  - `project_id` / `project_name`
  - `prompt_id` / `prompt_name`
  - `version` (版本号整数)

---

## 5. 数据模型设计

### 5.1 模型定义原则

- 使用 Pydantic 定义所有数据模型
- 严格类型注解，支持 IDE 自动补全
- 不可变字段使用 `Field(frozen=True)` 标记
- 所有时间字段统一使用 `datetime` 类型

### 5.2 核心模型结构

**Project 模型**:
```python
class Project:
    id: UUID
    name: str
    description: str | None
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
```

**Prompt 模型**:
```python
class Prompt:
    id: UUID
    name: str                    # 支持分类命名: "category/prompt_name"
    description: str | None
    project_id: UUID
    type: str                    # 提示词类型
    tags: list[str]
    created_at: datetime
    updated_at: datetime
```

**PromptVersion 模型**:
```python
class PromptVersion:
    id: UUID
    prompt_id: UUID
    version: int                 # 版本号（不可变）
    content: dict[str, Any]      # 提示词内容（不可变）
    labels: list[str]            # 版本标签（可变）
    metadata: dict[str, Any]     # 元数据（可变）
    commit_message: str          # 提交信息（不可变）
    created_at: datetime         # 创建时间（不可变）
    updated_at: datetime
```

---

## 6. API 调用设计

### 6.1 同步与异步 API

提供同步和异步两套完整 API：

```python
# 同步 API
client = LangPrompt()
prompt = client.prompts.get("greeting")

# 异步 API
client = AsyncLangPrompt()
prompt = await client.prompts.get("greeting")
```

### 6.2 分页处理

对于列表类接口，统一使用分页模式：

```python
# 参数设计
list(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    tags: list[str] | None = None
)

# 返回结构
class PagedResponse[T]:
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
```

### 6.3 内容获取快捷方法

提供专门的快捷方法简化常见操作：

```python
# 按标签获取（最常用）
content = client.prompts.get_content(
    name="greeting",
    label="production"  # 默认为 "production"
)

# 按版本号获取
content = client.prompts.get_content(
    name="greeting",
    version=5
)

# 获取最新版本
content = client.prompts.get_latest(name="greeting")
```

---

## 7. 错误处理设计

### 7.1 异常层级

```python
LangPromptError                    # 基础异常
├── AuthenticationError            # 认证失败（401）
├── PermissionError               # 权限不足（403）
├── NotFoundError                 # 资源不存在（404）
├── ValidationError               # 参数验证失败（422）
├── RateLimitError                # 请求限流（429）
├── ServerError                   # 服务器错误（5xx）
├── NetworkError                  # 网络错误
└── TimeoutError                  # 请求超时
```

### 7.2 错误响应解析

所有错误包含详细信息：

```python
class LangPromptError(Exception):
    error_code: str              # 错误代码
    message: str                 # 错误消息
    details: dict[str, Any]      # 详细信息
    status_code: int | None      # HTTP 状态码
```

### 7.3 错误处理最佳实践

```python
try:
    content = client.prompts.get_content("greeting", label="production")
except NotFoundError:
    # 提示词不存在，使用默认值
    content = get_default_prompt()
except PermissionError:
    # 权限不足，记录日志
    logger.error("API Key 权限不足")
except LangPromptError as e:
    # 其他错误
    logger.error(f"获取提示词失败: {e.message}")
```

---

## 8. 重试机制设计

### 8.1 重试策略

**默认重试条件**:
- HTTP 5xx 服务器错误
- 网络超时或连接错误
- 429 限流错误（使用指数退避）

**不重试的错误**:
- 4xx 客户端错误（除了 429）
- 认证和权限错误
- 参数验证错误

### 8.2 退避算法

采用**指数退避 + 抖动**策略：

```
第 n 次重试延迟 = min(retry_delay * 2^n + random(0, 1), max_delay)
```

- `retry_delay`: 基础延迟（默认 1 秒）
- `max_delay`: 最大延迟（默认 30 秒）
- 添加随机抖动避免雷同请求

### 8.3 自定义重试配置

```python
client = LangPrompt(
    max_retries=5,           # 最大重试 5 次
    retry_delay=2.0,         # 基础延迟 2 秒
    retry_statuses=[429, 500, 502, 503, 504]  # 可自定义重试的状态码
)
```

---

## 9. 缓存策略设计

### 9.1 缓存机制（可选功能）

缓存可显著提升性能，但默认禁用以保证数据实时性。

**缓存层级**:
1. **内存缓存**: 进程级缓存，速度最快
2. **文件缓存**: 跨进程共享（可选）
3. **自定义缓存**: 支持 Redis 等外部缓存

### 9.2 缓存键设计

```
缓存键格式: langprompt:{project_id}:{resource}:{identifier}

示例:
- langprompt:uuid:prompt:greeting
- langprompt:uuid:version:greeting:production
- langprompt:uuid:version:greeting:v5
```

### 9.3 缓存失效策略

- **TTL 过期**: 基于时间的自动过期（默认 1 小时）
- **主动刷新**: 提供 `refresh=True` 参数强制刷新
- **版本化缓存**: 不可变数据（如版本内容）可永久缓存

### 9.4 缓存控制

```python
# 启用缓存
client = LangPrompt(enable_cache=True, cache_ttl=3600)

# 强制刷新
content = client.prompts.get_content("greeting", refresh=True)

# 清空缓存
client.cache.clear()
```

---

## 10. 配置管理设计

### 10.1 配置文件支持

支持配置文件简化多环境管理：

**配置文件路径**:
- `~/.langprompt/config` (用户级)
- `./.langprompt` (项目级，优先级更高)

**配置格式** (TOML):
```toml
[default]
project_name = "my-project"
api_key = "your-api-key"
base_url = "https://api.langprompt.com/api/v1"
timeout = 30
max_retries = 3

[production]
project_id = "uuid-here"
api_key = "prod-api-key"

[development]
project_name = "dev-project"
api_key = "dev-api-key"
```

### 10.2 配置优先级

从高到低：
1. 构造函数参数
2. 环境变量
3. 项目级配置文件 (`./.langprompt`)
4. 用户级配置文件 (`~/.langprompt/config`)
5. 默认值

### 10.3 多环境配置

```python
# 使用不同配置环境
client = LangPrompt(config_env="production")
client = LangPrompt(config_env="development")
```

---

## 11. 高级特性设计

### 11.1 中间件支持

允许用户自定义请求和响应处理：

```python
class Middleware:
    def before_request(self, request): ...
    def after_response(self, response): ...
    def on_error(self, error): ...

client = LangPrompt(middlewares=[LoggingMiddleware(), MetricsMiddleware()])
```

### 11.2 请求钩子

```python
client.on("request", lambda req: logger.info(f"请求: {req.url}"))
client.on("response", lambda res: logger.info(f"响应: {res.status}"))
client.on("error", lambda err: logger.error(f"错误: {err}"))
```

### 11.3 批量操作

支持批量获取提高效率：

```python
# 批量获取提示词
prompts = client.prompts.batch_get(["greeting", "farewell", "help"])

# 批量获取内容
contents = client.prompts.batch_get_content(
    names=["greeting", "farewell"],
    label="production"
)
```

---

## 12. 性能优化设计

### 12.1 连接池管理

- 使用 HTTP 连接池复用连接
- 默认池大小: 10 个连接
- 支持自定义连接池配置

### 12.2 并发控制

- 异步 API 支持并发请求
- 提供并发限制防止资源耗尽
- 支持请求队列和优先级

### 12.3 压缩传输

- 自动启用 gzip 压缩
- 减少网络传输数据量
- 对大型提示词内容尤其有效

---

## 13. 日志与监控设计

### 13.1 日志集成

- 使用标准库 `logging` 模块
- 默认日志级别: `WARNING`
- 支持自定义日志配置

```python
import logging
logging.getLogger("langprompt").setLevel(logging.DEBUG)
```

### 13.2 日志内容

记录关键操作：
- API 请求和响应（DEBUG）
- 重试和失败（WARNING）
- 错误详情（ERROR）
- 缓存命中率（INFO）

### 13.3 监控指标

可选的指标收集：
- 请求成功率
- 平均响应时间
- 缓存命中率
- 错误率分布

---

## 14. 测试与质量保证

### 14.1 测试覆盖

- **单元测试**: 覆盖所有核心模块
- **集成测试**: 真实 API 交互测试
- **Mock 测试**: 使用 `responses` 库模拟 HTTP 响应
- **类型检查**: 使用 `mypy` 确保类型安全

### 14.2 测试工具

- `pytest`: 测试框架
- `pytest-asyncio`: 异步测试支持
- `pytest-cov`: 代码覆盖率
- `responses`: HTTP Mock

### 14.3 CI/CD 集成

- 自动运行测试套件
- 代码覆盖率检查（目标 >80%）
- 类型检查和代码规范检查
- 自动发布到 PyPI

---

## 15. 版本与兼容性

### 15.1 语义化版本

遵循 `MAJOR.MINOR.PATCH` 规范：
- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的功能新增
- **PATCH**: 向后兼容的问题修复

### 15.2 Python 版本支持

- **最低版本**: Python 3.11+
- **推荐版本**: Python 3.12+
- **测试覆盖**: 3.11, 3.12, 3.13

### 15.3 依赖管理

**核心依赖**:
- `httpx`: 现代 HTTP 客户端（同步/异步）
- `pydantic`: 数据验证和模型

**可选依赖**:
- `redis`: Redis 缓存支持
- `orjson`: 更快的 JSON 解析

---

## 16. 安全性考虑

### 16.1 API Key 保护

- 不在日志中输出完整 API Key
- 日志中仅显示 Key 前缀（如 `lp_xxx...`）
- 建议使用环境变量或密钥管理服务

### 16.2 HTTPS 强制

- 所有请求强制使用 HTTPS
- 拒绝 HTTP 连接（除非显式允许）
- 验证 SSL 证书

### 16.3 敏感数据处理

- 提示词内容可能包含敏感信息
- 不在缓存中存储标记为敏感的内容
- 支持自定义数据加密钩子

---

## 17. 文档与示例

### 17.1 文档结构

- **快速开始**: 5 分钟上手
- **完整教程**: 详细使用指南
- **API 参考**: 自动生成的 API 文档
- **最佳实践**: 生产环境使用建议

### 17.2 示例项目

提供典型使用场景示例：
- 简单提示词获取
- 多环境配置管理
- 异步批量操作
- 自定义缓存策略
- 与 LangChain 集成

---

## 18. 扩展性与插件

### 18.1 自定义序列化

支持自定义提示词内容的序列化：

```python
class CustomSerializer:
    def serialize(self, data): ...
    def deserialize(self, data): ...

client = LangPrompt(serializer=CustomSerializer())
```

### 18.2 自定义缓存后端

```python
class RedisCacheBackend:
    def get(self, key): ...
    def set(self, key, value, ttl): ...
    def delete(self, key): ...

client = LangPrompt(
    enable_cache=True,
    cache_backend=RedisCacheBackend()
)
```

### 18.3 自定义 HTTP 客户端

允许使用自定义的 HTTP 客户端实现：

```python
client = LangPrompt(http_client=CustomHttpClient())
```

---

## 19. 发布与分发

### 19.1 包管理

- **PyPI**: 官方 Python 包索引
- **包名**: `langprompt-python`
- **安装命令**: `pip install langprompt-python`

### 19.2 版本发布流程

1. 代码审查和测试
2. 更新版本号和 CHANGELOG
3. 构建分发包
4. 发布到 PyPI
5. 创建 GitHub Release
6. 更新文档网站

### 19.3 向后兼容承诺

- 在 MAJOR 版本内保持 API 兼容
- 废弃功能提前至少一个 MINOR 版本警告
- 提供迁移指南

---

## 20. 总结

LangPrompt Python SDK 的设计理念：

1. **简洁优雅**: API 设计直观，符合 Python 习惯
2. **类型安全**: 完整的类型注解和 IDE 支持
3. **高性能**: 异步支持、连接池、智能缓存
4. **容错性**: 自动重试、友好的错误处理
5. **可扩展**: 中间件、钩子、自定义后端
6. **专注核心**: 聚焦提示词获取，管理由 Web 完成

通过清晰的架构和优雅的 API 设计，LangPrompt SDK 将为 Python 开发者提供最佳的提示词管理体验。
