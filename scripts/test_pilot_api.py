"""Exercise the W6 contract over HTTP without an ERP site."""

import importlib.util
import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SPEC = importlib.util.spec_from_file_location(
    "phase0_pilot_api", Path(__file__).with_name("phase0-pilot-api.py")
)
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)


class PilotApiTest(unittest.TestCase):
    def setUp(self):
        self.server = pilot.PilotServer(("127.0.0.1", 0))
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.thread.join, 2)
        self.addCleanup(self.server.shutdown)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.draft = {
            "kind": "purchase_receipt",
            "companyId": "demo-company",
            "partnerId": "demo-supplier-01",
            "postingDate": "2026-11-23",
            "lines": [{
                "productId": "DEMO-BOLT-01", "warehouseId": "demo-warehouse-main", "quantity": "12"
            }],
        }

    def request(self, method, path, body=None, key=None, **headers):
        request = Request(self.origin + pilot.PREFIX + path, method=method, headers=headers)
        if body is not None:
            request.data = json.dumps(body).encode()
            request.add_header("Content-Type", "application/json")
        if key is not None:
            request.add_header("Idempotency-Key", key)
        try:
            response = urlopen(request, timeout=2)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_options_scope_partners_and_save_both_kinds(self):
        for kind, partner in (("purchase_receipt", "demo-supplier-01"),
                              ("sales_delivery", "demo-customer-01")):
            with self.subTest(kind=kind):
                status, options = self.request("GET", f"/entry-options?kind={kind}")
                self.assertEqual(status, 200)
                self.assertEqual(options["data"]["partners"][0]["id"], partner)
                status, response = self.request(
                    "POST", "/drafts", dict(self.draft, kind=kind, partnerId=partner), key=kind
                )
                self.assertEqual(status, 201)
                saved = response["data"]
                self.assertEqual(saved["status"], "draft")
                self.assertEqual(saved["revision"], 1)
                self.assertEqual(self.request("GET", f"/drafts/{saved['id']}"), (200, response))

    def test_concurrent_replay_and_conflicting_payload(self):
        with ThreadPoolExecutor(2) as pool:
            first = pool.submit(self.request, "POST", "/drafts", self.draft, "create")
            second = pool.submit(self.request, "POST", "/drafts", self.draft, "create")
            self.assertEqual(first.result()[0], 201)
            self.assertEqual(first.result(), second.result())
        changed = dict(self.draft, postingDate="2026-11-24")
        status, response = self.request("POST", "/drafts", changed, key="create")
        self.assertEqual((status, response["error"]["code"]), (409, "IDEMPOTENCY_CONFLICT"))

    def test_update_replay_and_stale_revision_keep_current_record(self):
        _, created = self.request("POST", "/drafts", self.draft, key="create")
        path = f"/drafts/{created['data']['id']}"
        change = dict(self.draft, postingDate="2026-11-24", revision=1)
        update = self.request("PUT", path, change, key="update")
        self.assertEqual(update[0], 200)
        self.assertEqual(update[1]["data"]["revision"], 2)
        self.assertEqual(self.request("PUT", path, change, key="update"), update)
        status, error = self.request("PUT", path, change, key="stale")
        self.assertEqual((status, error["error"]["code"]), (409, "STALE_REVISION"))
        self.assertEqual(self.request("GET", path), update)

    def test_rejects_foreign_origin_and_invalid_form(self):
        status, _ = self.request("POST", "/drafts", self.draft, key="create",
                                 Origin="https://example.invalid")
        self.assertEqual(status, 403)
        invalid = dict(self.draft, partnerId="demo-customer-01", status="submitted",
                       lines=[dict(self.draft["lines"][0], quantity="0", warehouseId="unknown")])
        status, response = self.request("POST", "/drafts", invalid, key="create")
        self.assertEqual(status, 422)
        self.assertEqual({item["path"] for item in response["error"]["issues"]},
                         {"status", "partnerId", "lines.0.quantity", "lines.0.warehouseId"})
        self.assertEqual(self.request("POST", "/drafts", self.draft, key="create")[0], 201)


if __name__ == "__main__":
    unittest.main()
