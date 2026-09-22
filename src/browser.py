from playwright.async_api import Browser, BrowserContext, Playwright

from src.config import (
    BROWSER_LOCALE,
    BROWSER_USER_AGENT,
    BROWSER_VIEWPORT_HEIGHT,
    BROWSER_VIEWPORT_WIDTH,
    CF_CLEARANCE,
    X_AUTH_TOKEN,
    X_CT0,
)


async def init_browser_context(
    p: Playwright, headless: bool = True
) -> tuple[Browser, BrowserContext]:
    """Menginisialisasi Playwright Chromium dengan session cookies dari environment."""
    browser = await p.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
        ],
    )

    context = await browser.new_context(
        viewport={"width": BROWSER_VIEWPORT_WIDTH, "height": BROWSER_VIEWPORT_HEIGHT},
        user_agent=BROWSER_USER_AGENT,
        locale=BROWSER_LOCALE,
        color_scheme="dark",
    )

    cookies: list[dict] = []

    if X_AUTH_TOKEN and X_AUTH_TOKEN != "masukkan_auth_token_anda_disini":
        cookies.append({
            "name": "auth_token",
            "value": X_AUTH_TOKEN,
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
        })

    if X_CT0 and X_CT0 != "masukkan_ct0_anda_disini":
        cookies.append({
            "name": "ct0",
            "value": X_CT0,
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
        })

    if CF_CLEARANCE:
        cookies.append({
            "name": "cf_clearance",
            "value": CF_CLEARANCE,
            "domain": ".x.com",
            "path": "/",
            "secure": True,
            "httpOnly": False,
        })

    if cookies:
        await context.add_cookies(cookies)
        print("[Auth] Cookie sesi X berhasil diinjeksikan.")
    else:
        print(
            "[Auth] PERINGATAN: Cookie belum diisi di .env. Scraping mungkin dibatasi login wall."
        )

    return browser, context
