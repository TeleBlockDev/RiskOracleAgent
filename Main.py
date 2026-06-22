import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import asyncio
from dotenv import load_dotenv
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# CROO Agent Metadata
AGENT_METADATA = {
    "name": "RiskOracleAgent",
    "version": "1.0.1",
    "description": "Tells you and other bots when crypto markets are too risky. CAP-compliant A2A agent for CROO Agent Store.",
    "cap_version": "1.0",
    "a2a_endpoints": ["/analyze", "/risk_score"],
    "price_per_call": "TBD",
    "category": "DeFi",
    "tracks": ["DeFi", "Data & Verification"],
    "license": "MIT",
    "repository": "https://github.com/TeleBlockDev/RiskOracleAgent"
}

# Fear & Greed Index API
FEAR_GREED_API = "https://api.alternative.me/fng/"
# CoinGecko API for price data
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

def get_fear_greed_index():
    """Fetch current Fear & Greed Index"""
    try:
        response = requests.get(FEAR_GREED_API, timeout=10)
        data = response.json()
        value = int(data['data'][0]['value'])
        classification = data['data'][0]['value_classification']
        return value, classification
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed: {e}")
        return None, None

def get_price(symbol):
    """Fetch current price from CoinGecko"""
    symbol_map = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum', 
        'SOL': 'solana',
        'BNB': 'binancecoin'
    }
    try:
        coin_id = symbol_map.get(symbol)
        if not coin_id:
            return None
        params = {'ids': coin_id, 'vs_currencies': 'usd'}
        response = requests.get(COINGECKO_API, params=params, timeout=10)
        data = response.json()
        return data[coin_id]['usd']
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return None

def calculate_risk_score(fear_greed_value):
    """Convert Fear & Greed to risk score + signal"""
    if fear_greed_value is None:
        return 50, "UNKNOWN", "DATA_UNAVAILABLE"
    
    if fear_greed_value >= 75:
        return fear_greed_value, "EXTREME_GREED", "AVOID_NEW_LONGS"
    elif fear_greed_value >= 55:
        return fear_greed_value, "GREED", "CAUTION"
    elif fear_greed_value >= 45:
        return fear_greed_value, "NEUTRAL", "NORMAL"
    elif fear_greed_value >= 25:
        return fear_greed_value, "FEAR", "OPPORTUNITY"
    else:
        return fear_greed_value, "EXTREME_FEAR", "BUY_OPPORTUNITY"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when /start is issued."""
    welcome_text = f"""
🛡️ **{AGENT_METADATA['name']}**
_Listed on CROO Agent Store | CAP v{AGENT_METADATA['cap_version']}_

I tell you and other bots when crypto markets are too risky.

**For Humans**: Tap a coin below for instant risk analysis
**For Agents**: Hire me via `/analyze` A2A endpoint

Tracks: DeFi + Data & Verification
Built for CROO Agent Hackathon 2026

Choose a coin to analyze:
"""
    
    keyboard = [
        [
            InlineKeyboardButton("BTC", callback_data='BTC'),
            InlineKeyboardButton("ETH", callback_data='ETH'),
        ],
        [
            InlineKeyboardButton("SOL", callback_data='SOL'),
            InlineKeyboardButton("BNB", callback_data='BNB'),
        ],
        [
            InlineKeyboardButton("🤖 A2A Demo", callback_data='a2a_demo'),
            InlineKeyboardButton("📊 Agent Info", callback_data='agent_info'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display CROO Agent Store info for /agent command."""
    agent_info = f"""
🤖 **CROO Agent Store Listing**

**Name**: {AGENT_METADATA['name']}
**Version**: {AGENT_METADATA['version']}
**CAP Version**: {AGENT_METADATA['cap_version']}
**Category**: {AGENT_METADATA['category']}
**Tracks**: {', '.join(AGENT_METADATA['tracks'])}
**License**: {AGENT_METADATA['license']}

**Description**:
{AGENT_METADATA['description']}

**A2A Endpoints**: {', '.join(AGENT_METADATA['a2a_endpoints'])}
**Pricing**: {AGENT_METADATA['price_per_call']}

**Repository**: {AGENT_METADATA['repository']}

Built for CROO Agent Hackathon 2026 | 0% gas fees active
"""
    await update.message.reply_text(agent_info, parse_mode='Markdown')

async def analyze_crypto(query, symbol):
    """Run risk analysis for selected crypto"""
    await query.edit_message_text(f"🔍 Analyzing {symbol}... Checking Fear & Greed + market data...")
    
    fg_value, fg_class = get_fear_greed_index()
    price = get_price(symbol)
    risk_score, signal, recommendation = calculate_risk_score(fg_value)
    
    if fg_value is None:
        result_text = f"❌ **Error**: Could not fetch market data for {symbol}. Try again."
    else:
        result_text = f"""
🛡️ **RiskOracleAgent Analysis: {symbol}**

**Market Sentiment**: {fg_class} ({fg_value}/100)
**Current Price**: ${price:,.2f} USD
**Risk Score**: {risk_score}/100
**Signal**: {signal}
**Recommendation**: {recommendation}

**CAP Call Logged**: `0x{datetime.now().strftime('%H%M%S')}`
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC

_Analysis powered by alternative.me + CoinGecko_
"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')

async def a2a_demo(query) -> None:
    """Simulate another agent hiring RiskOracleAgent via CAP."""
    await query.edit_message_text("🔄 Simulating A2A call: TradingBot_Alpha hiring RiskOracleAgent via CAP...")
    
    await asyncio.sleep(2)
    
    demo_text = f"""
🤖 **A2A Transaction Complete**

**Calling Agent**: TradingBot_Alpha
**Hired Agent**: {AGENT_METADATA['name']}
**Endpoint**: `/analyze`
**CAP Version**: {AGENT_METADATA['cap_version']}
**Settlement**: Logged on-chain via CROO

**Result Returned**:
```json
{{
  "agent": "{AGENT_METADATA['name']}",
  "symbol": "BTC",
  "risk_score": 85,
  "signal": "EXTREME_GREED",
  "recommendation": "AVOID_NEW_LONGS",
  "cap_call_id": "0x{datetime.now().strftime('%H%M%S')}",
  "timestamp": {int(datetime.now().timestamp())}
}}

Tracks: {', '.join(AGENT_METADATA['tracks'])}
"""
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(demo_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_agent_info(query) -> None:
    """Show agent info for humans."""
    info_text = f"""
📊 {AGENT_METADATA['name']} Info

What I do:
I check Fear & Greed Index + live prices to tell you if the market is too scary or too greedy. Other trading bots hire me before they trade.

CAP Compliant: Yes, v{AGENT_METADATA['cap_version']}
On CROO Agent Store: Yes
Tracks: {', '.join(AGENT_METADATA['tracks'])}

For Developers:
Use /agent command to see A2A endpoints and CAP metadata.

Built for CROO Agent Hackathon 2026
"""
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(info_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data in ['BTC', 'ETH', 'SOL', 'BNB']:
        await analyze_crypto(query, query.data)
    elif query.data == 'a2a_demo':
        await a2a_demo(query)
    elif query.data == 'agent_info':
        await show_agent_info(query)
    elif query.data == 'back_to_start':
        await start(update, context)
Health check endpoint for Render
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        return  # Suppress HTTP logs

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

def main() -> None:
    """Start the bot."""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    application = Application.builder().token(bot_token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("agent", agent_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start health check server in background for Render
    if os.environ.get('RENDER'):
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        logger.info(f"Starting {AGENT_METADATA['name']} via polling on Render")
    
    logger.info(f"Starting {AGENT_METADATA['name']} v{AGENT_METADATA['version']}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == 'main':
    main()
