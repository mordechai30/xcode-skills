"""Live-schema JSON-RPC transport to Apple's installed Xcode MCP bridge."""
from __future__ import annotations

import json
import codecs
import os
import queue
import subprocess
import threading
import time
from lifecycle.diagnostics import StreamDiagnostics


class MCPClient:
    """Own one retained mcpbridge transport for the active app context.

    The Xcode app and its debugger remain owned by Xcode after this transport closes.
    """

    def __init__(self, timeout=60, command=None, env=None, cwd=None):
        """Start an owned stdio server and initialize MCP.
        Read live tool schemas, including paginated results.
        """
        # Owned transport process, closed during final session cleanup.
        self.process = subprocess.Popen(command or ["xcrun", "mcpbridge"], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, bufsize=1, env=env, cwd=cwd)
        # Request deadline in seconds.
        self.timeout = min(timeout, 60)
        # Next unique JSON-RPC request identifier.
        self.next_id = 1
        # Complete stdout messages consumed by serialized requests.
        self.lines = queue.Queue()
        # Server diagnostics collected independently of JSON-RPC.
        self.stderr_lines = queue.Queue()
        self.stderr_parser = StreamDiagnostics()
        # Retained sessions deliver diagnostics directly to their operation log.
        self.diagnostic_sink = None
        # Tool-list changes invalidate the current schema cache.
        self.tools_changed = False
        # Background reader that preserves complete protocol lines.
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()
        # Background diagnostic reader kept active during pauses.
        self.stderr_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self.stderr_reader.start()
        try:
            self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                         "clientInfo": {"name": "xcode-operation-skill", "version": "1.0"}})
            self.notify("notifications/initialized", {})
            # Current discovered tool contracts for request validation.
            self.tools = []
            cursor = None
            seen = set()
            while True:
                page = self.request('tools/list', {'cursor': cursor} if cursor else {})
                self.tools.extend(page.get('tools', []))
                cursor = page.get('nextCursor')
                if not cursor:
                    break
                if cursor in seen:
                    raise RuntimeError('MCP tool pagination repeated its cursor.')
                seen.add(cursor)
        except BaseException:
            self.close()
            raise

    def _read_stdout(self):
        """Feed complete MCP lines to waiting requests.
        A sentinel reports EOF without silently reconnecting.
        """
        for line in self.process.stdout:
            try:
                message = json.loads(line) if isinstance(line, str) else line
            except json.JSONDecodeError:
                continue
            if 'id' not in message:
                if message.get('method') == 'notifications/tools/list_changed':
                    self.tools_changed = True
                continue
            self.lines.put(message)
        self.lines.put(None)

    def _read_stderr(self):
        """Retain server diagnostics separately from JSON-RPC.
        Read incrementally so an active server does not delay output capture.
        """
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        while True:
            chunk = os.read(self.process.stderr.fileno(), 4096)
            detail = self.stderr_parser.feed(decoder.decode(chunk, final=not chunk), final=not chunk)
            if detail:
                if self.diagnostic_sink:
                    self.diagnostic_sink(detail)
                else:
                    self.stderr_lines.put(detail)
            if not chunk:
                break

    def set_diagnostic_sink(self, sink):
        """Send retained-session stderr directly to its diagnostic log.
        Flush startup diagnostics once before discarding queue storage.
        """
        self.diagnostic_sink = sink
        pending = self.take_diagnostics()
        if pending:
            sink(pending)

    def _write(self, message):
        """Send one JSON-RPC message to the owned server.
        Reject requests after transport exit.
        """
        if self.process.poll() is not None:
            raise RuntimeError("Apple MCP bridge exited before the request.")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def notify(self, method, params):
        """Send a notification without a response identifier.
        Initialization uses this after its negotiated response.
        """
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def request(self, method, params):
        """Send a request and wait for its matching ID or deadline.
        Discard unrelated notifications and answer supported server requests.
        """
        request_id = self.next_id
        self.next_id += 1
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + min(self.timeout, 60)
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=min(0.5, deadline - time.monotonic()))
            except queue.Empty:
                continue
            if line is None:
                raise RuntimeError("Apple MCP bridge closed stdout before replying.")
            try:
                message = json.loads(line) if isinstance(line, str) else line
            except json.JSONDecodeError:
                continue
            if message.get("id") != request_id:
                if message.get('method') == 'notifications/tools/list_changed':
                    self.tools_changed = True
                if message.get('method') and 'id' in message:
                    reply = {'jsonrpc': '2.0', 'id': message['id']}
                    if message['method'] == 'ping':
                        reply['result'] = {}
                    else:
                        reply['error'] = {'code': -32601, 'message': 'Client method is not supported.'}
                    self._write(reply)
                continue
            if "error" in message:
                raise RuntimeError(f"Apple MCP {method} failed: {message['error']}")
            return message.get("result", {})
        raise TimeoutError(f"Apple MCP {method} exceeded {self.timeout} seconds.")

    def call(self, name, arguments, before_send=None, timeout=None):
        """Validate live supported and required fields before invoking a tool.
        Return one useful result representation and preserve remote errors.
        """
        if self.tools_changed:
            refreshed = []
            cursor = None
            seen = set()
            while True:
                page = self.request('tools/list', {'cursor':cursor} if cursor else {})
                refreshed.extend(page.get('tools', []))
                cursor = page.get('nextCursor')
                if not cursor:
                    break
                if cursor in seen:
                    raise RuntimeError('MCP schema pagination repeated a cursor.')
                seen.add(cursor)
            self.tools = refreshed
            self.tools_changed = False
        schema = next((item for item in self.tools if item.get("name") == name), None)
        if schema is None:
            raise RuntimeError(f"Apple MCP tool is not available: {name}")
        properties = schema.get("inputSchema", {}).get("properties", {})
        unknown = sorted(set(arguments) - set(properties))
        if unknown:
            raise RuntimeError(f"Current {name} schema rejects fields: {', '.join(unknown)}")
        missing = set(schema.get('inputSchema', {}).get('required', [])) - set(arguments)
        if missing:
            raise RuntimeError('Missing required live fields for ' + name + ': ' + ', '.join(sorted(missing)))
        for key, value in arguments.items():
            definition = properties.get(key, {})
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if 'maximum' in definition and value > definition['maximum']:
                    raise RuntimeError('Current ' + name + ' schema maximum exceeded for ' + key)
                if 'minimum' in definition and value < definition['minimum']:
                    raise RuntimeError('Current ' + name + ' schema minimum exceeded for ' + key)
        if before_send:
            before_send()
        previous_timeout = self.timeout
        try:
            if timeout is not None:
                self.timeout = min(timeout, 60)
            value = self.request("tools/call", {"name": name, "arguments": arguments})
        finally:
            self.timeout = previous_timeout
        return {"isError": value.get("isError", False), "structured": value.get("structuredContent"),
                "content": [] if value.get("structuredContent") is not None else value.get("content", [])}

    def close(self):
        """Close and reap only this owned stdio server process.
        Shared IDE and application processes are not transport cleanup targets.
        """
        if self.process.poll() is None:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
        self.reader.join(timeout=1)
        self.stderr_reader.join(timeout=1)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream and not stream.closed:
                stream.close()

    def __enter__(self):
        """Return the initialized transport for scoped discovery.
        Active app sessions retain the same instance outside such a scope.
        """
        return self

    def __exit__(self, *_):
        """Close an owned transport when scoped discovery ends.
        Application lifecycle is handled by operation modules.
        """
        self.close()

    def take_diagnostics(self):
        """Remove consumed MCP stderr diagnostics from the owned queue.
        Ordinary server output is discarded by the stderr reader.
        """
        lines = []
        while True:
            try:
                lines.append(self.stderr_lines.get_nowait())
            except queue.Empty:
                return '\n'.join(lines)
