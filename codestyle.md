# 后端代码规范（Python / Flask）

## 规范来源

本文档的规则来源于以下公开的、被广泛认可的官方或社区标准：

1. [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)（Python 官方编码风格指南）
2. [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)（文档字符串约定）
3. [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)（Google 的 Python 编码规范）
4. [The Zen of Python (PEP 20)](https://peps.python.org/pep-0020/)

本项目的代码在上述通用规范的基础上，补充了少量与本项目结构相关的约定，
以便前后端分离架构下的分工更加清晰。

## 1. 布局与格式

| 项目 | 约定 |
| --- | --- |
| 缩进 | 4 个空格，禁止使用 Tab |
| 行宽 | 单行不超过 88 个字符 |
| 空行 | 顶层函数与类之间空 2 行；类内方法之间空 1 行 |
| 换行 | 优先使用括号进行隐式续行，必要时使用反斜杠 |
| 文件编码 | UTF-8 |
| 文件结尾 | 保留一个空行，去掉多余的空白字符 |

## 2. 命名规范

| 类型 | 规则 | 示例 |
| --- | --- | --- |
| 模块 / 包 | 全小写，单词间用下划线 | `calculator_service.py` |
| 类 | 大驼峰（CapWords） | `CalculatorService`、`ExpressionError` |
| 函数 / 方法 / 变量 | 小写下划线（snake_case） | `calculate()`、`record_id` |
| 常量 | 全大写加下划线 | `MAX_EXPRESSION_LENGTH` |
| 私有成员 | 前缀单个下划线 | `_row_to_dict()`、`self._peek()` |

命名要求见名知意，避免拼音、无意义缩写和单字母命名（循环变量 `i` 等除外）。

## 3. 导入规范

- 导入语句统一放在文件顶部，按「标准库 → 第三方库 → 本项目模块」分组；
- 每组之间空一行；
- 避免使用 `from module import *`；
- 仅用于类型标注的导入放在 `typing` 中声明。

```python
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from flask import Blueprint, request

from service.calculator_service import CalculatorService
from utils.api_response import ok
```

## 4. 注释与文档字符串

- 每一个模块、公开类与公开函数都要有文档字符串（docstring），使用三引号；
- 文档字符串使用中文描述「做什么」和「为什么这样做」；
- 行内注释只解释**为什么**，不重复代码本身；
- 修改代码时同步更新注释，禁止保留与实现不符的注释。

```python
def normalize_expression(expression: str) -> str:
    """去掉多余空白，前端展示与入库都用规范化后的表达式。"""
    return "".join(expression.split())
```

## 5. 类型标注

- 公开函数必须标注参数与返回值类型；
- 类型标注只用于说明，不做运行时强制校验；
- 可选参数使用 `Optional[...]`，容器使用 `List[...]`、`Dict[...]`。

## 6. 分层架构约定

项目采用「控制器 — 服务 — 数据访问」三层结构，各层职责必须严格区分：

| 层 | 目录 | 职责 | 禁止事项 |
| --- | --- | --- | --- |
| 控制器层 | `src/controller/` | 解析请求参数、调用服务、返回统一响应 | 不写业务逻辑、不直接写 SQL |
| 服务层 | `src/service/` | 业务规则、计算、校验、异常抛出 | 不直接操作 HTTP 对象 |
| 数据层 | `src/model/` | 数据库连接与 SQL 语句 | 不写业务判断 |

所有 SQL 语句集中写在 `src/model/history_repository.py`，并使用参数化查询
（`?` 占位符）防止 SQL 注入，禁止通过字符串拼接生成 SQL。

## 7. 错误处理

- 可预期的错误（输入非法、除零、记录不存在）通过自定义异常
  （`utils/exceptions.py`）抛出，由 `app.py` 中的统一异常处理器转换为 JSON 响应；
- 禁止使用裸 `except:`，至少要捕获 `Exception`；
- 捕获异常后要么处理，要么重新抛出，禁止静默忽略；
- 面向用户的错误信息要清楚、可读，不暴露堆栈与内部实现细节。

## 8. 安全规范

- **禁止**使用 `eval`、`exec`、`compile` 等动态执行用户输入的方式；
- 用户输入在进入计算前必须经过长度、类型与字符合法性校验；
- 数据库操作必须使用参数化查询；
- 表达式解析器只允许白名单内的函数与常量。

## 9. 测试规范

- 测试文件放在 `tests/` 目录下，命名以 `test_` 开头；
- 使用 Python 标准库 `unittest`，测试之间互相独立；
- 测试不仅要覆盖正常路径，还要覆盖边界与异常路径（除零、非法字符、超长表达式等）；
- 新增功能时应同步补充测试用例。

## 10. 提交规范

- 提交信息使用简洁的祈使句，说明本次改动的内容；
- 不提交数据库文件、虚拟环境目录、编辑器配置文件；
- 提交前确保 `python -m unittest discover -s tests -t . -v` 全部通过。
