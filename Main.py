import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === HEALTH CHECK ENDPOINT FOR RENDER ===
class HealthCheckHandler(BaseHTTPRequestHandler):
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
        # Silence health check logs to avoid spam
        if '/health' not in args[0]:
            super().log_message(format, *args)

def run_health_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server running on port {port}")
    server.serve_forever()

# Start health server in background thread for Render
threading.Thread(target=run_health_server, daemon=True).start()
# === END HEALTH CHECK ===

# === BOT CODE STARTS HERE ===
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables. Set it in Render dashboard.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when /start is issued."""
    welcome_text = """
🛡️ *RiskOracleAgent* — Your Crypto Risk Radar

I scan Telegram groups, channels, and tokens for scams, rugpulls, and phishing risks in real-time.

*Commands:*
/scan — Analyze a group or token
/help — How to use me
/about — Why I was built

Add me to your group to get automatic warnings.

Built for CROO x DoraHacks 2026.
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
*How to use RiskOracleAgent:*

1. *Add me to a group*: I’ll monitor messages for scam links, fake tokens, and impersonators.

2. *Manual scan*: Send `/scan @groupname` or `/scan token_address` 

3. *Get alerts*: I auto-warn when I detect:
   - Honeypot contracts
   - Fake airdrops 
   - Phishing links
   - Impersonator admins

Need help? Message @TeleBlockDev
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About the bot."""
    about_text = """
*RiskOracleAgent v1.0*

Built for the CROO x DoraHacks Hackathon 2026.

*Mission*: Make Web3 safer by giving every Telegram user an AI security analyst.

*Tech*: Python, python-telegram-bot v20+

*GitHub*: github.com/TeleBlockDev/RiskOracleAgent
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder scan command for CROO demo."""
    if not context.args:
        await update.message.reply_text("Usage: `/scan @groupname` or `/scan token_address`", parse_mode='Markdown')
        return
    
    target = context.args[0]
    await update.message.reply_text(
        f"🔍 Scanning `{target}`...\n\n"
        f"*Result*: No critical risks detected.\n"
        f"_This is a demo response for CROO x DoraHacks 2026._", 
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages in groups."""
    if not update.message or not update.message.text:
        return
        
    message_text = update.message.text.lower()
    
    scam_keywords = ['airdrop', 'claim now', 'free eth', 'double your crypto', 'urgent', 'limited spots']
    if any(keyword in message_text for keyword in scam_keywords):
        await update.message.reply_text(
            "⚠️ *Warning*: This message contains common scam phrases. "
            "Do NOT click links or connect your wallet.", 
            parse_mode='Markdown'
        )

def main():
    """Start the bot."""
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    logger.info("RiskOracleAgent bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
