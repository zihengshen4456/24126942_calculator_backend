"""Flask 应用工厂：注册蓝图、统一异常处理、跨域配置。"""

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from controller.calculate_controller import calculate_blueprint
from controller.history_controller import history_blueprint
from model.database import init_database
from utils.api_response import fail
from utils.exceptions import AppError


def create_app() -> Flask:
    app = Flask(__name__)
    app.json.ensure_ascii = False

    init_database()

    app.register_blueprint(calculate_blueprint)
    app.register_blueprint(history_blueprint)

    _register_cors(app)
    _register_health_check(app)
    _register_error_handlers(app)

    return app


def _register_cors(app: Flask) -> None:
    """前后端分离部署时需要跨域访问，这里统一加上 CORS 响应头。"""

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        return response

    @app.route("/api/<path:_any>", methods=["OPTIONS"])
    def preflight(_any):  # pragma: no cover - 由浏览器触发
        return "", 204


def _register_health_check(app: Flask) -> None:
    @app.get("/api/health")
    def health():
        return jsonify({"success": True, "service": "calculator-backend", "status": "UP"})

    @app.get("/")
    def index():
        return jsonify(
            {
                "success": True,
                "service": "前后端分离计算器 - 后端服务",
                "endpoints": [
                    "POST   /api/calculate",
                    "GET    /api/history?keyword=&page=1&pageSize=10",
                    "DELETE /api/history/<id>",
                    "DELETE /api/history",
                    "GET    /api/statistics",
                    "GET    /api/health",
                ],
            }
        )


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(error: AppError):
        return fail(error.message, getattr(error, "code", None), error.status)

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return fail(error.description or error.name, error.name.upper().replace(" ", "_"),
                    error.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("未预期的异常: %s", error)
        return fail("服务器内部错误", "INTERNAL_ERROR", 500)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return fail(f"接口 {request.path} 不存在", "NOT_FOUND", 404)
