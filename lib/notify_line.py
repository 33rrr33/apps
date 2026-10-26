"""Send a short notice to the user's own LINE Official Account (LINE Messaging API broadcast).

The account's only friend is the user, so a broadcast reaches just them. Free plan: 200 messages/month.
Credential (cloud environment settings, never chat): LINE_CHANNEL_TOKEN  (long-lived channel access token)

Usage:  python3 lib/notify_line.py "メッセージ本文"
Exits 0 and prints {"ok": true} on success; prints a one-line reason and exits 1 otherwise
(callers should treat a failure as non-fatal: the Claude app notice still goes out).
"""
import json, os, ssl, sys, urllib.error, urllib.request

CA = "/root/.ccr/ca-bundle.crt"
CTX = ssl.create_default_context(cafile=CA) if os.path.exists(CA) else ssl.create_default_context()

def send(text):
    token = os.environ.get("LINE_CHANNEL_TOKEN")
    if not token:
        raise SystemExit("missing environment variable LINE_CHANNEL_TOKEN")
    body = json.dumps({"messages": [{"type": "text", "text": text[:4900]}]}).encode()
    req = urllib.request.Request("https://api.line.me/v2/bot/message/broadcast", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=60) as r:
            print(json.dumps({"ok": True, "status": r.status}))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"LINE HTTP {e.code}: {e.read().decode()[:300]}")

if __name__ == "__main__":
    send(" ".join(sys.argv[1:]) or "テスト通知です")
