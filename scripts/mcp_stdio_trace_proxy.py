#!/usr/bin/env python3
"""MCP stdio proxy that logs JSON-RPC traffic.

Usage:
  python scripts/mcp_stdio_trace_proxy.py --log logs/mcp-trace.jsonl -- python -m server --transport stdio

Configure your MCP client to use this script as the server command to capture
full tool-list, tool-call, and tool-result traffic.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict


def build_record(direction: str, raw_line: str) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "ts": time.time(),
        "direction": direction,
        "raw": raw_line,
    }
    try:
        payload = json.loads(raw_line)
        record["json"] = payload
        if isinstance(payload, dict):
            record["method"] = payload.get("method")
            record["id"] = payload.get("id")
    except json.JSONDecodeError as exc:
        record["parse_error"] = str(exc)
    return record


def write_bytes(target, line: bytes) -> None:
    target.write(line)
    if hasattr(target, "flush"):
        target.flush()


async def pump_stream(
    reader: asyncio.StreamReader,
    writer,
    log_fh,
    direction: str,
) -> None:
    while True:
        line = await reader.readline()
        if not line:
            break
        text = line.decode("utf-8", errors="replace").rstrip("\r\n")
        record = build_record(direction, text)
        log_fh.write(json.dumps(record) + "\n")
        log_fh.flush()
        if writer is not None:
            if hasattr(writer, "drain"):
                writer.write(line)
                await writer.drain()
            else:
                write_bytes(writer, line)


async def main() -> int:
    parser = argparse.ArgumentParser(description="MCP stdio trace proxy")
    parser.add_argument("--log", default="logs/mcp-trace.jsonl", help="Path to JSONL log file")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run (prefix with --)")
    args = parser.parse_args()

    if not args.cmd or args.cmd[0] != "--":
        parser.error("Command must be provided after --")

    cmd = args.cmd[1:]
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if proc.stdin is None or proc.stdout is None or proc.stderr is None:
        raise RuntimeError("Failed to open subprocess pipes")

    loop = asyncio.get_running_loop()
    stdin_reader = asyncio.StreamReader()
    stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
    await loop.connect_read_pipe(lambda: stdin_protocol, sys.stdin)

    with log_path.open("a", encoding="utf-8") as log_fh:
        tasks = [
            asyncio.create_task(
                pump_stream(
                    reader=stdin_reader,
                    writer=proc.stdin,
                    log_fh=log_fh,
                    direction="client->server",
                )
            ),
            asyncio.create_task(
                pump_stream(
                    reader=proc.stdout,
                    writer=sys.stdout.buffer,
                    log_fh=log_fh,
                    direction="server->client",
                )
            ),
            asyncio.create_task(
                pump_stream(
                    reader=proc.stderr,
                    writer=sys.stderr.buffer,
                    log_fh=log_fh,
                    direction="server->stderr",
                )
            ),
        ]

        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()

    return await proc.wait()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
