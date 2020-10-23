#!/usr/bin/env python3

import configparser
import argparse
import random

import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request

from model import download_model_folder, download_reverse_model_folder, load_model
from decoder import generate_response

app = Flask(__name__)

# Script arguments can include path of the config
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('--config', type=str, default="chatbot.cfg")
arg_parser.add_argument('--host', type=str, default="0.0.0.0")
arg_parser.add_argument('--port', type=str, default="5011")
arg_parser.add_argument('--log', type=str, default="../logs/gtp2bot.log")
args = arg_parser.parse_args()

# Read the config
config = configparser.ConfigParser(allow_no_value=True)
with open(args.config) as f:
    config.read_file(f)

# Download and load main model
target_folder_name = download_model_folder(config)
model, tokenizer = load_model(target_folder_name, config)

# Download and load reverse model
use_mmi = config.getboolean('model', 'use_mmi')
if use_mmi:
    mmi_target_folder_name = download_reverse_model_folder(config)
    mmi_model, mmi_tokenizer = load_model(mmi_target_folder_name, config)
else:
    mmi_model = None
    mmi_tokenizer = None

@app.route('/query')
def query():
    # Parse parameters
    num_samples = config.getint('decoder', 'num_samples')
    max_turns_history = config.getint('decoder', 'max_turns_history')
    question = request.args.get('question')

    # Generate bot messages
    bot_messages = generate_response(
        model,
        tokenizer,
        question + tokenizer.eos_token,
        config,
        mmi_model=mmi_model,
        mmi_tokenizer=mmi_tokenizer
    )
    if num_samples == 1:
        bot_message = bot_messages[0]
    else:
        # TODO: Select a message that is the most appropriate given the context
        # This way you can avoid loops
        bot_message = random.choice(bot_messages)

    app.logger.info('bot_message: %s', bot_message)
    app.logger.info('question: %s', question)
    app.logger.info('result >>> %s', bot_message)
    result = {}
    result["msg"] = bot_message
    result["status"] = "ok"
    return jsonify(result)

if __name__ == '__main__':
    handler = RotatingFileHandler(args.log, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host=args.host, port=args.port)
