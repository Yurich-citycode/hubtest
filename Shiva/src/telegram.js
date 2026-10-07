import fs from 'node:fs';
import path from 'node:path';

const API_TIMEOUT_MS = 40_000;
const CAPTION_SAFE_LENGTH = 950;

export async function telegramApi(token, method, payload = {}) {
  let response;
  const isFormData = typeof FormData !== 'undefined' && payload instanceof FormData;
  try {
    response = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
      method: 'POST',
      headers: isFormData ? undefined : { 'content-type': 'application/json' },
      body: isFormData ? payload : JSON.stringify(payload),
      signal: AbortSignal.timeout(API_TIMEOUT_MS),
    });
  } catch (error) {
    const reason = error?.name === 'TimeoutError' ? 'тайм-аут' : 'ошибка сети';
    throw new Error(`Telegram API: ${reason}`);
  }

  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error(`Telegram API вернул некорректный ответ (HTTP ${response.status})`);
  }
  if (!response.ok || !result?.ok) {
    // Do not include request URLs or credentials in logs/errors.
    throw new Error(`Telegram API отклонил ${method} (HTTP ${response.status})`);
  }
  return result.result;
}

export function sendTelegramMessage(token, chatId, text) {
  return telegramApi(token, 'sendMessage', {
    chat_id: chatId,
    text,
    parse_mode: 'HTML',
    disable_web_page_preview: true,
  });
}

export async function sendTelegramMedia(token, chatId, text, mediaPath, mediaType = 'auto') {
  if (!mediaPath) return sendTelegramMessage(token, chatId, text);

  const extension = path.extname(mediaPath).toLowerCase();
  const isAnimation = mediaType === 'animation' || (mediaType === 'auto' && extension === '.gif');
  const field = isAnimation ? 'animation' : 'photo';
  const mimeType = {
    '.gif': 'image/gif',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
  }[extension] || 'application/octet-stream';
  const form = new FormData();
  form.append('chat_id', String(chatId));

  // Telegram's media caption has a smaller size limit than a normal message.
  // For a longer template, send the image/GIF first and the full text after it.
  const fitsCaption = text.length <= CAPTION_SAFE_LENGTH;
  if (fitsCaption) {
    form.append('caption', text);
    form.append('parse_mode', 'HTML');
  }

  const bytes = fs.readFileSync(mediaPath);
  form.append(field, new Blob([bytes], { type: mimeType }), path.basename(mediaPath));
  await telegramApi(token, isAnimation ? 'sendAnimation' : 'sendPhoto', form);

  if (!fitsCaption) await sendTelegramMessage(token, chatId, text);
}
