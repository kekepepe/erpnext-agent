"""Minimal authenticated ERPNext REST client for disposable Phase 0 scripts."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Any


class ERPNextAPI:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar)
        )

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"ERPNext API {method} {path} failed with HTTP {error.code}: {detail}"
            ) from error

    def login(self, username: str, password: str) -> None:
        data = urllib.parse.urlencode({"usr": username, "pwd": password}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/api/method/login", data=data, method="POST"
        )
        try:
            with self.opener.open(request, timeout=30) as response:
                result = json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ERPNext login failed: {detail}") from error
        if result.get("message") != "Logged In":
            raise RuntimeError("ERPNext login did not return the expected result")

    @staticmethod
    def resource_path(doctype: str, name: str | None = None) -> str:
        path = f"/api/resource/{urllib.parse.quote(doctype, safe='')}"
        if name is not None:
            path += f"/{urllib.parse.quote(name, safe='')}"
        return path

    def get_doc(self, doctype: str, name: str) -> dict[str, Any] | None:
        path = self.resource_path(doctype, name)
        request = urllib.request.Request(f"{self.base_url}{path}", method="GET")
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)["data"]
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"ERPNext API GET {doctype} {name} failed: {detail}"
            ) from error

    def insert(self, doctype: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", self.resource_path(doctype), payload)["data"]

    def list_docs(
        self,
        doctype: str,
        fields: list[str],
        filters: list[list[Any]],
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = urllib.parse.urlencode(
            {
                "fields": json.dumps(fields),
                "filters": json.dumps(filters),
                "limit_page_length": limit,
            }
        )
        result = self.request("GET", f"{self.resource_path(doctype)}?{query}")
        return result["data"]

    def call(self, method: str, payload: dict[str, Any]) -> Any:
        result = self.request(
            "POST", f"/api/method/{urllib.parse.quote(method, safe='.')}", payload
        )
        return result.get("message")

    def submit(self, document: dict[str, Any]) -> dict[str, Any]:
        return self.call("frappe.client.submit", {"doc": document})
