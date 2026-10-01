# Slack Application Setup & Configuration Guide

> **File:** `spec/slack-configuration.md`  
> **Target System:** Slack AI Assistant with Socket Mode & Block Kit Interactivity  
> **Reference Portal:** [Slack API Portal](https://api.slack.com/apps)  

---

## 1. Overview & Connection Architecture

The assistant connects to Slack via **Socket Mode** using WebSocket connections. This eliminates the need for public IP addresses, ngrok tunnels, or incoming webhook endpoints during local development and enterprise deployment behind corporate firewalls.

```
┌───────────────────────────┐                     ┌───────────────────────────┐
│     Slack Cloud API       │◀═══ WebSocket ═════▶│   Local / Server App      │
│  (Events & Interactivity) │  (Socket Mode)      │  (slack_bolt AsyncApp)    │
└───────────────────────────┘                     └───────────────────────────┘
```

---

## 2. Step-by-Step App Creation (App Manifest Method)

The fastest and most reliable way to configure your Slack app with 100% precision is using the **App Manifest**.

### Step 1: Create App from Manifest
1. Navigate to [api.slack.com/apps](https://api.slack.com/apps).
2. Click **Create New App**.
3. In the modal, select **From an app manifest**.
4. Choose the target workspace where the bot will reside.
5. In the manifest editor, paste the YAML below into the **YAML** tab (or JSON into the **JSON** tab):

### Manifest 1: Primary Bot (AIAssistant)
```yaml
display_information:
  name: Slack AI Assistant
  description: AI assistant with file analysis, web search, and write approval gate
  background_color: "#1A1D21"
features:
  bot_user:
    display_name: AIAssistant
    always_online: true
  slash_commands:
    - command: "/ai-help"
      description: "Show available AI commands and capabilities"
      should_escape: false
    - command: "/ai-status"
      description: "View assistant operational status and diagnostics"
      should_escape: false
    - command: "/ai-reset"
      description: "Reset conversation thread memory"
      should_escape: false
    - command: "/ai-summary"
      description: "Generate executive summary of channel or thread"
      usage_hint: "[message_count or URL]"
      should_escape: false
oauth_config:
  scopes:
    bot:
      - commands
      - channels:join
      - app_mentions:read
      - channels:history
      - chat:write
      - files:read
      - files:write
      - groups:history
      - im:history
      - im:read
      - im:write
  pkce_enabled: false
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
  app_level_token_rotation_enabled: false
  is_mcp_enabled: false
```

### Manifest 2: Analyst Bot (KITA-Analyst)
```yaml
display_information:
  name: KITA Analyst
  description: Specialist AI analyst for RTO marketing compliance auditing and candidate CV ranking
  background_color: "#007A5A"
features:
  bot_user:
    display_name: KITA-Analyst
    always_online: true
  slash_commands:
    - command: "/compliance-check"
      description: "Audit document or article against RTO marketing compliance standards"
      should_escape: false
    - command: "/cv-check"
      description: "Assess candidate CVs against job description criteria"
      should_escape: false
oauth_config:
  scopes:
    bot:
      - commands
      - channels:join
      - app_mentions:read
      - channels:history
      - chat:write
      - files:read
      - files:write
      - groups:history
      - im:history
      - im:read
      - im:write
  pkce_enabled: false
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
  app_level_token_rotation_enabled: false
  is_mcp_enabled: false
```

6. Click **Next**, review the configured permissions, and click **Create**.

---

## 3. Generating Required Tokens

Three credentials are required to authenticate and run the application:

### Credential 1: App-Level Token (`SLACK_APP_TOKEN`)
*Required to establish the WebSocket connection in Socket Mode.*
1. In the app settings sidebar, click **Basic Information**.
2. Scroll down to the **App-Level Tokens** section.
3. Click **Generate Token and Scopes**.
4. Set **Token Name** to `SocketModeToken`.
5. Click **Add Scope** and select `connections:write`.
6. Click **Generate**.
7. Copy the token. It starts with `xapp-`.

### Credential 2: Bot User OAuth Token (`SLACK_BOT_TOKEN`)
*Required for API calls (reading files, posting messages, uploading documents).*
1. In the app settings sidebar, click **Install App**.
2. Click **Install to Workspace** and authorize the requested permissions.
3. Once installed, copy the **Bot User OAuth Token**. It starts with `xoxb-`.

### Credential 3: Signing Secret (`SLACK_SIGNING_SECRET`)
*Used to verify message authenticity.*
1. In the app settings sidebar, click **Basic Information**.
2. Scroll to the **App Credentials** section.
3. Locate **Signing Secret** and click **Show**.
4. Copy the secret string.

---

## 4. Required OAuth Scopes Reference

| Scope | Type | Purpose in this System |
|---|---|---|
| `files:read` | Bot | Allows the bot to download files uploaded by users (PDF, DOCX, CSV, code) via authenticated HTTP requests to `url_private_download`. |
| `files:write` | Bot | Allows the bot to call `files_upload_v2` to upload generated PDF reports and approved documents into threads. |
| `chat:write` | Bot | Allows the bot to post conversational responses and interactive Block Kit approval cards. |
| `app_mentions:read` | Bot | Allows the bot to listen to `@AIAssistant` mentions in channels. |
| `im:history` | Bot | Enables reading message threads and file attachments in 1-on-1 DMs. |
| `im:read` | Bot | Allows accessing DM channel IDs. |
| `im:write` | Bot | Allows opening DM conversations. |
| `connections:write` | App-Level | Mandatory scope for Socket Mode WebSocket communication. |

---

## 5. External LLM Provider Setup: OpenRouter

The assistant uses **OpenRouter** as the unified gateway for LLM models (e.g. Anthropic Claude 3.5 Sonnet, OpenAI GPT-4o, Google Gemini 1.5 Pro).

1. Create an account at [openrouter.ai](https://openrouter.ai).
2. Generate an API Key in your dashboard.
3. Set the key in your `.env` as `OPENROUTER_API_KEY`.
4. Default recommended model: `anthropic/claude-3.5-sonnet` (or configurable via `OPENROUTER_MODEL`).

---

## 6. Local Environment Configuration (`.env`)

Create a `.env` file in the project root:

```env
# ==============================================================================
# Slack Configuration
# ==============================================================================
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-level-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# ==============================================================================
# OpenRouter / LLM Configuration
# ==============================================================================
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# ==============================================================================
# Application & Agent Behavior
# ==============================================================================
AGENT_NAME=AIAssistant
PROPOSAL_TTL_SECONDS=1800
MAX_FILE_SIZE_BYTES=10485760
LOG_LEVEL=INFO
```

---

## 7. Verification Checklist

Before starting the bot, verify your Slack setup:
- [ ] Socket Mode is toggled to **Enabled** under *Settings > Socket Mode*.
- [ ] Interactivity is toggled to **Enabled** under *Features > Interactivity & Shortcuts*.
- [ ] Bot is invited to test channels via `/invite @AIAssistant`.
- [ ] `SLACK_APP_TOKEN` starts with `xapp-`.
- [ ] `SLACK_BOT_TOKEN` starts with `xoxb-`.
- [ ] `OPENROUTER_API_KEY` is configured and funded.
