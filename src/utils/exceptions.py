"""业务异常定义。

所有可预期的错误（表达式非法、除零、记录不存在等）都通过异常向上抛出，
由统一异常处理器转换成标准 JSON 响应，避免在控制器里写大量 if/else。
"""


class AppError(Exception):
    """业务异常基类。"""

    code = "APP_ERROR"
    status = 400

    def __init__(self, message: str, code: str = None, status: int = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status:
            self.status = status


class ValidationError(AppError):
    """输入校验失败，对应 HTTP 400。"""

    code = "VALIDATION_ERROR"
    status = 400


class NotFoundError(AppError):
    """资源不存在，对应 HTTP 404。"""

    code = "NOT_FOUND"
    status = 404
