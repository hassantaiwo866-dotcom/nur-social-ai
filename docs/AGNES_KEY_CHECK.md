# Agnes API key check (no generation)

This manually triggered workflow verifies that the repository secret `AGNES_API_KEY`
authenticates to Agnes's OpenAI-compatible model catalogue.

It performs only `GET https://apihub.agnes-ai.com/v1/models`. It does **not**
call chat, image, or video generation endpoints, and does not verify prices,
free quota, or whether generation is enabled for the account.

## Run it

1. Add `AGNES_API_KEY` under GitHub Actions repository secrets.
2. Open Actions → **Agnes API Key Check (No Generation)**.
3. Select **Run workflow**.
4. Review the sanitized output.

The output reports authentication status and whether these model IDs appear in
the catalogue: `agnes-2.5-flash`, `agnes-3.0-flash`,
`agnes-image-2.5-flash`, and `agnes-video-2.5-flash`.

Never paste the key into workflow inputs, logs, code, or chat. This test is
credential/catalogue verification only. Confirm free pricing in the Agnes
platform console before any generation request.

## Safety

- The script never prints the API key or response headers.
- It only makes a GET request to `/v1/models`.
- It does not attempt a generation call or automatic fallback.
- Authentication failures and network errors are reported without exposing
  response bodies.
