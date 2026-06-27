import asyncio

import requests

from load_env import TELEGRAM_BOT_TOKEN, supabase

# ─── CONFIGURATION ──────────────────────────────────────────────────────────────
CHAT_ID = "YOUR_CHAT_ID"  # Replace with your actual chat ID


# ─── TELEGRAM SENDER (synchronous, will be run in a thread) ──────────────────
def send_telegram_message(text: str) -> None:
    """Send a plain text message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")


async def send_telegram_message_async(text: str) -> None:
    """Async wrapper that offloads the blocking HTTP call to a thread."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_telegram_message, text)


# ─── REALTIME CALLBACK ──────────────────────────────────────────────────────
def handle_change(payload: dict) -> None:
    """
    Callback for any Postgres change on the 'subito' table.
    Payload keys: schema, table, event_type, new, old, etc.
    """
    event = payload.get("event_type")
    new = payload.get("new")
    old = payload.get("old")

    if event == "INSERT":
        msg = (
            f"🆕 <b>New row added</b>\n"
            f"Title: {new.get('title', 'N/A')}\n"
            f"Price: {new.get('price', 'N/A')}\n"
            f"URL: {new.get('url', 'N/A')}"
        )
    elif event == "UPDATE":
        msg = (
            f"✏️ <b>Row updated</b> (ID: {new.get('id')})\n"
            f"New Title: {new.get('title', 'N/A')}\n"
            f"Old Title: {old.get('title', 'N/A') if old else 'N/A'}\n"
            f"New Price: {new.get('price', 'N/A')}\n"
            f"Old Price: {old.get('price', 'N/A') if old else 'N/A'}"
        )
    elif event == "DELETE":
        msg = (
            f"🗑️ <b>Row deleted</b> (ID: {old.get('id')})\n"
            f"Title: {old.get('title', 'N/A')}\n"
            f"Price: {old.get('price', 'N/A')}"
        )
    else:
        msg = f"Unknown event: {event}"

    # Schedule the async send (does not block the Realtime callback)
    asyncio.create_task(send_telegram_message_async(msg))


# ─── MAIN LOOP ──────────────────────────────────────────────────────────────
async def main():
    # Subscribe to all changes on the public.subito table
    channel = supabase.channel("realtime:public:subito")
    channel.on(
        "postgres_changes",
        event="*",  # Listen to all events
        schema="public",
        table="subito",
        callback=handle_change,
    )
    channel.subscribe()
    print("✅ Listening for changes on 'subito' table. Press Ctrl+C to stop.")

    try:
        # Keep the event loop alive forever (or until interrupted)
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Unsubscribing and exiting...")
        await channel.unsubscribe()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
