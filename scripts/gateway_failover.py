#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gateway_failover.py -- New API 双网关故障转移
================================================================
吸收自 Panniantong/Agent-Reach（~66K stars）的 multi-backend fallback 机制：

  Agent-Reach 的 transcribe 按优先级逐个尝试转写后端，首个成功即返回；
  本模块把同一语义落到 Agnes 网关层：omarchy 本机 New API
  （127.0.0.1:13000）为主，黑苹果 New API 等为备——主网关出现端点级
  故障（连不上/超时/5xx/429）时自动切到下一个，调用方只调一个入口。

  切换规则（只对"端点故障"切换，不对"请求错误"切换）：
    - 连接失败 / 超时 / HTTP 502/503/504 / HTTP 429  -> 换下一个端点
    - 其他 4xx（400/401/403/404…）                  -> 请求本身问题，直接返回
  全部端点都故障 -> 抛 AllGatewaysFailed（带 attempts 明细）。

端点配置（kind = "chat" | "image"）：
  AGNES_CHAT_BASE_URLS / AGNES_IMAGE_BASE_URLS   逗号分隔，全量覆盖（最高优先级）
  AGNES_CHAT_BASE_URL  / AGNES_IMAGE_BASE_URL    主端点
  AGNES_CHAT_FALLBACK_URLS / AGNES_IMAGE_FALLBACK_URLS  逗号分隔，备选端点
  兜底：load_credentials()[0]，再兜底 http://127.0.0.1:13000/v1

  例：AGNES_CHAT_FALLBACK_URLS="http://100.84.255.7:13000/v1"

用法：
    from gateway_failover import post_with_failover
    res = post_with_failover("/chat/completions", payload, kind="chat")

职责划分（与 /api/gateway/health 的 probe_gateway）：
  - 本模块 / agnes_engine.call_agnes：调用时的主动容错。端点级故障
    （连不上/超时/5xx/429）自动切换端点，对调用方透明；
    面向机器的自愈，不面向人展示。
  - /api/gateway/health：被动探活。GET <base>/models，不触发模型推理，
    返回 reachable/latency/model 清单；面向人/UI 的健康展示。
  两者正交：健康检查回答"网关现在好不好"，故障转移保证"调用时坏了
  自动换路"。本模块不替代健康检查，健康检查也不做调用时切换。
"""

from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from agnes_engine import load_credentials
except ImportError:  # pragma: no cover -- 单独使用时降级
    load_credentials = None  # type: ignore

try:
    from agnes_gateway import load_gateway
except ImportError:  # pragma: no cover -- 单独使用时降级
    load_gateway = None  # type: ignore

DEFAULT_BASE = "http://127.0.0.1:13000/v1"

#: 触发故障转移的 HTTP 状态码：网关坏了 / 被限流了
FAILOVER_STATUSES = {429, 502, 503, 504}


class AllGatewaysFailed(RuntimeError):
    """所有网关端点都故障。"""


def _split_urls(raw: str | None) -> list[str]:
    return [u.strip().rstrip("/") for u in (raw or "").split(",") if u.strip()]


def _dedup(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def resolve_endpoints(kind: str = "chat", key_path: Path | str | None = None) -> list[str]:
    """解析 kind 对应的网关端点列表（优先级从高到低，去重）。"""
    if kind not in ("chat", "image"):
        raise ValueError("kind 必须为 chat 或 image")
    prefix = "AGNES_CHAT" if kind == "chat" else "AGNES_IMAGE"

    # 1. 全量覆盖
    urls = _split_urls(os.environ.get(prefix + "_BASE_URLS"))
    if urls:
        return _dedup(urls)

    # 2. 主 + 备选拼接
    primary = (
        os.environ.get(prefix + "_BASE_URL")
        or os.environ.get("AGNES_BASE_URL")
        or os.environ.get("NEW_API_BASE_URL")
        or ""
    ).strip().rstrip("/")
    if not primary:
        resolver = load_credentials if kind == "chat" else (load_gateway or load_credentials)
        if callable(resolver):
            try:
                try:
                    res_tuple = resolver(key_path=key_path)
                except TypeError:
                    res_tuple = resolver()
                primary = (res_tuple[0] or "").strip().rstrip("/")
            except Exception:
                primary = ""
    fallbacks = _split_urls(os.environ.get(prefix + "_FALLBACK_URLS"))
    urls = _dedup([u for u in [primary] + fallbacks if u])
    return urls or [DEFAULT_BASE]


def _default_http_post(url: str, payload: dict, key: str | None,
                       timeout: int) -> tuple[int, dict]:
    """默认 POST 实现：返回 (status, data)。HTTPError 转为返回值，不抛错。"""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "User-Agent": "AgnesStudio-GatewayFailover/1.0",
                 **({"Authorization": "Bearer %s" % key} if key else {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8", "ignore") or "{}")
        except Exception:
            data = {"error": str(e)}
        finally:
            try:
                e.close()
            except Exception:
                pass
        return e.code, data
    # URLError / socket.timeout 等继续上抛，由 post_with_failover 归类为端点故障


def post_with_failover(
    path: str,
    payload: dict,
    *,
    kind: str = "chat",
    timeout: int = 30,
    api_key: str | None = None,
    key_resolver: Callable[..., tuple] | None = None,
    http_post: Callable | None = None,
    first_endpoint: str | None = None,
    key_path: Path | str | None = None,
) -> dict:
    """带故障转移的 POST。

    返回 {"ok", "status", "data", "endpoint_used", "attempts"}；
    attempts 为 [{"endpoint", "ok", "status"|"error"}]。
    全部端点故障时抛 AllGatewaysFailed。
    first_endpoint: 显式指定的端点排首位（请求级覆盖高于环境链）。
    """
    endpoints = resolve_endpoints(kind, key_path=key_path)
    if first_endpoint and str(first_endpoint).strip():
        fe = str(first_endpoint).strip().rstrip("/")
        endpoints = [fe] + [u for u in endpoints if u != fe]
    post = http_post or _default_http_post
    if api_key is None:
        resolver = key_resolver
        if resolver is None:
            resolver = load_credentials if kind == "chat" else (load_gateway or load_credentials)
        if callable(resolver):
            try:
                try:
                    res_tuple = resolver(key_path=key_path)
                except TypeError:
                    res_tuple = resolver()
                api_key = res_tuple[1]
            except Exception:
                api_key = None

    attempts: list[dict] = []
    last_err: str | None = None
    for ep in endpoints:
        url = ep + path
        try:
            status, data = post(url, payload, api_key, timeout)
        except (urllib.error.URLError, socket.timeout, TimeoutError,
                ConnectionError, OSError) as e:
            # 端点级故障：连不上 / 超时 -> 换下一个
            last_err = "%s: %s" % (type(e).__name__, str(e)[:160])
            attempts.append({"endpoint": ep, "ok": False, "error": last_err})
            continue
        attempts.append({"endpoint": ep, "ok": True, "status": status})
        if status in FAILOVER_STATUSES:
            last_err = "HTTP %s" % status
            continue  # 端点故障 -> 换下一个
        return {"ok": 200 <= status < 300, "status": status, "data": data,
                "endpoint_used": ep, "attempts": attempts}
    raise AllGatewaysFailed(
        "所有网关端点均故障 (%s): %s"
        % (kind, "; ".join("%s[%s]" % (a["endpoint"], a.get("error") or a.get("status"))
                           for a in attempts) or last_err))


def doctor(
    kind: str = "chat",
    timeout: int = 5,
    key_path: Path | str | None = None,
) -> dict[str, dict]:
    """对每个端点 GET /models 探活；单个端点异常不拖垮整体。

    状态语义：
      ok    - 200，网关健康
      warn  - 401/403，网关可达但需认证（key 未配或无效）
      error - 其他（连不上/超时/5xx…）
    """
    results: dict[str, dict] = {}
    for ep in resolve_endpoints(kind, key_path=key_path):
        try:
            req = urllib.request.Request(
                ep + "/models", method="GET",
                headers={"User-Agent": "AgnesStudio-GatewayFailover/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
        except urllib.error.HTTPError as e:
            # HTTPError 说明 TCP 通、网关活着：401/403 只是缺 key
            status = e.code
            try:
                e.close()
            except Exception:
                pass
        except Exception as e:  # noqa: BLE001 -- doctor 必须扛住任何端点
            results[ep] = {"status": "error",
                           "message": "%s: %s" % (type(e).__name__, str(e)[:160])}
            continue
        if status == 200:
            results[ep] = {"status": "ok", "message": "HTTP 200"}
        elif status in (401, 403):
            results[ep] = {"status": "warn",
                           "message": "网关可达，需认证（HTTP %s）" % status}
        else:
            results[ep] = {"status": "error", "message": "HTTP %s" % status}
    return results


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description="New API 网关故障转移探活")
    ap.add_argument("--kind", default="chat", choices=["chat", "image"])
    ap.add_argument("--key-path", default=None, help="自定义 key JSON 路径")
    ap.add_argument("--doctor", action="store_true", help="探活所有端点")
    a = ap.parse_args(argv)
    if a.doctor:
        print(json.dumps(doctor(a.kind, key_path=a.key_path), ensure_ascii=False, indent=2))
        return
    print(json.dumps({"endpoints": resolve_endpoints(a.kind, key_path=a.key_path)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
