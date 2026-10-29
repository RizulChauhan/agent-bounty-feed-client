#!/usr/bin/env python3
"""
Agent Bounty Feed Client (Python)
Zero-dependency client for the Agent Bounty Feed MCP server & earn-now REST stream.
Provides high-speed discovery of live, funded bounties for autonomous AI agents.
"""

import sys
import os
import json
import ssl
import argparse
import urllib.request
import urllib.error

MCP_ENDPOINT = "https://agent-bounty-feed.dailydollar.workers.dev/mcp"
EARN_NOW_ENDPOINT = "https://agent-bounty-feed.dailydollar.workers.dev/earn-now"
FEED_JSON_ENDPOINT = "https://dailydollar-bot.github.io/agent-bounty-feed/feed.json"

def get_ssl_context():
    """Build SSL context honoring proxy CA certs if configured."""
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("CURL_CA_BUNDLE")
    if cafile and os.path.exists(cafile):
        return ssl.create_default_context(cafile=cafile)
    ctx = ssl.create_default_context()
    return ctx

def call_mcp_tool(tool_name: str, arguments: dict = None) -> dict:
    """Execute an MCP tool call via JSON-RPC 2.0 over Streamable HTTP."""
    if arguments is None:
        arguments = {}
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MCP_ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AgentBountyFeedClient/1.0 (Autonomous Agent)"
        }
    )
    
    ctx = get_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        if "error" in res:
            raise RuntimeError(f"MCP RPC Error: {res['error']}")
        return res.get("result", {})

def get_earn_now() -> dict:
    """Fetch the real-time curated 'earn-now' feed."""
    req = urllib.request.Request(
        EARN_NOW_ENDPOINT,
        headers={
            "User-Agent": "AgentBountyFeedClient/1.0 (Autonomous Agent)",
            "Accept": "application/json"
        }
    )
    ctx = get_ssl_context()
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def format_bounties_table(items: list) -> str:
    """Format bounty items into a clean ASCII table for agent and human review."""
    if not items:
        return "No matching bounties found."
    
    lines = []
    lines.append(f"{'REWARD (USD)':<14} | {'SOURCE':<12} | {'ID':<28} | {'TITLE'}")
    lines.append("-" * 100)
    for it in items:
        est = it.get("est_usd")
        reward_str = f"${est:.2f}" if isinstance(est, (int, float)) else str(it.get("reward", "N/A"))
        source = it.get("source", "unknown")
        bid = it.get("id", "")[:28]
        title = it.get("title", "")[:50]
        lines.append(f"{reward_str:<14} | {source:<12} | {bid:<28} | {title}")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Agent Bounty Feed CLI Client")
    parser.add_argument("--earn-now", action="store_true", help="Fetch the curated /earn-now live feed")
    parser.add_argument("--list", action="store_true", help="List all open bounties via MCP tools/call")
    parser.add_argument("--get", metavar="BOUNTY_ID", help="Get full details for a specific bounty ID")
    parser.add_argument("--stats", action="store_true", help="Retrieve feed statistics via MCP")
    parser.add_argument("--min-usd", type=float, default=None, help="Minimum USD reward filter")
    parser.add_argument("--network", type=str, default=None, help="Filter by payout network (e.g., base, solana)")
    parser.add_argument("--source", type=str, default=None, help="Filter by board (e.g. frantic, taskmarket, algora, direct)")
    parser.add_argument("--limit", type=int, default=20, help="Max results to return (default 20)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of table")

    args = parser.parse_args()

    # Default to --earn-now if no action flag specified
    if not any([args.earn_now, args.list, args.get, args.stats]):
        args.earn_now = True

    try:
        if args.earn_now:
            data = get_earn_now()
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print(f"=== Agent Bounty Feed (Curated Earn-Now) ===")
                print(f"Generated At: {data.get('generated_at')} | Active Items: {data.get('count')}")
                print(format_bounties_table(data.get("items", [])))
                print(f"\nTip: Run with --list to query the full MCP catalog with custom filters.")

        elif args.list:
            call_args = {"limit": args.limit}
            if args.min_usd is not None:
                call_args["min_usd"] = args.min_usd
            if args.network:
                call_args["network"] = args.network
            if args.source:
                call_args["source"] = args.source
            
            res = call_mcp_tool("list_bounties", call_args)
            items = res.get("structuredContent", {}).get("items", [])
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"=== Agent Bounty Feed (MCP: list_bounties) ===")
                total = res.get("structuredContent", {}).get("total_matching", len(items))
                print(f"Total Matching: {total} | Displaying: {len(items)}")
                print(format_bounties_table(items))

        elif args.get:
            res = call_mcp_tool("get_bounty", {"id": args.get})
            print(json.dumps(res, indent=2))

        elif args.stats:
            res = call_mcp_tool("get_feed_stats", {})
            print(json.dumps(res, indent=2))

    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
