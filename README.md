# 计算器系统 · 后端（Calculator Backend）

前后端分离的在线计算器系统的**后端服务**，负责表达式解析与计算、输入校验、
异常处理、计算历史持久化，并对外提供 RESTful API。

> 配套前端仓库：见博客中的「前端 GitHub 仓库」链接。

## 一、项目介绍

本服务是整个计算器系统的「大脑」：

- 前端只负责界面交互与结果展示；
- 所有数学运算、表达式合法性校验、异常判断都在本服务完成；
- 每一次成功计算都会写入 SQLite 数据库，前端可随时查询与删除。

核心原则：**前端不参与任何计算，只发送表达式字符串。**

## 二、技术栈

| 项目 | 选型 |
| --- | --- |
| 语言 | Python 3.8+（开发环境为 Python 3.13） |
| Web 框架 | Flask 3.1 |
| 数据库 | SQLite 3（Python 标准库 `sqlite3`，无需额外安装） |
| 表达式解析 | 自研「词法分析 + 递归下降语法分析」，不使用 `eval` / `exec` |
| 测试 | Python 标准库 `unittest` |

## 三、运行环境

- Python 3.8 及以上版本
- Windows / macOS / Linux 均可运行
- 除 Flask 外无其他第三方依赖，数据库使用 Python 内置的 SQLite

## 四、安装方式

```bash
# 1. 进入后端项目目录
cd 24126942_calculator_backend

# 2. （推荐）创建虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

## 五、数据库初始化方式

**无需手动初始化。**

服务启动时会自动创建数据库文件和 `calculation_history` 表（幂等操作，重复启动不会报错）：

```
data/calculator.db          # SQLite 数据库文件（首次启动自动生成）
```

表结构：

```sql
CREATE TABLE IF NOT EXISTS calculation_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    expression  TEXT    NOT NULL,
    result      TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
```

如果需要重置数据库，直接删除 `data/calculator.db` 后重新启动服务即可。

## 六、启动方式

```bash
python run.py
```

启动成功后终端会输出：

```
 * Running on http://127.0.0.1:5000
```

访问 <http://127.0.0.1:5000/api/health> 应返回：

```json
{ "success": true, "service": "calculator-backend", "status": "UP" }
```

## 七、配置说明

所有配置通过环境变量传入，均带有合理默认值，不配置也能直接运行：

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `CALCULATOR_HOST` | 监听地址 | `127.0.0.1` |
| `CALCULATOR_PORT` | 监听端口 | `5000` |
| `CALCULATOR_DB_PATH` | SQLite 数据库文件路径 | `data/calculator.db` |
| `CALCULATOR_TZ_OFFSET` | 记录时间相对 UTC 的小时偏移，例如 `8` 表示东八区 | 服务器本地时区 |

示例（让局域网内其他设备也能访问）：

```bash
CALCULATOR_HOST=0.0.0.0 python run.py
```

## 八、API 说明

所有接口统一返回 JSON，格式约定如下：

- 成功：`{ "success": true, ...业务字段 }`
- 失败：`{ "success": false, "message": "错误说明", "code": "错误码" }`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/calculate` | 计算表达式并写入历史 |
| `GET` | `/api/history` | 查询历史（支持 `keyword`、`page`、`pageSize`） |
| `DELETE` | `/api/history/{id}` | 删除指定历史记录 |
| `DELETE` | `/api/history` | 清空全部历史（扩展功能） |
| `GET` | `/api/statistics` | 计算统计信息（扩展功能） |
| `GET` | `/api/health` | 健康检查 |

### 1. 计算表达式

```http
POST /api/calculate
Content-Type: application/json

{ "expression": "(1+2)*3" }
```

成功响应（HTTP 200）：

```json
{
  "success": true,
  "expression": "(1+2)*3",
  "result": 9,
  "id": 1,
  "createdAt": "2026-10-06 10:20:00"
}
```

失败响应（HTTP 400）：

```json
{ "success": false, "message": "除数不能为 0", "code": "DIVISION_BY_ZERO" }
```

### 2. 查询历史

```http
GET /api/history?keyword=1%2B2&page=1&pageSize=10
```

```json
{
  "success": true,
  "items": [
    { "id": 3, "expression": "1+2", "result": "3", "createdAt": "2026-10-06 10:22:00" }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10,
  "totalPages": 1,
  "keyword": "1+2"
}
```

### 3. 删除历史

```http
DELETE /api/history/3
```

成功返回 200；记录不存在返回 404：

```json
{ "success": false, "message": "历史记录 3 不存在", "code": "NOT_FOUND" }
```

### 4. 计算统计（扩展功能）

```json
{
  "success": true,
  "statistics": {
    "total": 12,
    "today": 8,
    "operators": { "+": 5, "*": 4, "/": 3 },
    "mostUsedOperator": "+",
    "mostUsedCount": 5
  }
}
```

## 九、支持的表达式语法

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| 四则运算 | `+ - * /` | `12+8`、`10/4` |
| 取模 | `%` | `10%3` |
| 幂运算 | `^` 或 `**`，右结合 | `2^10`、`2^-1` |
| 括号 | 改变运算优先级 | `(1+2)*3` |
| 一元正负号 | 可出现在任意位置 | `-5+8`、`3*-2` |
| 小数 | 支持 `.5` 写法 | `0.1+0.2` |
| 常量 | `pi`、`e`、`tau` | `2*pi` |
| 一元函数 | `sqrt cbrt abs sin cos tan asin acos atan ln log log2 exp floor ceil round fact` | `sqrt(16)`、`fact(5)` |
| 二元函数 | `pow hypot max min mod` | `pow(2,10)`、`max(3,8)` |

非法输入会返回明确的错误信息，例如：

| 输入 | 返回的错误码 | 提示信息 |
| --- | --- | --- |
| `1/0` | `DIVISION_BY_ZERO` | 除数不能为 0 |
| `1+` | `EXPRESSION_SYNTAX_ERROR` | 表达式不完整 |
| `(1+2` | `EXPRESSION_SYNTAX_ERROR` | 括号不匹配，缺少 ')' |
| `abc` | `UNKNOWN_IDENTIFIER` | 未知的常量或函数 'abc' |
| `1@2` | `UNSUPPORTED_CHARACTER` | 表达式包含不支持的字符 '@' |

## 十、运行测试

```bash
python -m unittest discover -s tests -t . -v
```

测试覆盖表达式解析、优先级、括号、一元运算、小数、除零、非法输入、
注入防护，以及计算 / 查询 / 删除 / 统计等接口。

## 十一、前后端连接方式

1. 先启动后端：`python run.py`（默认监听 `127.0.0.1:5000`）；
2. 再打开前端页面，前端默认请求 `http://127.0.0.1:5000/api`；
3. 如果后端部署在其他地址，可以在前端 URL 后追加 `?api=` 参数指定，例如：

   ```
   calculator.html?api=http://192.168.1.10:5000/api
   ```

后端已开启 CORS（`Access-Control-Allow-Origin: *`），允许前端与服务端分离部署。

## 十二、项目结构

```
24126942_calculator_backend/
├── src/
│   ├── app.py                    # Flask 应用工厂：注册蓝图、异常处理、CORS
│   ├── controller/               # 控制器层：接收请求、参数校验
│   │   ├── calculate_controller.py
│   │   └── history_controller.py
│   ├── service/                  # 业务层：计算、历史、统计
│   │   ├── expression_parser.py  # 自研表达式解析器（词法 + 递归下降）
│   │   ├── calculator_service.py
│   │   ├── history_service.py
│   │   └── statistics_service.py
│   ├── model/                    # 数据层：数据库连接与 SQL
│   │   ├── database.py
│   │   └── history_repository.py
│   └── utils/                    # 通用工具：响应格式、异常、时间
│       ├── api_response.py
│       ├── exceptions.py
│       └── timeutil.py
├── tests/                        # 单元测试与接口测试
├── data/                         # SQLite 数据库文件目录（自动生成）
├── run.py                        # 启动入口
├── requirements.txt
├── README.md
└── codestyle.md
```

## 十三、安全说明

本项目**没有**使用 `eval`、`exec` 或任何等价的动态代码执行方式。

解析器只识别有限的运算符、函数与常量：词法分析阶段会拒绝所有不认识的字符，
语法分析阶段会拒绝不符合文法的结构。因此像
`__import__('os').system('...')` 这类输入会在解析阶段直接报错，
不存在代码注入风险。
