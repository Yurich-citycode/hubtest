import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const projectDir = path.resolve(here, '..');

function loadDotEnv(filePath = path.join(projectDir, '.env')) {
  if (!fs.existsSync(filePath)) return;

  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const separator = trimmed.indexOf('=');
    if (separator < 1) continue;

    const key = trimmed.slice(0, separator).trim();
    let value = trimmed.slice(separator + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = value;
  }
}

loadDotEnv();

function positiveInteger(value, fallback, name, min = 1) {
  const parsed = Number.parseInt(value ?? '', 10);
  if (!Number.isFinite(parsed) || parsed < min) {
    if (value !== undefined && value !== '') throw new Error(`${name} должен быть целым числом не меньше ${min}`);
    return fallback;
  }
  return parsed;
}

function nonNegativeNumber(value, fallback, name) {
  if (value === undefined || value === '') return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`${name} должен быть числом не меньше 0`);
  return parsed;
}

const tokenMint = (process.env.TOKEN_MINT || '3YhtPb2TTr671vg6zoStj2896sQoSSNBKyJzvzHQogib').trim();
if (!/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(tokenMint)) {
  throw new Error('TOKEN_MINT должен быть корректным Solana-адресом (base58, 32–44 символа)');
}

const messageTemplateFile = (process.env.MESSAGE_TEMPLATE_FILE || 'message.html').trim();
const mediaFile = (process.env.MEDIA_FILE || '').trim();
const mediaType = (process.env.MEDIA_TYPE || 'auto').trim().toLowerCase();

export const config = Object.freeze({
  telegramToken: (process.env.TELEGRAM_BOT_TOKEN || '').trim(),
  telegramChatId: (process.env.TELEGRAM_CHAT_ID || '').trim(),
  tokenMint,
  tokenSymbol: (process.env.TOKEN_SYMBOL || 'TOKEN').trim().slice(0, 32) || 'TOKEN',
  quoteMint: (process.env.QUOTE_MINT || '').trim(),
  quoteSymbol: (process.env.QUOTE_SYMBOL || 'SHIB').trim().slice(0, 16) || 'SHIB',
  minBuyAmount: nonNegativeNumber(process.env.MIN_BUY_AMOUNT, 0, 'MIN_BUY_AMOUNT'),
  rpcUrl: (process.env.SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com').trim(),
  pollIntervalMs: positiveInteger(process.env.POLL_INTERVAL_MS, 15_000, 'POLL_INTERVAL_MS', 2_000),
  commitment: (process.env.COMMITMENT || 'confirmed').trim(),
  maxSignaturePages: positiveInteger(process.env.MAX_SIGNATURE_PAGES, 5, 'MAX_SIGNATURE_PAGES', 1),
  messageTemplatePath: path.resolve(projectDir, messageTemplateFile),
  mediaPath: mediaFile ? path.resolve(projectDir, mediaFile) : '',
  mediaType,
  statePath: path.join(projectDir, 'data', 'state.json'),
});

export function validateConfig() {
  if (!config.telegramToken || config.telegramToken === 'PASTE_NEW_TOKEN_HERE') {
    throw new Error('Укажите новый TELEGRAM_BOT_TOKEN в файле Shiva/.env');
  }
  try {
    new URL(config.rpcUrl);
  } catch {
    throw new Error('SOLANA_RPC_URL должен быть URL');
  }
  if (config.quoteMint && !/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(config.quoteMint)) {
    throw new Error('QUOTE_MINT должен быть корректным Solana-адресом или оставьте поле пустым');
  }

  if (!fs.existsSync(config.messageTemplatePath) || !fs.statSync(config.messageTemplatePath).isFile()) {
    throw new Error(`Не найден файл шаблона сообщения: ${config.messageTemplatePath}`);
  }
  if (config.mediaType !== 'auto' && config.mediaType !== 'photo' && config.mediaType !== 'animation') {
    throw new Error('MEDIA_TYPE должен быть auto, photo или animation');
  }
  if (config.mediaPath) {
    if (!fs.existsSync(config.mediaPath) || !fs.statSync(config.mediaPath).isFile()) {
      throw new Error(`Не найден файл фото/GIF: ${config.mediaPath}`);
    }
    const extension = path.extname(config.mediaPath).toLowerCase();
    const supported = config.mediaType === 'animation'
      ? ['.gif']
      : config.mediaType === 'photo'
        ? ['.jpg', '.jpeg', '.png']
        : ['.gif', '.jpg', '.jpeg', '.png'];
    if (!supported.includes(extension)) {
      throw new Error('Для фото используйте JPG/PNG, для GIF — файл .gif. Проверьте MEDIA_FILE и MEDIA_TYPE.');
    }
  }
}
