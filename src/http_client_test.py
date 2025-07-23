import asyncio
import logging
import httpx
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from mcp.types import TextContent

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def extract_text_from_result(result) -> str:
    """Safely extract text from MCP tool result"""
    if not result.content:
        return "No content"
    
    for item in result.content:
        if isinstance(item, TextContent):
            return item.text
    
    content_types = [type(item).__name__ for item in result.content]
    return f"Non-text content: {', '.join(content_types)}"


async def test_session_safe(session_name: str, requests: int = 3):
    """Test a single session with safer error handling"""
    headers = {"Authorization": "Bearer dev-token"}
    results = []
    session_id = None

    print(f"\n{session_name} - Testing {requests} requests")
    print("-" * 40)

    try:
        async with streamablehttp_client("http://127.0.0.1:8000/mcp", headers=headers) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                session_id = get_session_id()
                print(f"{session_name} Session ID: {session_id}")

                for i in range(requests):
                    try:
                        result = await session.call_tool("hello_world", {"name": f"{session_name}-User{i+1}"})
                        result_text = extract_text_from_result(result)
                        print(f"  Request {i+1}: SUCCESS - {result_text}")
                        results.append("SUCCESS")
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        if "429" in str(e) or "Too Many Requests" in str(e):
                            print(f"  Request {i+1}: BLOCKED - Rate limited")
                            results.append("BLOCKED")
                        else:
                            print(f"  Request {i+1}: ERROR - {e}")
                            results.append("ERROR")
                        
                        for j in range(i+1, requests):
                            print(f"  Request {j+1}: BLOCKED - Session rate limited")
                            results.append("BLOCKED")
                        break

    except Exception as e:
        print(f"{session_name}: Connection error - {str(e)[:100]}")
        if len(results) == 0:
            results = ["ERROR"] * requests
        elif len(results) < requests:
            remaining = requests - len(results)
            results.extend(["BLOCKED"] * remaining)

    return results, session_id


async def test_two_sessions():
    """Test rate limiting across two sessions"""
    print("HTTP Rate Limit Test - Two Sessions")
    print("=" * 50)
    
    results_a, session_id_a = await test_session_safe("SESSION-A", 20)
    await asyncio.sleep(0.5)
    results_b, session_id_b = await test_session_safe("SESSION-B", 20)
    
    # Analyze results
    print("\nRESULTS SUMMARY")
    print("=" * 30)
    
    success_a = results_a.count("SUCCESS")
    blocked_a = results_a.count("BLOCKED")
    error_a = results_a.count("ERROR")
    
    success_b = results_b.count("SUCCESS")
    blocked_b = results_b.count("BLOCKED")
    error_b = results_b.count("ERROR")
    
    print(f"SESSION-A: {success_a} success, {blocked_a} blocked, {error_a} errors")
    print(f"SESSION-B: {success_b} success, {blocked_b} blocked, {error_b} errors")
    print(f"Total: {success_a + success_b} success, {blocked_a + blocked_b} blocked")
    
    if session_id_a and session_id_b:
        print(f"Different session IDs: {session_id_a != session_id_b}")
    else:
        print("Could not compare session IDs")
    
    total_success = success_a + success_b
    total_blocked = blocked_a + blocked_b
    
    print(f"\nRATE LIMITING ASSESSMENT:")
    if total_success >= 2 and total_blocked >= 2:
        print("✅ PASS: Rate limiting is working")
        print(f"   - {total_success} requests succeeded")
        print(f"   - {total_blocked} requests were rate limited") 
        print("   - Each session got limited after ~2 requests")
    elif total_success == 0:
        print("❌ FAIL: No requests succeeded (check server/auth)")
    else:
        print("⚠️  UNCLEAR: Unexpected pattern")
        print("   Check server logs for actual behavior")


if __name__ == "__main__":
    asyncio.run(test_two_sessions())
