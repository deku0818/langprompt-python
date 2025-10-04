# LangPrompt Python SDK

LangPrompt Python SDK 是 [LangPrompt](https://github.com/deku0818/langprompt) 的 Python 客户端库，提供简洁易用的 API 来管理和使用 AI Prompt。

## 项目简介

LangPrompt 是 Prompt 管理界的 **GitHub + Apollo** 结合体，励志提供：

- 🔄 **完整的版本管理** - 类似 Git 的版本控制机制
- 🔐 **企业级权限管理** - 多层级角色权限控制（Owner/Admin/Editor/Viewer）
- 🚀 **高性能 API** - 异步处理，支持大规模并发
- 📊 **灵活的元数据** - 支持自定义配置和标签管理
- 🤖 **AI友好** - 未来会提供相关MCP，便于测试、创建、迭代Prompt
- 🏷️ **智能标签系统** - 支持 production/staging/development 等环境标签

## 核心概念

### 数据层级结构

```
项目 (Project)
 └── 提示词 (Prompt)
      └── 版本 (Version)
```

### 版本管理特性

LangPrompt 采用类似 Git 的版本管理机制：

- **不可变字段**：`content`、`version`、`commit_message`、`created_at` 一旦创建不可修改
- **可变字段**：`labels`、`metadata` 可以动态更新
- **标签唯一性**：同一提示词下，每个标签只能标记一个版本
- **版本递增**：自动管理版本号，确保历史完整性

### 权限体系

| 角色 | 权限范围 |
|------|----------|
| **Owner** | 项目所有者，拥有所有权限包括项目删除 |
| **Admin** | 项目管理员，可管理成员和所有读写操作 |
| **Editor** | 编辑者，可创建和编辑提示词及版本 |
| **Viewer** | 查看者，仅可查看项目和提示词 |

## 安装

```bash
# 使用 pip 安装
pip install langprompt-python

# 使用 uv 安装（推荐）
uv pip install langprompt-python
```

## 快速开始

### 基础使用

```python
from langprompt import LangPrompt

# 初始化客户端
client = LangPrompt(
    project_name="my-project",
    api_key="your-api-key"
)

# 获取提示词内容
content = client.prompts.get_prompt(
    prompt_name="greeting",
    label="production"
)

print(content)
```

### 异步使用

```python
from langprompt import AsyncLangPrompt
import asyncio

async def main():
    async with AsyncLangPrompt(
        project_name="my-project",
        api_key="your-api-key"
    ) as client:
        content = await client.prompts.get_prompt(
            prompt_name="greeting",
            label="production"
        )
        print(content)

asyncio.run(main())
```

### 环境变量配置

```bash
export LANGPROMPT_PROJECT_NAME=my-project
export LANGPROMPT_API_KEY=your-api-key
```

然后无需参数初始化：

```python
client = LangPrompt()  # 自动从环境变量读取配置
```

## 使用示例

### 获取项目信息

```python
project = client.projects.get()
print(f"项目名称: {project.name}")
```

### 列出提示词

```python
# 列出所有提示词（分页）
prompts = client.prompts.list(limit=20, offset=0)
print(f"总共 {prompts.total} 个提示词")

for prompt in prompts.items:
    print(f"- {prompt.name}")
```

### 按标签获取提示词

```python
# 获取生产版本
version = client.prompts.get(
    prompt_name="greeting",
    label="production"
)

print(f"版本号: {version.version}")
print(f"内容: {version.content}")
```

### 按版本号获取

```python
version = client.prompts.get(
    prompt_name="greeting",
    version=5
)
```

### 错误处理

```python
from langprompt.exceptions import (
    NotFoundError,
    AuthenticationError,
    PermissionError,
)

try:
    content = client.prompts.get_prompt("greeting", label="production")
except NotFoundError:
    print("提示词不存在")
except AuthenticationError:
    print("认证失败")
except PermissionError:
    print("权限不足")
```

### 启用缓存

```python
client = LangPrompt(
    project_name="my-project",
    api_key="your-api-key",
    enable_cache=True,    # 启用缓存（默认：False）
    cache_ttl=3600       # 缓存时间（秒）
)
```

## 开发指南

### 环境准备

```bash
# 克隆项目
git clone https://github.com/langprompt/langprompt-python.git
cd langprompt-python

# 安装依赖（使用 uv）
uv sync

# 或使用 pip
pip install -e ".[dev]"
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_projects.py

# 查看覆盖率
pytest --cov=langprompt --cov-report=html
```

### 代码规范

```bash
# 格式化代码
ruff format .

# 代码检查
ruff check .

# 类型检查
mypy langprompt
```

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详情。

### 贡献流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](./LICENSE) 文件

## 相关链接

- [LangPrompt 服务端](https://github.com/deku0818/langprompt)
- [设计文档](./docs/langprompt设计文档.md)


## ⚠️注意

本项目是源于探索Vibe Coding的产物，超过99%的代码由AI编写。

此项目存在非常早期的阶段，请勿用于生产环境。

如有问题或建议，欢迎提交 Issue 或 Pull Request。
