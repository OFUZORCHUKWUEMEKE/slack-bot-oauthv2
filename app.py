# from flask import Flask
# from slack_bolt import App
# from slack_bolt.adapter.flask import SlackRequestHandler
# from config.settings import (
#     SIGNING_SECRET, SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SLACK_APP_TOKEN,
#     oauth_settings, state_store, authorize_url_generator
# )
# from slacke.events import handle_message_events, handle_app_mention_events
# from slacke.commands import handle_update_bot
# from slacke.oauth import install, oauth_redirect
# from agents.llm_agent import agent, llm

# flask_app = Flask(__name__)

# bolt_app = App(
#     signing_secret=SIGNING_SECRET,
#     oauth_settings=oauth_settings,
#     token_verification_enabled=False
# )

# handler = SlackRequestHandler(bolt_app)

# # Register Slack event handlers
# bolt_app.event("message")(handle_message_events)
# bolt_app.event("app_mention")(handle_app_mention_events)
# bolt_app.command("/update-bot")(handle_update_bot)

# # Flask routes
# @flask_app.route("/slack/events", methods=["POST"])
# def slack_events():
#     return handler.handle(request)

# @flask_app.route("/slack/install", methods=["GET"])
# def slack_install():
#     return handler.handle()

# @flask_app.route("/slack/oauth_redirect", methods=["GET"])
# def slack_oauth_redirect():
#     return oauth_redirect()

# @flask_app.route('/slack/commands/change-profile', methods=['POST'])
# def change_profile():
#     # Get data from the slash command
#     data = request.form
#     text = data.get('text', '')
#     team_id = data.get('team_id')
#     # team_id = 
    
#     # Parse the command arguments (username and profile_url)
#     args = text.split()
#     if len(args) >= 2:
#         new_username = args[0]
#         new_profile_url = args[1]
        
#         try:
#             installation_store = FileInstallationStore(base_dir="./data/installations")
#             installation = installation_store.find_installation(
#             enterprise_id=None,
#             team_id=team_id,
#             is_enterprise_install=False
#            )
#             if not installation:
#                logger.error(f"No installation found for team: {team_id}")
#                return
#             # installation_store.find
    
#             if not installation:
#               logger.error(f"No installation found for team: {team_id}")
#               return
#             # For user tokens only (not bot tokens)
#             # This requires user token with users.profile:write scope
#             # Note: This doesn't work with bot tokens as mentioned earlier
         
#             # For the specific message posting with custom appearance
#             # This works with bot tokens if you have chat:write.customize scope
#             client = WebClient(token=installation.bot_token)
#             channel_id = data.get('channel_id')
#             client.chat_postMessage(
#                 channel=channel_id,
#                 text=f"This message appears with my new identity!",
#                 username=new_username,
#                 icon_url=new_profile_url
#             )
#             supabase.table("teams").insert([{
#                 "team_id":team_id,
#                 "username":new_username,
#                 "image_url":new_profile_url
#             }]).execute()
                
#         except SlackApiError as e:
#             return jsonify({
#                 "response_type": "ephemeral",
#                 "text": f"Error: {e.response['error']}"
#             })
#     else:
#         return jsonify({
#             "response_type": "ephemeral",
#             "text": "Usage: /change-profile [new_username] [profile_image_url]"
#         })

# @flask_app.route("/", methods=["GET"])
# def home():
#     return "Slack Bot is running! <a href='/slack/install'>Install this bot</a>"

# # if __name__ == "__main__":
# #     app.run(port=int(os.getenv("PORT", 3000)))
# app = flask_app



import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from llama_index.llms.ollama import Ollama
from slack_bolt.async_app import AsyncApp
from llama_index.llms.gemini import Gemini
from llama_index.core import Settings
import requests
import json
import time
from llama_index.core.agent import ReActAgent
from pydantic import BaseModel,EmailStr,validator
from llama_index.core.tools import FunctionTool
import ollama
from dotenv import load_dotenv
from typing import Optional
from supabase import create_client
from flask import Flask , request
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
from slack_sdk.oauth import AuthorizeUrlGenerator
import html
from slack_sdk import WebClient

# from llama_index.core.llms import ChatMessage

# Initializes your app with your bot token and socket mode handler
# app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
load_dotenv()

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY=os.getenv("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
SLACK_APP_TOKEN=os.getenv("SLACK_APP_TOKEN")
# SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
SIGNING_SECRET=os.getenv("SIGNING_SECRET")
SLACK_CLIENT_ID=os.getenv("SLACK_CLIENT_ID")
SLACK_REDIRECT_URI=os.getenv("SLACK_REDIRECT_URL")
SLACK_CLIENT_SECRET=os.getenv("SLACK_CLIENT_SECRET")

oauth_settings = OAuthSettings(
    client_id=SLACK_CLIENT_ID,
    client_secret=SLACK_CLIENT_SECRET,
    scopes=[
        "app_mentions:read",
        "assistant:write",
        "bookmarks:read",
        "bookmarks:write",
        "calls:read",
        "channels:history",
        "channels:read", 
        "chat:write",
        "groups:history",
        "im:history",
        "chat:write.customize"
        ],
    installation_store=FileInstallationStore(base_dir="./data/installations"),
    state_store=FileOAuthStateStore(expiration_seconds=900, base_dir="./data/states"),
    install_path="/slack/install",
    redirect_uri_path="/slack/oauth_redirect",
)

state_store = FileOAuthStateStore(expiration_seconds=300, base_dir="./data")

authorize_url_generator = AuthorizeUrlGenerator(
    client_id=os.environ["SLACK_CLIENT_ID"],
    scopes=["app_mentions:read", "chat:write"],
    user_scopes=["search:read"],
)

bolt_app = App(
    signing_secret=SIGNING_SECRET,
    oauth_settings=oauth_settings,
    token_verification_enabled=False
    )

flask_app = Flask(__name__)
handler = SlackRequestHandler(bolt_app)

llm = Gemini(
    model="models/gemini-1.5-flash",
    api_key=GEMINI_API_KEY,  # uses GOOGLE_API_KEY env var by default
)

Settings.llm = llm

supabase = create_client(supabase_key=SUPABASE_SERVICE_KEY,supabase_url=SUPABASE_URL)

class UserPaymentInfo(BaseModel):
    email: EmailStr
    username: str
    phone_number: str
    amount: str
    
    # @validator('age')
    # def age_must_be_valid(cls, v):
    #     if v < 18:
    #         raise ValueError('User must be at least 18 years old')
    #     if v > 120:
    #         raise ValueError('Age seems too high, please verify')
    #     return v
    
    # @validator('amount')
    # def amount_must_be_positive(cls, v):
    #     if v <= 0:
    #         raise ValueError('Amount must be greater than 0')
    #     return v

def create_payment_link(
    email: str,
    username: str,
    phone_number: str,
    amount: str,
) -> str:
    """
    Create a payment link for a user and store their information in Supabase.
    
    Args:
        email: User's email address
        username: User's preferred username
        amount: Payment amount in USD
        phone_number: Description of the payment
        
    Returns:
        URL of the payment link
    """

    try:
        # Validate user information using Pydantic model
        user_info = UserPaymentInfo(
            email=email,
            username=username,
            amount=amount,
            phone_number=phone_number
        )
        result = supabase.table("payments").insert([{
            "email":user_info.email,
            "username":user_info.username,
            "amount":user_info.amount,
            "phone_number":user_info.phone_number
        }]).execute()
        payment_id = result.data[0]["id"]
        
        payment_link_url = "http://www.fourier.com/payment/ADF321"

        return f"Payment link created successfully: {payment_link_url} your payment id is {payment_id}"
    except ValueError as e:
        return f"Validation error: {str(e)}"
    except Exception as e:
        return f"Error creating payment link: {str(e)}" 

payment_link_tool = FunctionTool.from_defaults(
    name="create_payment_link",
    description="Create a payment link and store user information in the database",
    fn=create_payment_link
)

agent = ReActAgent.from_tools(
    [payment_link_tool],
    verbose=True,
    system_prompt=(
        "You are a helpful assistant that can create payment links for users. "
        "You need to collect their email, username, and age. "
        "Users must be at least 18 years old to make payments."
    )
)

def query_gemini(prompt):
    """
    Sends a prompt to gemini and get a response
    """
    try:
        # response = llm.complete(prompt)
        # return response.text
        response = agent.chat(prompt)
        return response.response
        
    except Exception as e:
        return f"Failed to communicate with gemini: {str(e)}"



# Alternative function if using Ollama
def query_ollama(prompt, model="mistral"):
    """
    Send a prompt to Ollama and get a response.
    """
    try:
        import ollama
        
        response = ollama.chat(model=model, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        
        return response['message']['content']
    
    except Exception as e:
        return f"Failed to communicate with Ollama: {str(e)}"


@bolt_app.event("message")
def handle_message_events(body, logger):
    # Only respond to messages in DMs with the bot
    if body["event"].get("channel_type") == "im":
        user = body["event"]["user"]
        text = body["event"].get("text", "")
        channel_id = body["event"]["channel"]
        
        # Acknowledge receipt with a typing indicator
        bolt_app.client.chat_postMessage(
            channel=channel_id,
            text="Thinking...",
            # thread_ts=body["event"].get("ts")
        )
        
        # Get response from local LLM
        # llm_response = query_ollama(text)
        llm_response = query_gemini(text)
        print(llm_response)
        # Or if using Ollama:
        # llm_response = query_ollama(text)
        
        # Send the LLM's response back to Slack
        bolt_app.client.chat_update(
            channel=channel_id,
            ts=app.client.chat_postMessage(
                channel=channel_id,
                text=llm_response,
                # thread_ts=body["event"].get("ts")
            )["ts"],
            text=llm_response
        )

# Make sure your event handler has the exact signature expected by Slack Bolt
@bolt_app.event("app_mention")
def handle_app_mention_events(body, logger):
    logger.info(body)
    
    # Extract event details
    event = body["event"]
    channel_id = event["channel"]
    user = event["user"]
    text = event["text"]

    db_username = None
    image_url = None
    username = None
    image_url = None
    
    # Get the installation for this team
    team_id = body.get("team_id")
    if not team_id:
        logger.error("No team_id found in request body")
        return
    
    # Find the installation for this team
    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id,
            is_enterprise_install=False
    )
    if not installation:
       logger.error(f"No installation found for team: {team_id}")
       return
    # installation_store.find
    response = supabase.table("teams").select('*').eq("team_id",team_id).execute()
    if response.data:
        user_data = response.data[0]
        db_username = user_data.get('username')
        image_url = user_data.get('image_url')
    
     # Use custom profile if available
    if db_username:
       username = db_username
            
            # Use image_url instead of emoji if available
    if image_url:
      icon_url = image_url
      icon_emoji = None  # Clear emoji if we have an image URL


    import re
    mention_pattern = re.compile(r'<@([A-Z0-9]+)>')
    match = mention_pattern.search(text)
    if match:
        bot_user_id = match.group(1)
        text = text.replace(f"<@{bot_user_id}>", "").strip()
    
    try:
        # Get response from Ollama
        # llm_response = query_ollama(text)
        
        llm_response = query_gemini(text)
        if username and image_url:
            client = WebClient(token=installation.bot_token)
            client.chat_postMessage(
              channel=channel_id,
              text=llm_response,
              username=username,
              icon_url=image_url
          )
        else:
            client = WebClient(token=installation.bot_token)
            client.chat_postMessage(
              channel=channel_id,
              text=llm_response,
            )

    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        bolt_app.client.chat_postMessage(
            channel=channel_id,
            text=f"Sorry, I encountered an error: {str(e)}",
            thread_ts=event.get("ts"),
            

        )

def download_image(url, save_path="temp_image.jpg"):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path
    else:
        raise Exception(f"Failed to download image from {url}")

# Function to change the bot's profile name
def set_bot_name(new_name):
    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id,
            is_enterprise_install=False
    )
    # installation_store.find
    
    if not installation:
        logger.error(f"No installation found for team: {team_id}")
        return
    try:
        client = WebClient(token=installation.bot_token)
        client.users_profile_set(
            profile={"first_name": new_name}
        )
        return True
    except SlackApiError as e:
        return f"Error setting name: {e.response['error']}"

def set_bot_image(image_path):
    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id,
            is_enterprise_install=False
    )
    # installation_store.find
    
    if not installation:
        logger.error(f"No installation found for team: {team_id}")
        return
    try:
        client = WebClient(token=installation.bot_token)
        client.users_setPhoto(image=image_path)
        return True
    except SlackApiError as e:
        return f"Error setting image: {e.response['error']}"
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

@bolt_app.command("/update-bot")
def handle_update_bot(ack, body, say):
    # Acknowledge the command immediately
    ack()

    # Get the command text (e.g., "NewName https://example.com/image.jpg")
    command_text = body.get("text", "").strip()
    if not command_text:
        say("Please provide a name and image URL, e.g., `/update-bot NewName https://example.com/image.jpg`")
        return

    # Split the text into name and URL
    parts = command_text.split(" ", 1)
    if len(parts) != 2:
        say("Invalid format. Use: `/update-bot [name] [image-url]`")
        return

    new_name, image_url = parts

    # Update the bot's name
    name_result = set_bot_name(new_name)
    if name_result is not True:
        say(name_result)
        return

    installation_store = FileInstallationStore(base_dir="./data/installations")
    installation = installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id,
            is_enterprise_install=False
    )
    if not installation:
        logger.error(f"No installation found for team: {team_id}")
        return
    # installation_store.find
    
    if not installation:
        logger.error(f"No installation found for team: {team_id}")
        return

    # Download and update the bot's image
    try:
        image_path = download_image(image_url)
        image_result = set_bot_image(image_path)
        if image_result is not True:
            say(image_result)
            return
        say(f"Updated bot to name '{new_name}' with new image!")
    except Exception as e:
        say(f"Error processing image: {str(e)}")

@flask_app.route('/slack/commands/change-profile', methods=['POST'])
def change_profile():
    # Get data from the slash command
    data = request.form
    text = data.get('text', '')
    team_id = data.get('team_id')
    # team_id = 
    
    # Parse the command arguments (username and profile_url)
    args = text.split()
    if len(args) >= 2:
        new_username = args[0]
        new_profile_url = args[1]
        
        try:
            installation_store = FileInstallationStore(base_dir="./data/installations")
            installation = installation_store.find_installation(
            enterprise_id=None,
            team_id=team_id,
            is_enterprise_install=False
           )
            if not installation:
               logger.error(f"No installation found for team: {team_id}")
               return
            # installation_store.find
    
            if not installation:
              logger.error(f"No installation found for team: {team_id}")
              return
            # For user tokens only (not bot tokens)
            # This requires user token with users.profile:write scope
            # Note: This doesn't work with bot tokens as mentioned earlier
         
            # For the specific message posting with custom appearance
            # This works with bot tokens if you have chat:write.customize scope
            client = WebClient(token=installation.bot_token)
            channel_id = data.get('channel_id')
            client.chat_postMessage(
                channel=channel_id,
                text=f"This message appears with my new identity!",
                username=new_username,
                icon_url=new_profile_url
            )
            supabase.table("teams").insert([{
                "team_id":team_id,
                "username":new_username,
                "image_url":new_profile_url
            }]).execute()
                
        except SlackApiError as e:
            return jsonify({
                "response_type": "ephemeral",
                "text": f"Error: {e.response['error']}"
            })
    else:
        return jsonify({
            "response_type": "ephemeral",
            "text": "Usage: /change-profile [new_username] [profile_image_url]"
        })

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

@flask_app.route("/slack/install", methods=["GET"])
def install():
    # state = state_store.issue()
    # # https://slack.com/oauth/v2/authorize?state=(generated value)&client_id={client_id}&scope=app_mentions:read,chat:write&user_scope=search:read
    # url = authorize_url_generator.generate(state)
    # return f'<a href="{html.escape(url)}">' \
    #        f'<img alt=""Add to Slack"" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a>'
    return handler.handle(request)

@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
    return handler.handle(request)

# Simple home page
@flask_app.route("/", methods=["GET"])
def home():
    return "Slack Bot is running! <a href='/slack/install'>Install this bot</a>"

# if __name__ == "__main__":
    # SocketModeHandler(app, SLACK_APP_TOKEN).start()
    # flask_app.run(port=os.getenv("PORT",3000))
#     # app.start(port=int(os.getenv("PORT",3000)))
app = flask_app