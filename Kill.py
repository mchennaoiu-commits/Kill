from merged_killer import *
from flask import Flask, jsonify
import threading
import time
import os

# Create Flask app for web interface/status
app = Flask(__name__)

bot_status = {
    "status": "offline",
    "start_time": None,
    "last_update": None,
    "bot_thread": None
}

@app.route('/')
def index():
    return jsonify({
        "name": "HRK's KILLER v2.0",
        "status": bot_status["status"],
        "running_since": bot_status["start_time"],
        "last_activity": bot_status["last_update"]
    })

@app.route('/start')
def start_bot():
    """API endpoint to start the bot if it's not running"""
    if bot_status["status"] == "online":
        return jsonify({"message": "Bot is already running", "status": "online"})
    
    # Start the bot in a new thread
    start_bot_thread()
    return jsonify({"message": "Bot started successfully", "status": bot_status["status"]})

def run_bot():
    """Function to run the Telegram bot in a separate thread"""
    global bot_status
    
    print("Starting HRK's KILLER v2.0...")
    bot_status["status"] = "online"
    bot_status["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Run the bot with improved error handling
    try:
        logger.info("Bot is starting in polling mode...")
        # Use infinity polling with timeout and error handling
        bot.infinity_polling(timeout=30, long_polling_timeout=15, 
                           allowed_updates=["message"], 
                           skip_pending=True)
    except telebot.apihelper.ApiTelegramException as e:
        if "Conflict: terminated by other getUpdates request" in str(e):
            logger.error("ERROR: Another bot instance is already running! Exiting.")
        else:
            logger.error(f"Telegram API error: {e}")
        bot_status["status"] = "error"
    except KeyboardInterrupt:
        logger.info("Bot manually stopped by keyboard interrupt")
        bot_status["status"] = "stopped"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        bot_status["status"] = "error"
    finally:
        logger.info("Bot has stopped")
        bot_status["last_update"] = time.strftime("%Y-%m-%d %H:%M:%S")

def start_bot_thread():
    """Helper function to start the bot in a new thread"""
    global bot_status
    if bot_status["bot_thread"] is None or not bot_status["bot_thread"].is_alive():
        bot_status["bot_thread"] = threading.Thread(target=run_bot)
        bot_status["bot_thread"].daemon = True
        bot_status["bot_thread"].start()
        return True
    return False

# Start the bot automatically when this module is first imported (for Gunicorn)
# Always start the bot in a new thread when imported
start_bot_thread()

if __name__ == "__main__":
    # Start the bot in a separate thread
    start_bot_thread()
    
    # If running directly (not through gunicorn), start the Flask app too
    app.run(host="0.0.0.0", port=5001, debug=False)