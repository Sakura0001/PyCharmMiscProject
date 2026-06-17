#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import html
import json
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from largeslb_fuzz import Dsn


@dataclass(frozen=True)
class FuzzLaunchConfig:
    primary_dsn: str
    readonly_dsn: str
    state_dir: str
    seed: str = ""
    workers: str = "4"
    duration: str = "0"
    run_id: str = ""
    bucket_count: str = "16"
    rows_per_bucket: str = "2048"
    target_fields: str = "char_255,varchar_16383,text_col,mediumtext_col,longtext_col,blob_col,mediumblob_col,longblob_col"
    readonly_check_rate: str = "0.05"
    replica_timeout: str = "300"
    replica_poll_interval: str = "1"
    update_chunk_size: str = "256"
    query_chunk_size: str = "512"
    sleep_ms: str = "0"
    engine_metric_interval: str = "60"
    reconnect_sleep: str = "5"
    max_reconnect_seconds: str = "0"
    verbose: bool = False
    init_only: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FuzzLaunchConfig":
        values = {}
        bool_fields = {"verbose", "init_only"}
        for field in dataclasses.fields(cls):
            raw = data.get(field.name, field.default)
            if field.name in bool_fields:
                if isinstance(raw, bool):
                    values[field.name] = raw
                elif isinstance(raw, str):
                    values[field.name] = raw.strip().lower() in ("1", "true", "yes", "on")
                else:
                    values[field.name] = bool(raw)
            else:
                values[field.name] = str(raw).strip()
        for required in ("primary_dsn", "readonly_dsn", "state_dir"):
            if not values.get(required):
                raise ValueError(f"{required} is required")
        return cls(**values)


def build_fuzz_command(
    fuzzer_path: Path,
    config: FuzzLaunchConfig,
) -> Tuple[List[str], List[str]]:
    command = [
        "python3",
        "-u",
        str(fuzzer_path),
        "--primary-dsn",
        config.primary_dsn,
        "--readonly-dsn",
        config.readonly_dsn,
        "--state-dir",
        config.state_dir,
        "--workers",
        config.workers,
        "--duration",
        config.duration,
        "--bucket-count",
        config.bucket_count,
        "--rows-per-bucket",
        config.rows_per_bucket,
        "--target-fields",
        config.target_fields,
        "--readonly-check-rate",
        config.readonly_check_rate,
        "--replica-timeout",
        config.replica_timeout,
        "--replica-poll-interval",
        config.replica_poll_interval,
        "--update-chunk-size",
        config.update_chunk_size,
        "--query-chunk-size",
        config.query_chunk_size,
        "--sleep-ms",
        config.sleep_ms,
        "--engine-metric-interval",
        config.engine_metric_interval,
        "--reconnect-sleep",
        config.reconnect_sleep,
        "--max-reconnect-seconds",
        config.max_reconnect_seconds,
    ]
    if config.seed:
        command.extend(["--seed", config.seed])
    if config.run_id:
        command.extend(["--run-id", config.run_id])
    if config.verbose:
        command.append("--verbose")
    if config.init_only:
        command.append("--init-only")

    redacted = list(command)
    for i, item in enumerate(redacted):
        if item in ("--primary-dsn", "--readonly-dsn") and i + 1 < len(redacted):
            redacted[i + 1] = redact_dsn(redacted[i + 1])
    return command, redacted


def redact_dsn(value: str) -> str:
    try:
        return Dsn.parse(value).redacted()
    except Exception:
        if "@" not in value or ":" not in value:
            return value
        prefix, suffix = value.rsplit("@", 1)
        user = prefix.split("//", 1)[-1].split(":", 1)[0]
        scheme = prefix.split("//", 1)[0] + "//" if "//" in prefix else ""
        return f"{scheme}{user}:***@{suffix}"


class LogBuffer:
    def __init__(self, limit: int = 800):
        self.limit = limit
        self._lines: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def append(self, line: str) -> None:
        text = line.rstrip("\n")
        lowered = text.lower()
        level = "INFO"
        if any(token in lowered for token in ("error", "failure", "traceback", "assert", "corrupt")):
            level = "ERROR"
        elif "warning" in lowered or "warn" in lowered:
            level = "WARN"
        record = {
            "ts": utc_now(),
            "level": level,
            "text": text,
            "anomaly": level == "ERROR",
        }
        with self._lock:
            self._lines.append(record)
            if len(self._lines) > self.limit:
                self._lines = self._lines[-self.limit :]

    def snapshot(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            lines = list(self._lines)
        if limit:
            return lines[-limit:]
        return lines


def collect_failures(state_dir: Path, limit: int = 20) -> List[Dict[str, Any]]:
    failures_root = state_dir / "failures"
    if not failures_root.exists():
        return []
    result: List[Dict[str, Any]] = []
    for failure_dir in sorted(
        [path for path in failures_root.iterdir() if path.is_dir()],
        key=lambda path: path.name,
        reverse=True,
    ):
        failure_file = failure_dir / "failure.json"
        if not failure_file.exists():
            continue
        try:
            data = json.loads(failure_file.read_text(encoding="utf-8"))
            result.append(summarize_failure(failure_dir, data))
        except Exception as exc:
            result.append(
                {
                    "path": str(failure_dir),
                    "kind": "failure_parse_error",
                    "message": str(exc),
                    "op_id": "",
                    "scenario": "",
                    "where": f"无法解析 {failure_file}",
                    "details": {},
                }
            )
        if len(result) >= limit:
            break
    return result


def summarize_failure(failure_dir: Path, failure: Dict[str, Any]) -> Dict[str, Any]:
    details = failure.get("details") or {}
    plan = failure.get("plan") or {}
    extra = failure.get("extra") or {}
    op_id = plan.get("op_id") or details.get("op_id") or failure.get("op_id") or ""
    scenario = plan.get("kind") or plan.get("scenario") or ""
    where_parts = []
    if scenario:
        where_parts.append(f"scenario={scenario}")
    if plan.get("target_field"):
        where_parts.append(f"target_field={plan['target_field']}")
    if plan.get("payload_len") is not None:
        where_parts.append(f"payload_len={plan['payload_len']}")
    if op_id:
        where_parts.append(f"op_id={op_id}")
    if "row_id" in details:
        where_parts.append(f"row_id={details['row_id']}")
    if "mismatches" in details and isinstance(details["mismatches"], dict):
        where_parts.append("field=" + ",".join(sorted(details["mismatches"].keys())))
    if "visibility" in details:
        where_parts.append(f"visibility={details['visibility']}")
    selected_rows = extra.get("selected_rows") or []
    if selected_rows:
        buckets = sorted({str(item.get("bucket")) for item in selected_rows if "bucket" in item})
        if buckets:
            where_parts.append("bucket=" + ",".join(buckets[:8]))
    return {
        "path": str(failure_dir),
        "kind": failure.get("kind", "unknown"),
        "message": failure.get("message", ""),
        "op_id": op_id,
        "scenario": scenario,
        "where": " | ".join(where_parts) if where_parts else str(failure_dir),
        "details": details,
        "ts": failure.get("ts", ""),
    }


class FuzzProcessManager:
    def __init__(self, fuzzer_path: Path):
        self.fuzzer_path = fuzzer_path
        self.logs = LogBuffer()
        self._process: Optional[subprocess.Popen[str]] = None
        self._reader: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._started_at = ""
        self._state_dir: Optional[Path] = None
        self._redacted_command: List[str] = []
        self._exit_code: Optional[int] = None

    def start(self, config: FuzzLaunchConfig) -> Dict[str, Any]:
        with self._lock:
            if self.is_running_locked():
                raise RuntimeError("fuzzer is already running")
            Path(config.state_dir).mkdir(parents=True, exist_ok=True)
            command, redacted = build_fuzz_command(self.fuzzer_path, config)
            self.logs.append("$ " + " ".join(redacted))
            self._process = subprocess.Popen(
                command,
                cwd=str(self.fuzzer_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            self._started_at = utc_now()
            self._state_dir = Path(config.state_dir)
            self._redacted_command = redacted
            self._exit_code = None
            self._reader = threading.Thread(target=self._read_output, daemon=True)
            self._reader.start()
            return self.status()

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None:
                return self.status()
            self.logs.append("INFO stopping fuzz process")
            process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.logs.append("WARNING terminate timed out; killing fuzz process")
            process.kill()
            process.wait(timeout=10)
        with self._lock:
            self._exit_code = process.returncode
        return self.status()

    def status(self) -> Dict[str, Any]:
        with self._lock:
            running = self.is_running_locked()
            process = self._process
            if process is not None and not running:
                self._exit_code = process.poll()
            state_dir = self._state_dir
            failures = collect_failures(state_dir) if state_dir else []
            latest_failure = failures[0] if failures else None
            return {
                "running": running,
                "pid": process.pid if process is not None and running else None,
                "started_at": self._started_at,
                "exit_code": self._exit_code,
                "state_dir": str(state_dir) if state_dir else "",
                "command": self._redacted_command,
                "logs": self.logs.snapshot(limit=200),
                "failures": failures,
                "latest_failure": latest_failure,
            }

    def is_running_locked(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def _read_output(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            self.logs.append(line)
        with self._lock:
            self._exit_code = process.poll()
        self.logs.append(f"INFO fuzz process exited code={self._exit_code}")


class ConsoleHandler(BaseHTTPRequestHandler):
    manager: FuzzProcessManager

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self.send_html(INDEX_HTML)
            return
        if self.path.startswith("/api/status"):
            self.send_json(self.manager.status())
            return
        self.send_error(404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/start":
                payload = self.read_json()
                config = FuzzLaunchConfig.from_dict(payload)
                self.send_json(self.manager.start(config))
                return
            if self.path == "/api/stop":
                self.send_json(self.manager.stop())
                return
            self.send_error(404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def make_handler(manager: FuzzProcessManager) -> type[ConsoleHandler]:
    class BoundConsoleHandler(ConsoleHandler):
        pass

    BoundConsoleHandler.manager = manager
    return BoundConsoleHandler


def utc_now() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local web console for LargeSLB fuzz runner.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--fuzzer-path",
        default=str(Path(__file__).with_name("largeslb_fuzz.py")),
        help="Path to largeslb_fuzz.py",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    manager = FuzzProcessManager(Path(args.fuzzer_path).resolve())
    server = ThreadingHTTPServer((args.host, args.port), make_handler(manager))
    url = f"http://{args.host}:{args.port}"
    print(f"LargeSLB fuzz console listening on {html.escape(url)}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        manager.stop()
    finally:
        server.server_close()
    return 0


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LargeSLB Fuzz 控制台</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #1f2933;
      --muted: #64707d;
      --line: #d8dde5;
      --accent: #0f766e;
      --danger: #b42318;
      --warn: #a15c07;
      --ok: #16703b;
      --code: #111827;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 22px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }
    h1, h2 { margin: 0; letter-spacing: 0; }
    h1 { font-size: 20px; }
    h2 { font-size: 15px; }
    main {
      display: grid;
      grid-template-columns: minmax(340px, 430px) minmax(0, 1fr);
      gap: 16px;
      padding: 16px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }
    .stack { display: grid; gap: 16px; }
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    label { display: grid; gap: 4px; color: var(--muted); font-size: 12px; }
    input {
      width: 100%;
      min-width: 0;
      height: 34px;
      padding: 6px 8px;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--ink);
      background: #fff;
      font: inherit;
    }
    input[type="checkbox"] { width: auto; height: auto; }
    .wide { grid-column: 1 / -1; }
    .checks {
      display: flex;
      gap: 16px;
      align-items: center;
      margin-top: 10px;
      color: var(--muted);
    }
    .checks label { display: flex; flex-direction: row; align-items: center; gap: 6px; }
    .actions { display: flex; gap: 10px; margin-top: 12px; }
    button {
      height: 36px;
      padding: 0 14px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      cursor: pointer;
      font: inherit;
    }
    button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
    button.danger { background: var(--danger); border-color: var(--danger); color: #fff; }
    .status-row {
      display: grid;
      grid-template-columns: 110px 1fr;
      gap: 8px;
      padding: 4px 0;
      border-bottom: 1px solid #eef1f4;
    }
    .status-row:last-child { border-bottom: 0; }
    .key { color: var(--muted); }
    .pill {
      display: inline-flex;
      align-items: center;
      height: 24px;
      padding: 0 8px;
      border-radius: 999px;
      color: #fff;
      background: var(--muted);
      font-size: 12px;
    }
    .pill.ok { background: var(--ok); }
    .pill.stop { background: var(--muted); }
    .pill.bad { background: var(--danger); }
    .failure {
      border-left: 4px solid var(--danger);
      background: #fff7f6;
      padding: 10px;
      margin-top: 10px;
      border-radius: 6px;
    }
    .failure strong { color: var(--danger); }
    pre {
      margin: 0;
      padding: 10px;
      min-height: 340px;
      max-height: 560px;
      overflow: auto;
      color: #dbeafe;
      background: var(--code);
      border-radius: 6px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .log-error { color: #fecaca; }
    .log-warn { color: #fde68a; }
    .hint { color: var(--muted); font-size: 12px; margin-top: 8px; }
    @media (max-width: 980px) {
      main { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>LargeSLB Fuzz 控制台</h1>
    <span id="run-pill" class="pill stop">未运行</span>
  </header>
  <main>
    <section>
      <h2>启动参数</h2>
      <form id="launch-form">
        <div class="grid">
          <label class="wide">主库 DSN
            <input name="primary_dsn" placeholder="mysql://user:pass@host:3306/db?charset=utf8mb4" required>
          </label>
          <label class="wide">只读副本 DSN
            <input name="readonly_dsn" placeholder="mysql://user:pass@host:3306/db?charset=utf8mb4" required>
          </label>
          <label class="wide">state-dir
            <input name="state_dir" value="/tmp/largeslb_fuzz_console" required>
          </label>
          <label>seed <input name="seed" placeholder="可空"></label>
          <label>run-id <input name="run_id" placeholder="可空"></label>
          <label>workers <input name="workers" value="4"></label>
          <label>duration <input name="duration" value="0"></label>
          <label>bucket-count <input name="bucket_count" value="16"></label>
          <label>rows-per-bucket <input name="rows_per_bucket" value="2048"></label>
          <label class="wide">target-fields
            <input name="target_fields" value="char_255,varchar_16383,text_col,mediumtext_col,longtext_col,blob_col,mediumblob_col,longblob_col">
          </label>
          <label>readonly-check-rate <input name="readonly_check_rate" value="0.05"></label>
          <label>replica-timeout <input name="replica_timeout" value="300"></label>
          <label>replica-poll-interval <input name="replica_poll_interval" value="1"></label>
          <label>update-chunk-size <input name="update_chunk_size" value="256"></label>
          <label>query-chunk-size <input name="query_chunk_size" value="512"></label>
          <label>sleep-ms <input name="sleep_ms" value="0"></label>
          <label>engine-metric-interval <input name="engine_metric_interval" value="60"></label>
          <label>reconnect-sleep <input name="reconnect_sleep" value="5"></label>
          <label>max-reconnect-seconds <input name="max_reconnect_seconds" value="0"></label>
        </div>
        <div class="checks">
          <label><input type="checkbox" name="verbose"> verbose</label>
          <label><input type="checkbox" name="init_only"> init-only</label>
        </div>
        <div class="actions">
          <button class="primary" type="submit">启动</button>
          <button class="danger" type="button" id="stop-btn">停止</button>
          <button type="button" id="refresh-btn">刷新</button>
        </div>
        <div class="hint">控制台只传参和拉起进程，不校验数据库参数，也不把重启本身判为失败。</div>
      </form>
    </section>
    <div class="stack">
      <section>
        <h2>运行状态</h2>
        <div id="status"></div>
      </section>
      <section>
        <h2>异常定位</h2>
        <div id="failures">暂无异常</div>
      </section>
      <section>
        <h2>实时输出</h2>
        <pre id="logs"></pre>
      </section>
    </div>
  </main>
  <script>
    const form = document.querySelector('#launch-form');
    const statusBox = document.querySelector('#status');
    const failuresBox = document.querySelector('#failures');
    const logsBox = document.querySelector('#logs');
    const pill = document.querySelector('#run-pill');

    function formData() {
      const data = {};
      for (const item of new FormData(form).entries()) data[item[0]] = item[1];
      data.verbose = form.verbose.checked;
      data.init_only = form.init_only.checked;
      return data;
    }

    async function api(path, options = {}) {
      const res = await fetch(path, options);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || res.statusText);
      return body;
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      try {
        await api('/api/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(formData())
        });
        await refresh();
      } catch (err) {
        alert(err.message);
      }
    });
    document.querySelector('#stop-btn').addEventListener('click', async () => {
      await api('/api/stop', {method: 'POST'});
      await refresh();
    });
    document.querySelector('#refresh-btn').addEventListener('click', refresh);

    function renderStatus(data) {
      pill.className = data.running ? 'pill ok' : 'pill stop';
      pill.textContent = data.running ? '运行中' : '未运行';
      statusBox.innerHTML = [
        ['running', data.running ? 'true' : 'false'],
        ['pid', data.pid || ''],
        ['started_at', data.started_at || ''],
        ['exit_code', data.exit_code === null ? '' : data.exit_code],
        ['state_dir', data.state_dir || ''],
        ['command', (data.command || []).join(' ')]
      ].map(([k, v]) => `<div class="status-row"><div class="key">${escapeHtml(k)}</div><div>${escapeHtml(String(v))}</div></div>`).join('');
    }

    function renderFailures(data) {
      const failures = data.failures || [];
      if (!failures.length) {
        failuresBox.textContent = '暂无异常';
        return;
      }
      pill.className = 'pill bad';
      pill.textContent = '检测到异常';
      failuresBox.innerHTML = failures.slice(0, 8).map(item => `
        <div class="failure">
          <div><strong>${escapeHtml(item.kind || 'unknown')}</strong> ${escapeHtml(item.message || '')}</div>
          <div>异常位置：${escapeHtml(item.where || item.path || '')}</div>
          <div>目录：${escapeHtml(item.path || '')}</div>
        </div>
      `).join('');
    }

    function renderLogs(data) {
      logsBox.innerHTML = (data.logs || []).map(item => {
        const cls = item.level === 'ERROR' ? 'log-error' : (item.level === 'WARN' ? 'log-warn' : '');
        return `<span class="${cls}">[${escapeHtml(item.level)}] ${escapeHtml(item.text || '')}</span>`;
      }).join('\n');
      logsBox.scrollTop = logsBox.scrollHeight;
    }

    async function refresh() {
      const data = await api('/api/status');
      renderStatus(data);
      renderFailures(data);
      renderLogs(data);
    }

    function escapeHtml(value) {
      return value.replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[ch]));
    }

    refresh();
    setInterval(refresh, 1500);
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
