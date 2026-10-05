"""接口层集成测试：覆盖计算、历史查询、删除与清空。"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

TEMP_DB = os.path.join(tempfile.mkdtemp(), "test_calculator.db")
os.environ["CALCULATOR_DB_PATH"] = TEMP_DB

from app import create_app  # noqa: E402


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()
        self.client.delete("/api/history")

    def test_calculate_success(self):
        response = self.client.post("/api/calculate", json={"expression": "(1+2)*3"})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["result"], 9)
        self.assertEqual(body["expression"], "(1+2)*3")

    def test_calculate_invalid_expression(self):
        response = self.client.post("/api/calculate", json={"expression": "1+"})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_calculate_division_by_zero(self):
        response = self.client.post("/api/calculate", json={"expression": "5/0"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "DIVISION_BY_ZERO")

    def test_calculate_missing_field(self):
        response = self.client.post("/api/calculate", json={})
        self.assertEqual(response.status_code, 400)

    def test_history_flow(self):
        self.client.post("/api/calculate", json={"expression": "1+1"})
        self.client.post("/api/calculate", json={"expression": "2*2"})

        body = self.client.get("/api/history").get_json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["items"][0]["expression"], "2*2")

        record_id = body["items"][0]["id"]
        self.assertEqual(self.client.delete(f"/api/history/{record_id}").status_code, 200)
        self.assertEqual(self.client.get("/api/history").get_json()["total"], 1)

        self.assertEqual(self.client.delete("/api/history/999999").status_code, 404)

    def test_history_search_and_pagination(self):
        for index in range(12):
            self.client.post("/api/calculate", json={"expression": f"{index}+1"})

        first_page = self.client.get("/api/history?page=1&pageSize=5").get_json()
        self.assertEqual(len(first_page["items"]), 5)
        self.assertEqual(first_page["totalPages"], 3)

        searched = self.client.get("/api/history?keyword=11%2B1").get_json()
        self.assertEqual(searched["total"], 1)

    def test_statistics(self):
        self.client.post("/api/calculate", json={"expression": "3*4"})
        statistics = self.client.get("/api/statistics").get_json()["statistics"]
        self.assertGreaterEqual(statistics["total"], 1)
        self.assertEqual(statistics["mostUsedOperator"], "*")

    def test_health(self):
        body = self.client.get("/api/health").get_json()
        self.assertEqual(body["status"], "UP")


if __name__ == "__main__":
    unittest.main()
