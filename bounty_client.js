#!/usr/bin/env node
/**
 * Agent Bounty Feed Client (Node.js)
 * Zero-dependency client for the Agent Bounty Feed MCP server & earn-now REST stream.
 * Compatible with Node.js 18+
 */

const MCP_ENDPOINT = 'https://agent-bounty-feed.dailydollar.workers.dev/mcp';
const EARN_NOW_ENDPOINT = 'https://agent-bounty-feed.dailydollar.workers.dev/earn-now';

async function callMcpTool(toolName, args = {}) {
  const payload = {
    jsonrpc: '2.0',
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: args,
    },
    id: 1,
  };

  const res = await fetch(MCP_ENDPOINT, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'AgentBountyFeedClient-Node/1.0 (Autonomous Agent)',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }

  const data = await res.json();
  if (data.error) {
    throw new Error(`MCP RPC Error: ${JSON.stringify(data.error)}`);
  }
  return data.result;
}

async function getEarnNow() {
  const res = await fetch(EARN_NOW_ENDPOINT, {
    headers: {
      Accept: 'application/json',
      'User-Agent': 'AgentBountyFeedClient-Node/1.0 (Autonomous Agent)',
    },
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return await res.json();
}

function printTable(items) {
  if (!items || items.length === 0) {
    console.log('No matching bounties found.');
    return;
  }
  console.log(
    `${'REWARD'.padEnd(14)} | ${'SOURCE'.padEnd(12)} | ${'ID'.padEnd(28)} | TITLE`
  );
  console.log('-'.repeat(95));
  for (const it of items) {
    const est = it.est_usd;
    const rewardStr =
      typeof est === 'number' ? `$${est.toFixed(2)}` : String(it.reward ?? 'N/A');
    const source = (it.source ?? 'unknown').padEnd(12);
    const id = (it.id ?? '').slice(0, 28).padEnd(28);
    const title = (it.title ?? '').slice(0, 50);
    console.log(`${rewardStr.padEnd(14)} | ${source} | ${id} | ${title}`);
  }
}

async function main() {
  const argv = process.argv.slice(2);
  const isJson = argv.includes('--json');
  const isList = argv.includes('--list');
  const isStats = argv.includes('--stats');

  const minUsdIdx = argv.indexOf('--min-usd');
  const minUsd = minUsdIdx !== -1 ? parseFloat(argv[minUsdIdx + 1]) : null;

  const getIdx = argv.indexOf('--get');
  const getId = getIdx !== -1 ? argv[getIdx + 1] : null;

  try {
    if (getId) {
      const res = await callMcpTool('get_bounty', { id: getId });
      console.log(JSON.stringify(res, null, 2));
    } else if (isStats) {
      const res = await callMcpTool('get_feed_stats', {});
      console.log(JSON.stringify(res, null, 2));
    } else if (isList) {
      const toolArgs = { limit: 20 };
      if (minUsd !== null) toolArgs.min_usd = minUsd;

      const res = await callMcpTool('list_bounties', toolArgs);
      const items = res?.structuredContent?.items ?? [];
      if (isJson) {
        console.log(JSON.stringify(res, null, 2));
      } else {
        console.log(`=== Agent Bounty Feed (MCP list_bounties) ===`);
        console.log(`Displaying: ${items.length} items`);
        printTable(items);
      }
    } else {
      // Default: earn-now
      const data = await getEarnNow();
      if (isJson) {
        console.log(JSON.stringify(data, null, 2));
      } else {
        console.log(`=== Agent Bounty Feed (Curated Earn-Now) ===`);
        console.log(
          `Generated At: ${data.generated_at} | Active Items: ${data.count}`
        );
        printTable(data.items);
      }
    }
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

main();
