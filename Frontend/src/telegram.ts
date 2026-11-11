/**
 * Telegram WebApp integration layer.
 *
 * CareerMatch is a Telegram Mini App: identity comes from Telegram's
 * WebApp SDK (https://core.telegram.org/bots/webapps), not a login form.
 * This module is the single place that talks to `window.Telegram.WebApp`;
 * nothing else in the app should reach into that global directly.
 *
 * Real path: when opened inside Telegram, `window.Telegram.WebApp.initData`
 * is a signed string. We send it verbatim on every API request via the
 * `X-Telegram-Init-Data` header; Django verifies its HMAC signature against
 * the bot token (see backend users/telegram_auth.py) and resolves it to a
 * TelegramUser. The frontend never parses or trusts initData itself.
 *
 * Dev fallback: when the app is opened in an ordinary browser (no Telegram
 * object), there is no initData to send. So the app is still testable, we
 * fall back to a stable per-browser debug id sent as `X-Debug-Telegram-Id`.
 * The backend only honours that header when DEBUG=True, so this path can
 * never become the production identity mechanism.
 */

interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: {
    user?: TelegramWebAppUser;
  };
  ready: () => void;
  expand: () => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  themeParams?: Record<string, string>;
}

export interface TelegramWebAppUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
  photo_url?: string;
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

const DEV_TELEGRAM_ID_KEY = "careermatch:dev-telegram-id";

function getWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

/** Telegram display details; use backend-verified identity before showing them. */
export function getTelegramUser(): TelegramWebAppUser | null {
  return getWebApp()?.initDataUnsafe?.user ?? null;
}

/** True when actually running inside the Telegram client. */
export function isTelegramEnvironment(): boolean {
  const webApp = getWebApp();
  return !!webApp && webApp.initData.length > 0;
}

/**
 * Call once on app startup. Signals Telegram the app is ready to be shown
 * and expands it to full height. No-op outside Telegram.
 */
export function initTelegram(): void {
  const webApp = getWebApp();
  if (!webApp) return;
  webApp.ready();
  webApp.expand();
}

/**
 * A stable per-browser id used only in local development, so the same
 * "user" persists across reloads instead of getting a fresh TelegramUser
 * every time. Never used when running inside real Telegram.
 */
function getOrCreateDevTelegramId(): string {
  const envId = import.meta.env.VITE_DEV_TELEGRAM_ID as string | undefined;
  if (envId) return envId;

  const stored = localStorage.getItem(DEV_TELEGRAM_ID_KEY);
  if (stored) return stored;

  // Telegram ids are numeric; keep this one in a range that won't collide
  // with real Telegram ids (which are much larger and always positive).
  const generated = String(100000 + Math.floor(Math.random() * 899999));
  localStorage.setItem(DEV_TELEGRAM_ID_KEY, generated);
  return generated;
}

/**
 * Auth headers to attach to every backend request. Real Telegram init data
 * when available; otherwise a dev-only debug header (rejected by the
 * backend unless DJANGO_DEBUG=True).
 */
export function getAuthHeaders(): Record<string, string> {
  const webApp = getWebApp();
  if (webApp && webApp.initData) {
    return { "X-Telegram-Init-Data": webApp.initData };
  }
  return { "X-Debug-Telegram-Id": getOrCreateDevTelegramId() };
}
