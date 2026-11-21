# Private Telegram media review

## Purpose
Deliver generated Nūr media to a configured private Telegram chat so the owner can inspect previews on a phone without downloading GitHub Actions artifacts.

## GitHub Actions secrets
Configure these repository Actions secrets:
- `TELEGRAM_BOT_TOKEN`: the token issued by BotFather for the existing Nūr bot.
- `TELEGRAM_REVIEW_CHAT_ID`: optional preferred numeric chat ID for the private review conversation. If this is not set, the review step reuses the existing `TELEGRAM_CHAT_ID` secret.

Do not put either value in source code, workflow literals, issue comments or chat messages. Start the bot conversation and send it a message before the first run so Telegram permits the bot to message that chat. The existing `TELEGRAM_CHAT_ID` can be reused when it points to your private one-to-one conversation; no duplicate secret is required.

## Workflow
1. Generate the editorial image, vertical video and metadata.
2. Upload the GitHub Actions artifact as a backup.
3. Run `telegram_review.py`. If either Telegram secret is missing, the step logs a skip and leaves the generated artifact intact.
4. The review script requires `qa.status == passed`, then sends the PNG using `sendPhoto` and the MP4 using `sendVideo`. If Telegram rejects inline video delivery through its Bot API response, it retries the MP4 as a document.
5. Topic history is saved as before.

## Separation from publishing
`telegram_review.py` is preview-only. It does not publish to public social channels and does not read or set `NUR_APPROVED`. The existing `telegram_publisher.py` keeps its explicit `NUR_APPROVED=yes` and passing-QA checks. Do not merge review and publishing destinations or use a public channel as the review chat.

## Verification and limitations
Unit tests mock Telegram API responses and verify credential skip, private chat routing, QA blocking and document fallback. They do not prove that the real bot token or chat ID is correct. A real workflow run is required to verify delivery. Telegram's Bot API and account/file-size constraints may affect inline playback; a document fallback preserves access to the MP4 but may require opening it manually.
