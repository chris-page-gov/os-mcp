"""Audit Logger for OS/ONS MCP Server

This module provides comprehensive audit logging in an LLM-readable format.
Each query is logged with clear sections that can be copy/pasted into an LLM
for analysis.

Audit Log Sections:
1. QUERY - The incoming user question
2. ROUTING - Intent classification and tool recommendation
3. TOOL_CALLS - Each tool call with inputs and outputs
4. RESPONSE - Final response to the user
5. METRICS - Performance and efficiency metrics
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from pathlib import Path
import threading

# Thread-local storage for audit context
_audit_context = threading.local()


@dataclass
class ToolCallRecord:
    """Record of a single tool call"""
    tool_name: str
    timestamp: str
    duration_ms: float
    inputs: Dict[str, Any]
    outputs: Any
    success: bool
    error: Optional[str] = None


@dataclass
class AuditRecord:
    """Complete audit record for a query"""
    audit_id: str
    timestamp: str
    query: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    recommended_tool: Optional[str] = None
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    final_response: Optional[str] = None
    total_duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """
    Comprehensive audit logger for MCP server operations.

    Produces structured, LLM-readable logs with clear sections.
    """

    # Section delimiters for easy parsing
    SECTION_START = "=" * 60
    SECTION_END = "-" * 60
    SUBSECTION = "·" * 40

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_to_file: bool = True,
        log_to_console: bool = False,
    ):
        self.log_dir = log_dir or Path("logs/audit")
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self._current_record: Optional[AuditRecord] = None
        self._start_time: Optional[float] = None

        if log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Standard logger for console output
        self.logger = logging.getLogger("audit")

    def start_query(self, query: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start auditing a new query. Returns audit ID."""
        audit_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        self._current_record = AuditRecord(
            audit_id=audit_id,
            timestamp=timestamp,
            query=query,
            metadata=metadata or {},
        )
        self._start_time = time.time()

        # Store in thread-local for access by other components
        _audit_context.current_record = self._current_record
        _audit_context.audit_id = audit_id

        return audit_id

    def record_routing(
        self,
        intent: str,
        confidence: float,
        recommended_tool: str,
        workflow_steps: List[str],
    ) -> None:
        """Record the query routing decision"""
        if self._current_record:
            self._current_record.intent = intent
            self._current_record.confidence = confidence
            self._current_record.recommended_tool = recommended_tool
            self._current_record.metadata["workflow_steps"] = workflow_steps

    def record_tool_call(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Any,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Record a tool call"""
        if self._current_record:
            record = ToolCallRecord(
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
                duration_ms=duration_ms,
                inputs=inputs,
                outputs=outputs,
                success=success,
                error=error,
            )
            self._current_record.tool_calls.append(record)

    def record_response(self, response: str) -> None:
        """Record the final response"""
        if self._current_record:
            self._current_record.final_response = response

    def record_error(self, error: str) -> None:
        """Record an error"""
        if self._current_record:
            self._current_record.success = False
            self._current_record.error = error

    def end_query(self) -> Optional[AuditRecord]:
        """End auditing and return the complete record"""
        if not self._current_record:
            return None

        if self._start_time:
            self._current_record.total_duration_ms = (time.time() - self._start_time) * 1000

        record = self._current_record

        # Write to file
        if self.log_to_file:
            self._write_to_file(record)

        # Log to console
        if self.log_to_console:
            self.logger.info(self.format_for_llm(record))

        # Clean up
        self._current_record = None
        self._start_time = None
        _audit_context.current_record = None
        _audit_context.audit_id = None

        return record

    def format_for_llm(self, record: AuditRecord) -> str:
        """
        Format audit record for LLM consumption.

        Produces a clearly structured, copy/paste-ready format.
        """
        lines = []

        # Header
        lines.append(self.SECTION_START)
        lines.append(f"AUDIT LOG: {record.audit_id}")
        lines.append(f"Timestamp: {record.timestamp}")
        lines.append(self.SECTION_START)
        lines.append("")

        # SECTION 1: QUERY
        lines.append("## 1. QUERY")
        lines.append(self.SECTION_END)
        lines.append(f"User Question: \"{record.query}\"")
        lines.append("")

        # SECTION 2: ROUTING
        lines.append("## 2. ROUTING DECISION")
        lines.append(self.SECTION_END)
        if record.intent:
            lines.append(f"Intent Detected: {record.intent}")
            lines.append(f"Confidence: {record.confidence:.2f}" if record.confidence else "Confidence: N/A")
            lines.append(f"Recommended Tool: {record.recommended_tool}")
            if "workflow_steps" in record.metadata:
                lines.append(f"Workflow Steps: {' → '.join(record.metadata['workflow_steps'])}")
        else:
            lines.append("No routing decision recorded (route_query not called)")
        lines.append("")

        # SECTION 3: TOOL CALLS
        lines.append("## 3. TOOL CALLS")
        lines.append(self.SECTION_END)
        if record.tool_calls:
            for i, call in enumerate(record.tool_calls, 1):
                lines.append(f"### Tool Call {i}: {call.tool_name}")
                lines.append(self.SUBSECTION)
                lines.append(f"Timestamp: {call.timestamp}")
                lines.append(f"Duration: {call.duration_ms:.1f}ms")
                lines.append(f"Status: {'SUCCESS' if call.success else 'FAILED'}")
                lines.append("")
                lines.append("**Inputs:**")
                lines.append("```json")
                lines.append(json.dumps(call.inputs, indent=2, default=str))
                lines.append("```")
                lines.append("")
                lines.append("**Outputs:**")
                lines.append("```json")
                # Truncate long outputs
                output_str = json.dumps(call.outputs, indent=2, default=str)
                if len(output_str) > 2000:
                    output_str = output_str[:2000] + "\n... [truncated]"
                lines.append(output_str)
                lines.append("```")
                if call.error:
                    lines.append(f"**Error:** {call.error}")
                lines.append("")
        else:
            lines.append("No tool calls recorded")
        lines.append("")

        # SECTION 4: RESPONSE
        lines.append("## 4. FINAL RESPONSE")
        lines.append(self.SECTION_END)
        if record.final_response:
            # Truncate very long responses
            response = record.final_response
            if len(response) > 3000:
                response = response[:3000] + "\n... [truncated]"
            lines.append(response)
        else:
            lines.append("No final response recorded")
        lines.append("")

        # SECTION 5: METRICS
        lines.append("## 5. METRICS")
        lines.append(self.SECTION_END)
        lines.append(f"Total Duration: {record.total_duration_ms:.1f}ms")
        lines.append(f"Tool Calls: {len(record.tool_calls)}")
        lines.append(f"Overall Status: {'SUCCESS' if record.success else 'FAILED'}")
        if record.error:
            lines.append(f"Error: {record.error}")

        # Tool call summary
        if record.tool_calls:
            lines.append("")
            lines.append("**Tool Call Summary:**")
            tool_counts: Dict[str, int] = {}
            for call in record.tool_calls:
                tool_counts[call.tool_name] = tool_counts.get(call.tool_name, 0) + 1
            for tool, count in sorted(tool_counts.items()):
                lines.append(f"  - {tool}: {count}x")

        lines.append("")
        lines.append(self.SECTION_START)
        lines.append("END OF AUDIT LOG")
        lines.append(self.SECTION_START)

        return "\n".join(lines)

    def format_compact(self, record: AuditRecord) -> str:
        """Format audit record in compact format for quick review"""
        tool_list = [c.tool_name for c in record.tool_calls]
        status = "✓" if record.success else "✗"

        return (
            f"[{record.audit_id}] {status} "
            f"Intent: {record.intent or 'unknown'} | "
            f"Tools: {' → '.join(tool_list)} | "
            f"Duration: {record.total_duration_ms:.0f}ms"
        )

    def _write_to_file(self, record: AuditRecord) -> None:
        """Write audit record to file"""
        # Daily log file
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{date_str}.log"

        # Append formatted log
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(self.format_for_llm(record))
            f.write("\n\n")

        # Also write JSON for programmatic access
        json_file = self.log_dir / f"audit_{date_str}.jsonl"
        with open(json_file, "a", encoding="utf-8") as f:
            # Convert to dict for JSON serialization
            record_dict = {
                "audit_id": record.audit_id,
                "timestamp": record.timestamp,
                "query": record.query,
                "intent": record.intent,
                "confidence": record.confidence,
                "recommended_tool": record.recommended_tool,
                "tool_calls": [
                    {
                        "tool_name": c.tool_name,
                        "timestamp": c.timestamp,
                        "duration_ms": c.duration_ms,
                        "inputs": c.inputs,
                        "outputs": str(c.outputs)[:500],  # Truncate
                        "success": c.success,
                        "error": c.error,
                    }
                    for c in record.tool_calls
                ],
                "total_duration_ms": record.total_duration_ms,
                "success": record.success,
                "error": record.error,
            }
            f.write(json.dumps(record_dict) + "\n")


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


def get_current_audit_id() -> Optional[str]:
    """Get the current audit ID from thread-local context"""
    return getattr(_audit_context, "audit_id", None)


def get_current_audit_record() -> Optional[AuditRecord]:
    """Get the current audit record from thread-local context"""
    return getattr(_audit_context, "current_record", None)


@contextmanager
def audit_query(query: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for auditing a query"""
    logger = get_audit_logger()
    audit_id = logger.start_query(query, metadata)
    try:
        yield audit_id
    except Exception as e:
        logger.record_error(str(e))
        raise
    finally:
        logger.end_query()


def audit_tool_call(tool_name: str):
    """Decorator for auditing tool calls"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = get_audit_logger()
            start_time = time.time()
            error = None
            success = True
            result = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                success = False
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                # Extract inputs from args/kwargs
                inputs = {}
                if args:
                    inputs["args"] = [str(a)[:200] for a in args[1:]]  # Skip self
                if kwargs:
                    inputs["kwargs"] = {k: str(v)[:200] for k, v in kwargs.items()}

                logger.record_tool_call(
                    tool_name=tool_name,
                    inputs=inputs,
                    outputs=result,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                )

        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def example():
        logger = AuditLogger(log_to_console=True)

        # Start a query
        audit_id = logger.start_query("Find Birmingham")

        # Record routing
        logger.record_routing(
            intent="place_lookup",
            confidence=0.95,
            recommended_tool="search_geographic_areas",
            workflow_steps=["search_geographic_areas"],
        )

        # Record tool calls
        logger.record_tool_call(
            tool_name="route_query",
            inputs={"query": "Find Birmingham"},
            outputs={"intent": "place_lookup", "confidence": 0.95},
            duration_ms=15.3,
            success=True,
        )

        logger.record_tool_call(
            tool_name="search_geographic_areas",
            inputs={"query": "Birmingham", "level": "local_auth"},
            outputs={"code": "E08000025", "name": "Birmingham"},
            duration_ms=245.7,
            success=True,
        )

        # Record response
        logger.record_response("Birmingham is a metropolitan borough with GSS code E08000025.")

        # End and get record
        record = logger.end_query()
        if record:
            print(logger.format_for_llm(record))

    asyncio.run(example())
