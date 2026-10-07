import fs from 'node:fs';
import path from 'node:path';
import { config, validateConfig } from './config.js';
import { findBuys, formatBuyMessage, rpcCall } from './solana.js';
import { sendTelegramMedia, sendTelegramMessage, telegramApi } from './telegram.js';

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
let stopping = false;
let lastPollAt = null;
let messageTemplate = '';

function loadState() {
  try {
    const state = JSON.parse(fs.readFileSync(config.statePath, 'utf8'));
    return {
      initialized: Boolean(state.initialized),
      lastSignature: typeof state.lastSignature === 'string' ? state.lastSignature : null,
      telegramOffset: Number.isSafeInteger(state.telegramOffset) ? state.telegramOffset : 0,
    };
  } catch {
    return { initialized: false, lastSignature: null, telegramOffset: 0 };
  }
}

const state = loadState();

function saveState() {
  fs.mkdirSync(path.dirname(config.statePath), { recursive: true });
  const temporaryPath = `${config.statePath}.tmp`;
  fs.writeFileSync(temporaryPath, `${JSON.stringify(state, null, 2)}\n`, { mode: 0o600 });
  fs.renameSync(temporaryPath, config.statePath);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function commandName(text) {
  const firstWord = String(text || '').trim().split(/\s+/)[0] || '';
  return firstWord.split('@')[0].replace(/^\//, '').toLowerCase();
}

async function handleTelegramUpdate(update) {
  const message = update.message;
  if (!message?.text || !message.chat?.id) return;
  const command = commandName(message.text);
  if (!['start', 'help', 'chatid', 'status', 'test'].includes(command)) return;

  const chatId = String(message.chat.id);
  let response;
  if (command === 'start') {
    response = [
      '<b>Shiva Buybot запущен</b> 🐕',
      '',
      'Я отслеживаю покупки токена в Solana и публикую их в выбранном Telegram-чате.',
      'Команды: /help, /chatid, /status, /test.',
    ].join('\n');
  } else if (command === 'help') {
    response = [
      '<b>Настройка Buybot</b>',
      '1. Добавьте бота в группу и отправьте /chatid (в группе можно использовать /chatid@ИмяБота).',
      '2. Впишите полученный ID в TELEGRAM_CHAT_ID в файле Shiva/.env и перезапустите процесс.',
      '3. Проверьте отправку командой /test.',
      '',
      'Нужны права на отправку сообщений. Бот не хранит и не запрашивает seed-фразы или приватные ключи.',
    ].join('\n');
  } else if (command === 'chatid') {
    response = `ID этого чата: <code>${escapeHtml(chatId)}</code>\nДобавьте его в <code>TELEGRAM_CHAT_ID</code> в файле <code>Shiva/.env</code>.`;
  } else if (command === 'status') {
    const lastPoll = lastPollAt ? new Date(lastPollAt).toISOString() : 'ещё не было';
    response = [
      '<b>Статус Buybot</b>',
      `Токен: <code>${escapeHtml(config.tokenMint)}</code>`,
      `Чат для объявлений: ${config.telegramChatId ? 'настроен' : 'не настроен'}`,
      `Последняя проверка Solana: <code>${escapeHtml(lastPoll)}</code>`,
    ].join('\n');
  } else {
    const target = config.telegramChatId || chatId;
    await sendTelegramMedia(
      config.telegramToken,
      target,
      '✅ Тестовое сообщение Shiva Buybot. Проверка текста и фото/GIF.',
      config.mediaPath,
      config.mediaType,
    );
    return;
  }

  await sendTelegramMessage(config.telegramToken, chatId, response);
}

async function telegramLoop(botUsername) {
  while (!stopping) {
    try {
      const updates = await telegramApi(config.telegramToken, 'getUpdates', {
        offset: state.telegramOffset || undefined,
        timeout: 25,
        allowed_updates: ['message'],
      });

      for (const update of updates) {
        await handleTelegramUpdate(update);
        state.telegramOffset = update.update_id + 1;
        saveState();
      }
    } catch (error) {
      if (!stopping) {
        console.error(`Telegram polling error (${botUsername}): ${error.message}`);
        await sleep(3_000);
      }
    }
  }
}

async function establishBaseline() {
  if (state.initialized) return;
  const signatures = await rpcCall(config.rpcUrl, 'getSignaturesForAddress', [
    config.tokenMint,
    { limit: 1, commitment: config.commitment },
  ]);
  state.lastSignature = signatures?.[0]?.signature || null;
  state.initialized = true;
  saveState();
  console.info('Стартовая точка сохранена; старые транзакции объявляться не будут.');
}

async function getNewSignatures() {
  const found = [];
  let before;
  let cursorFound = !state.lastSignature;
  const pageSize = 100;

  for (let page = 0; page < config.maxSignaturePages; page += 1) {
    const options = { limit: pageSize, commitment: config.commitment };
    if (before) options.before = before;
    const signatures = await rpcCall(config.rpcUrl, 'getSignaturesForAddress', [config.tokenMint, options]);
    if (!Array.isArray(signatures) || signatures.length === 0) break;

    let reachedCursor = false;
    for (const item of signatures) {
      if (state.lastSignature && item.signature === state.lastSignature) {
        reachedCursor = true;
        cursorFound = true;
        break;
      }
      found.push(item);
    }
    if (reachedCursor || signatures.length < pageSize) break;
    before = signatures.at(-1).signature;
  }

  if (!cursorFound && found.length >= pageSize * config.maxSignaturePages) {
    console.warn(`За один интервал накопилось больше ${found.length} транзакций; RPC-сканер ограничен настройкой MAX_SIGNATURE_PAGES.`);
  }
  return found.reverse();
}

async function monitorLoop() {
  let retryDelay = config.pollIntervalMs;
  while (!stopping) {
    try {
      await establishBaseline();
      const signatures = await getNewSignatures();
      for (const item of signatures) {
        if (stopping) break;
        if (item.err) {
          state.lastSignature = item.signature;
          saveState();
          continue;
        }

        const transaction = await rpcCall(config.rpcUrl, 'getTransaction', [
          item.signature,
          {
            commitment: config.commitment,
            encoding: 'jsonParsed',
            maxSupportedTransactionVersion: 0,
          },
        ]);
        if (!transaction) {
          // It may not yet be available at the chosen commitment. Retry next poll.
          console.warn(`Транзакция ${item.signature} пока не доступна; повторю проверку.`);
          break;
        }

        const buys = findBuys(transaction, config);
        let waitingForChatId = false;
        for (const buy of buys) {
          if (!config.telegramChatId) {
            console.warn('Покупка найдена, но TELEGRAM_CHAT_ID не задан; сохраню её и повторю после настройки чата. Используйте /chatid.');
            waitingForChatId = true;
            break;
          }
          const text = formatBuyMessage(buy, item.signature, config, messageTemplate);
          await sendTelegramMedia(
            config.telegramToken,
            config.telegramChatId,
            text,
            config.mediaPath,
            config.mediaType,
          );
          console.info(`Покупка отправлена в Telegram: ${buy.buyer.slice(0, 6)}…`);
        }
        if (waitingForChatId) break;

        state.lastSignature = item.signature;
        saveState();
      }
      lastPollAt = Date.now();
      retryDelay = config.pollIntervalMs;
    } catch (error) {
      console.error(`Solana monitor error: ${error.message}`);
      retryDelay = Math.min(Math.max(config.pollIntervalMs, retryDelay * 2), 60_000);
    }

    await sleep(retryDelay);
  }
}

async function main() {
  validateConfig();
  messageTemplate = fs.readFileSync(config.messageTemplatePath, 'utf8').trimEnd();
  if (!messageTemplate) throw new Error('Файл message.html пустой — добавьте в него текст объявления.');

  const bot = await telegramApi(config.telegramToken, 'getMe');
  // getUpdates (long polling) cannot be used while a webhook is registered.
  await telegramApi(config.telegramToken, 'deleteWebhook', { drop_pending_updates: false });

  console.info(`Бот @${bot.username} запущен; мониторинг mint ${config.tokenMint}.`);
  console.info(`RPC: ${new URL(config.rpcUrl).host}; интервал: ${config.pollIntervalMs} ms.`);
  if (!config.telegramChatId) console.warn('TELEGRAM_CHAT_ID не задан. Узнайте ID командой /chatid в целевой группе и перезапустите бота.');
  if (config.quoteMint) console.info(`Отслеживается quote mint ${config.quoteMint}.`);
  else console.info(`Quote mint не задан; будет определяться по транзакции (метка SPL-актива: ${config.quoteSymbol}).`);
  console.info(config.mediaPath ? `Фото/GIF: ${config.mediaPath}` : 'Фото/GIF не заданы; бот отправляет только текст.');

  await Promise.all([telegramLoop(bot.username), monitorLoop()]);
}

process.on('SIGINT', () => {
  stopping = true;
  console.info('Остановка по SIGINT…');
});
process.on('SIGTERM', () => {
  stopping = true;
  console.info('Остановка по SIGTERM…');
});

main().catch((error) => {
  // Errors from Telegram requests deliberately never include the token or URL.
  console.error(`Buybot не запустился: ${error.message}`);
  process.exitCode = 1;
});
