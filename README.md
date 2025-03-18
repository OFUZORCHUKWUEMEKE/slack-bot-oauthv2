## SlackBot with AI Agent Integration
A powerful Slack bot built with Slack's Bolt framework that integrates OAuth authentication and uses LlamaIndex as an AI agent for smart integrations and extensible tool capabilities.
Features

Slack OAuth Integration: Seamless authentication with Slack workspaces
Built on Bolt Framework: Leverages Slack's modern Bolt framework for reliable event handling
LlamaIndex AI Agent: Intelligent assistant capabilities powered by LlamaIndex
Extensible Architecture: Easily add new tools and capabilities
Smart Integrations: Connect with various services through the AI agent

Prerequisites

Python 3.8+
Slack App with Bot Token and necessary scopes (see config/settings.py for scopes)
Supabase account with a payments and teams table
Gemini API key (optional, for LLM integration)
Ollama installed (optional, for local LLM alternative)

## Features
1 Responds to direct messages and app mentions in Slack using LLM (Gemini or Ollama).
2 Creates payment links with user information stored in Supabase.
3 Customizable bot profile (name and image) via Slack commands.
4 OAuth support for easy installation in Slack workspaces.
5 Modular architecture for maintainability and scalability.


## Project structure
```bash
slack_bot/
├── app.py                  # Main Flask app and initialization (Entire codebase is found here , each feature can be found in the sub folders)
├── config/
│   └── settings.py         # Environment variables and configurations
├── models/
│   └── user.py            # Pydantic models for data validation
├── tools/
│   └── payment.py         # Payment link creation and tools
├── agents/
│   └── llm_agent.py       # LLM agent setup and query functions
├── slack/
│   ├── events.py          # Slack event handlers
│   ├── commands.py        # Slack command handlers
│   └── oauth.py           # Slack OAuth handlers
├── utils/
│   └── image.py           # Image download utility
└── requirements.txt        # Project dependencies
```

### Installation
1. Clone the repository
```typescript
git clone https://github.com/OFUZORCHUKWUEMEKE/slack-bot-oauthv2
cd slackbot-ai-agent
```

2. Create and activate a virtual enviroment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies
```bash
pip install -r requirements.txt
```
4.Set up environment variables:
```bash
.env.example .env
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-supabase-service-key
GEMINI_API_KEY=your-gemini-api-key
SLACK_APP_TOKEN=your-slack-app-token
SIGNING_SECRET=your-slack-signing-secret
SLACK_CLIENT_ID=your-slack-client-id
SLACK_REDIRECT_URL=your-slack-redirect-url
SLACK_CLIENT_SECRET=your-slack-client-secret
PORT=3000  # Optional, defaults to 3000
```
## Configuration

#### Supabase Table
Tables:
payments: Columns: id, email, username, phone_number, amount
teams: Columns: team_id, username, image_url

#### Slack Setup

1. Create a new Slack App at api.slack.com/apps
2. Enable the following features:
  -Bot Token Scopes (OAuth & Permissions)
  -Event Subscriptions
  -Slash Commands (optional)
3. Install the app to your workspace
4. Copy your credentials to the .env file

### Run the Application 
```bash
python app.py
```
The bot will be available at http://localhost:3000. Use a tool like ngrok to expose it to the internet for Slack integration:
```bash
ngrok http 3000
```

### Usage
#####Install the Slack App:
Visit http://localhost:3000/slack/install or your ngrok URL to install the bot in your Slack workspace.
Follow the OAuth flow to grant permissions.
Interact with the Bot:
1. Direct Messages: Send a message to the bot in a DM, and it will respond using the configured LLM.
2. App Mentions: Mention the bot (e.g., @BotName) in a channel, and it will reply.
3. Create Payment Link: Message the bot with a request like "create a payment link for email@example.com, username, phone_number, 50" to generate a payment link.
4. Chang Profile: Use the /change-profile command in Slack. e.g /change-profile {name} {iamge_url}

### Acknowledgments
Built with Slack Bolt, LlamaIndex, and Supabase.

