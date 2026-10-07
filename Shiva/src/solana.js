const LAMPORTS_PER_SOL = 1_000_000_000n;
const WRAPPED_SOL_MINT = 'So11111111111111111111111111111111111111112';

function quoteSymbolForMint(mint, config) {
  return mint === WRAPPED_SOL_MINT ? 'SOL' : config.quoteSymbol;
}

let rpcId = 0;

export async function rpcCall(rpcUrl, method, params) {
  const response = await fetch(rpcUrl, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: ++rpcId, method, params }),
    signal: AbortSignal.timeout(25_000),
  });
  if (!response.ok) throw new Error(`Solana RPC вернул HTTP ${response.status}`);

  const payload = await response.json();
  if (payload.error) {
    const message = payload.error.message || 'неизвестная ошибка';
    throw new Error(`Solana RPC ${method}: ${message}`);
  }
  return payload.result;
}

export function amountToNumber(raw, decimals) {
  const amount = Number(raw);
  if (!Number.isFinite(amount)) return Number.POSITIVE_INFINITY;
  return amount / (10 ** decimals);
}

export function formatAmount(raw, decimals) {
  let amount;
  try {
    amount = BigInt(raw);
  } catch {
    return '0';
  }
  if (amount < 0n) amount = -amount;

  const places = Math.max(0, Math.min(18, Number(decimals) || 0));
  const scale = 10n ** BigInt(places);
  const whole = (amount / scale).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  if (places === 0) return whole;

  const fraction = (amount % scale).toString().padStart(places, '0');
  const visible = fraction.slice(0, Math.min(places, 9)).replace(/0+$/, '');
  if (visible) return `${whole}.${visible}${fraction.slice(9).match(/[1-9]/) ? '…' : ''}`;
  if (fraction.match(/[1-9]/)) return `<0.${'0'.repeat(Math.min(places, 8) - 1)}1`;
  return whole;
}

function pubkeyString(entry) {
  if (typeof entry === 'string') return entry;
  return entry?.pubkey?.toString?.() ?? entry?.pubkey ?? '';
}

function readTokenBalances(meta) {
  const beforeOwnerByIndex = new Map();
  const afterOwnerByIndex = new Map();
  for (const entry of meta.preTokenBalances || []) {
    if (entry.owner) beforeOwnerByIndex.set(entry.accountIndex, entry.owner);
  }
  for (const entry of meta.postTokenBalances || []) {
    if (entry.owner) afterOwnerByIndex.set(entry.accountIndex, entry.owner);
  }

  const ownerByIndex = new Map([...beforeOwnerByIndex, ...afterOwnerByIndex]);
  const balances = new Map();
  const preAccounts = new Set();

  for (const [side, entries] of [
    ['pre', meta.preTokenBalances || []],
    ['post', meta.postTokenBalances || []],
  ]) {
    for (const entry of entries) {
      const owner = entry.owner || ownerByIndex.get(entry.accountIndex);
      const mint = entry.mint;
      if (!owner || !mint) continue;

      let raw;
      try {
        raw = BigInt(entry.uiTokenAmount?.amount ?? '0');
      } catch {
        continue;
      }

      const key = `${owner}\u0000${mint}`;
      let balance = balances.get(key);
      if (!balance) {
        balance = { owner, mint, decimals: Number(entry.uiTokenAmount?.decimals || 0), pre: 0n, post: 0n };
        balances.set(key, balance);
      }
      balance.decimals = Number(entry.uiTokenAmount?.decimals ?? balance.decimals);
      balance[side] += raw;
      if (side === 'pre') preAccounts.add(entry.accountIndex);
    }
  }

  const byOwner = new Map();
  for (const balance of balances.values()) {
    let ownerBalances = byOwner.get(balance.owner);
    if (!ownerBalances) {
      ownerBalances = new Map();
      byOwner.set(balance.owner, ownerBalances);
    }
    ownerBalances.set(balance.mint, {
      mint: balance.mint,
      decimals: balance.decimals,
      delta: balance.post - balance.pre,
    });
  }

  return { byOwner, preAccounts };
}

function getSolSpend(owner, transaction, meta, postTokenBalances, preTokenAccountIndexes) {
  const accountKeys = transaction.transaction?.message?.accountKeys || [];
  const ownerIndex = accountKeys.findIndex((entry) => pubkeyString(entry) === owner);
  if (ownerIndex < 0) return 0n;

  const preBalances = meta.preBalances || [];
  const postBalances = meta.postBalances || [];
  if (preBalances[ownerIndex] === undefined || postBalances[ownerIndex] === undefined) return 0n;

  let spent = BigInt(preBalances[ownerIndex]) - BigInt(postBalances[ownerIndex]);
  if (ownerIndex === 0) spent -= BigInt(meta.fee || 0);

  // When the buyer creates a token account in this transaction, its rent is
  // part of the wallet's SOL outflow, but not part of the swap amount.
  for (const tokenAccount of postTokenBalances) {
    if (tokenAccount.owner !== owner || preTokenAccountIndexes.has(tokenAccount.accountIndex)) continue;
    const index = tokenAccount.accountIndex;
    const accountRent = BigInt(postBalances[index] || 0) - BigInt(preBalances[index] || 0);
    if (accountRent > 0n) spent -= accountRent;
  }

  return spent > 0n ? spent : 0n;
}

function selectQuote(owner, ownerBalances, transaction, meta, config, preTokenAccountIndexes) {
  if (config.quoteMint) {
    const balance = ownerBalances.get(config.quoteMint);
    if (!balance || balance.delta >= 0n) return null;
    return {
      mint: balance.mint,
      raw: -balance.delta,
      decimals: balance.decimals,
      symbol: quoteSymbolForMint(balance.mint, config),
      kind: 'spl',
    };
  }

  const spentTokens = [...ownerBalances.values()]
    .filter((balance) => balance.mint !== config.tokenMint && balance.delta < 0n)
    .sort((a, b) => amountToNumber(-a.delta, a.decimals) - amountToNumber(-b.delta, b.decimals));

  if (spentTokens.length > 0) {
    const balance = spentTokens.at(-1);
    return {
      mint: balance.mint,
      raw: -balance.delta,
      decimals: balance.decimals,
      symbol: quoteSymbolForMint(balance.mint, config),
      kind: 'spl',
    };
  }

  const postTokenBalances = meta.postTokenBalances || [];
  const solSpent = getSolSpend(owner, transaction, meta, postTokenBalances, preTokenAccountIndexes);
  if (solSpent <= 0n) return null;
  return {
    mint: null,
    raw: solSpent,
    decimals: 9,
    symbol: 'SOL',
    kind: 'sol',
  };
}

/**
 * Detect net buys of the configured mint from a parsed Solana transaction.
 * A positive target-token balance alone is not enough: the buyer must also
 * have spent the configured quote mint, another SPL token, or SOL.
 */
export function findBuys(transaction, config) {
  const meta = transaction?.meta;
  if (!meta || meta.err) return [];

  const { byOwner, preAccounts } = readTokenBalances(meta);
  const buys = [];
  for (const [owner, ownerBalances] of byOwner) {
    const target = ownerBalances.get(config.tokenMint);
    if (!target || target.delta <= 0n) continue;

    const quote = selectQuote(owner, ownerBalances, transaction, meta, config, preAccounts);
    if (!quote || quote.raw <= 0n) continue;
    const quoteAmount = amountToNumber(quote.raw, quote.decimals);
    if (quoteAmount < config.minBuyAmount) continue;

    buys.push({
      buyer: owner,
      tokenRaw: target.delta,
      tokenDecimals: target.decimals,
      quoteRaw: quote.raw,
      quoteDecimals: quote.decimals,
      quoteMint: quote.mint,
      quoteSymbol: quote.symbol,
      quoteKind: quote.kind,
    });
  }
  return buys;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

export const DEFAULT_MESSAGE_TEMPLATE = `🐕 <b>Покупка {token}!</b>

🟢 Куплено: <b>{token_amount} {token}</b>
💸 Потрачено: <b>{quote_amount} {quote_symbol}</b>
👛 Покупатель: {buyer}

🔎 <a href="{tx_url}">Транзакция</a> · <a href="{token_url}">График / токен</a>`;

export function formatBuyMessage(buy, signature, config, template = DEFAULT_MESSAGE_TEMPLATE) {
  const tokenPage = `https://www.stonkfun.xyz/token/${config.tokenMint}`;
  const txPage = `https://solscan.io/tx/${signature}`;
  const buyerPage = `https://solscan.io/account/${buy.buyer}`;
  const buyerShort = `${buy.buyer.slice(0, 5)}…${buy.buyer.slice(-5)}`;
  const values = {
    token: escapeHtml(config.tokenSymbol),
    token_amount: escapeHtml(formatAmount(buy.tokenRaw, buy.tokenDecimals)),
    quote_amount: escapeHtml(formatAmount(buy.quoteRaw, buy.quoteDecimals)),
    quote_symbol: escapeHtml(buy.quoteSymbol),
    buyer: `<a href="${escapeHtml(buyerPage)}">${escapeHtml(buyerShort)}</a>`,
    tx_url: escapeHtml(txPage),
    token_url: escapeHtml(tokenPage),
  };

  return String(template).replace(/\{([a-z_]+)\}/g, (placeholder, key) => (
    Object.hasOwn(values, key) ? values[key] : placeholder
  ));
}

export const solanaConstants = Object.freeze({ LAMPORTS_PER_SOL });
