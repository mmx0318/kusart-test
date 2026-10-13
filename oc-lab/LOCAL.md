# Run OC Lab locally

This snapshot can start without `/home/admin/...`, a `.env`, user characters, or adult media. Missing style databases, play card pools, and adult albums are skipped. Calls that need them return an error instead of taking down the process.

## Start

```bash
cd oc-lab
python3 -m pip install flask pillow requests
OC_LAB_DEV_BYPASS_AUTH=1 python3 app.py
```

Open http://127.0.0.1:8791/

`python app.py` serves at `/`. A production `gunicorn app:app` import still defaults the login redirect and cookie path to `/oc-lab/` unless `OC_LAB_BASE` is set.

`OC_LAB_DEV_BYPASS_AUTH=1` (also `true` / `yes` / `on`) skips the shared-password gate. Without it, the login answer is `TEAM_ANSWER` or the code default `kusart`, and `python app.py` sets the cookie without the `Secure` flag so HTTP on localhost works.

Copy `.env.example` to `.env` if you want these variables on disk. `.env` is gitignored. A real environment variable overrides the file.

## What still needs real services

| Need | Variable |
| --- | --- |
| Descriptions, profiles, Ask Agent via OpenRouter | `OPENROUTER_API_KEY` |
| Ask Agent via your own bot | `ASK_AGENT_URL`, optional `ASK_AGENT_BEARER` |
| Kusa image / video tasks | `KUSA_B2B_KEY` or `OC_LAB_MMX_TOKEN` |
| Outfit / meme plays | `OPENAI_API_KEY` (falls back to `/home/admin/.openclaw/openai_key.txt`) |
| Character PV | `MINIMAX_API_KEY` |
| Style router and example JPGs | `OC_LAB_STYLE_DEMO`, `OC_LAB_TMP`, `OC_LAB_STYLE_UNI` |

Style cards on the main flow still use the `sx8/` images shipped in this snapshot. Adult type cards look for `adult/cards/`, which is not in the snapshot, so those images 404. Story manifests in `adult/stories/` are optional; the planned card still shows as in production.

## Ask Agent

`POST /api/ask-agent` with JSON:

```json
{
  "character": "御姐，黑长发，办公室里的格蕾丝，成年",
  "scene_goal": "加班后的办公室，她先开口",
  "nsfw": true,
  "dialogue": ""
}
```

`character` / `character_summary`, `scene_goal` / `goal`, `nsfw`, and `dialogue` / `existing_dialogue` are accepted. Optional `story_id`, `node_id`, `type` are forwarded to the webhook.

Response:

```json
{
  "story_beats": ["…"],
  "dialogue": [{"speaker": "格蕾丝", "line": "…"}],
  "image_prompt": "…",
  "negative_prompt": "…",
  "notes": "…",
  "source": "webhook"
}
```

`source` is `webhook` when `ASK_AGENT_URL` is set, `openrouter` when only `OPENROUTER_API_KEY` is set, or `mock` for the local demo payload. Scenes that describe minors are rejected.

In the UI, turn on 成人模式. An **Ask Agent** button sits at the bottom right and opens a panel. The same button is on the adult story player toolbar and pre-fills the current character, scene, and lines.
