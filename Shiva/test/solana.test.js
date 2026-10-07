import test from 'node:test';
import assert from 'node:assert/strict';
import { findBuys, formatAmount, formatBuyMessage } from '../src/solana.js';

const tokenMint = 'TargetMint11111111111111111111111111111111111';
const quoteMint = 'ShibMint111111111111111111111111111111111111';
const buyer = 'Buyer111111111111111111111111111111111111111';

function cfg(overrides = {}) {
  return {
    tokenMint,
    tokenSymbol: 'DOG',
    quoteMint,
    quoteSymbol: 'SHIB',
    minBuyAmount: 0,
    ...overrides,
  };
}

function shibBuyTransaction() {
  return {
    transaction: { message: { accountKeys: [buyer] } },
    meta: {
      err: null,
      fee: 5000,
      preBalances: [1_000_000_000],
      postBalances: [999_995_000],
      preTokenBalances: [
        { accountIndex: 1, mint: quoteMint, owner: buyer, uiTokenAmount: { amount: '10000000', decimals: 6 } },
      ],
      postTokenBalances: [
        { accountIndex: 1, mint: quoteMint, owner: buyer, uiTokenAmount: { amount: '7500000', decimals: 6 } },
        { accountIndex: 2, mint: tokenMint, owner: buyer, uiTokenAmount: { amount: '250000000', decimals: 9 } },
      ],
    },
  };
}

test('detects a target-token buy paid with the configured SHIB mint', () => {
  const buys = findBuys(shibBuyTransaction(), cfg());
  assert.equal(buys.length, 1);
  assert.equal(buys[0].buyer, buyer);
  assert.equal(buys[0].tokenRaw, 250_000_000n);
  assert.equal(buys[0].tokenDecimals, 9);
  assert.equal(buys[0].quoteRaw, 2_500_000n);
  assert.equal(buys[0].quoteSymbol, 'SHIB');
});

test('applies the minimum quote amount filter', () => {
  assert.equal(findBuys(shibBuyTransaction(), cfg({ minBuyAmount: 3 })).length, 0);
  assert.equal(findBuys(shibBuyTransaction(), cfg({ minBuyAmount: 2.5 })).length, 1);
});

test('recognizes wrapped SOL as SOL instead of using the SHIB label', () => {
  const transaction = shibBuyTransaction();
  const wrappedSolMint = 'So11111111111111111111111111111111111111112';
  transaction.meta.preTokenBalances[0].mint = wrappedSolMint;
  transaction.meta.postTokenBalances[0].mint = wrappedSolMint;
  const buy = findBuys(transaction, cfg({ quoteMint: '' }))[0];
  assert.equal(buy.quoteSymbol, 'SOL');
});

test('does not treat a sale as a buy', () => {
  const transaction = shibBuyTransaction();
  transaction.meta.preTokenBalances.push({
    accountIndex: 2,
    mint: tokenMint,
    owner: buyer,
    uiTokenAmount: { amount: '250000000', decimals: 9 },
  });
  transaction.meta.postTokenBalances[1].uiTokenAmount.amount = '100000000';
  assert.deepEqual(findBuys(transaction, cfg()), []);
});

test('does not announce an airdrop or a transfer with only a network fee', () => {
  const transaction = {
    transaction: { message: { accountKeys: [buyer] } },
    meta: {
      err: null,
      fee: 5000,
      preBalances: [1_000_000_000],
      postBalances: [999_995_000],
      preTokenBalances: [],
      postTokenBalances: [
        { accountIndex: 1, mint: tokenMint, owner: buyer, uiTokenAmount: { amount: '5000000', decimals: 6 } },
      ],
    },
  };
  assert.deepEqual(findBuys(transaction, cfg()), []);
});

test('detects SOL spend and removes the transaction fee and new ATA rent', () => {
  const transaction = {
    transaction: { message: { accountKeys: [buyer, 'NewTokenAccount111111111111111111111111111111'] } },
    meta: {
      err: null,
      fee: 5000,
      preBalances: [1_000_000_000, 0],
      postBalances: [900_000_000, 2_039_280],
      preTokenBalances: [],
      postTokenBalances: [
        { accountIndex: 1, mint: tokenMint, owner: buyer, uiTokenAmount: { amount: '5000000', decimals: 6 } },
      ],
    },
  };
  const buy = findBuys(transaction, cfg({ quoteMint: '' }))[0];
  assert.ok(buy);
  assert.equal(buy.quoteKind, 'sol');
  assert.equal(buy.quoteSymbol, 'SOL');
  assert.equal(buy.quoteRaw, 97_955_720n);
});

test('formats amounts without floating-point conversion and escapes HTML symbols', () => {
  assert.equal(formatAmount(123456789012n, 6), '123,456.789012');
  const message = formatBuyMessage({
    buyer,
    tokenRaw: 1_000_000n,
    tokenDecimals: 6,
    quoteRaw: 2_500_000n,
    quoteDecimals: 6,
    quoteSymbol: '<SHIB>',
  }, 'signature123', cfg({ tokenSymbol: '<DOG>' }));
  assert.match(message, /&lt;DOG&gt;/);
  assert.match(message, /&lt;SHIB&gt;/);
  assert.match(message, /solscan\.io\/tx\/signature123/);
});

test('uses custom announcement templates and substitutes the documented fields', () => {
  const message = formatBuyMessage({
    buyer,
    tokenRaw: 1_000_000n,
    tokenDecimals: 6,
    quoteRaw: 2_500_000n,
    quoteDecimals: 6,
    quoteSymbol: 'SHIB',
  }, 'signature123', cfg(), '🔥 {token}: {token_amount} for {quote_amount} {quote_symbol} {buyer} {tx_url} {token_url}');
  assert.match(message, /^🔥 DOG: 1/);
  assert.match(message, /2\.5 SHIB/);
  assert.match(message, /solscan\.io\/account\//);
  assert.match(message, /solscan\.io\/tx\/signature123/);
  assert.match(message, /stonkfun\.xyz\/token\//);
});
