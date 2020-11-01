import random

import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request

from .utils import load_pipeline, clean_text, generate_text

def run_server(args, **kwargs):
    """Runs the console bot.

    kwargs should have three keys:

    * pipeline: Keyword arguments passed when calling transformers.pipeline,
    * generator: Keyword arguments passed when calling the pipeline object + seed,
    * chatbot: Keyword arguments for setting up the chatbot."""
    pipeline_kwargs = kwargs.get('pipeline', {})
    generator_kwargs = kwargs.get('generator', {})
    chatbot_kwargs = kwargs.get('chatbot', {})

    # Prepare the pipeline
    pipeline = load_pipeline(**pipeline_kwargs)

    # Run the chatbot
    max_turns_history = chatbot_kwargs.get('max_turns_history', 2)
    message_selector = chatbot_kwargs.get('message_selector', random.choice)
    turns = {}

    app = Flask(__name__)

    @app.route('/bot', methods=['POST'])
    def query_bot():
        if request.args.get('message'):
            prompt = request.args.get('message')
        else:
            result = {"status": 400, "msg": "Message cannot be empty"}
            return jsonify(result)

        if request.args.get('chat_id'):
            chat_id = request.args.get('chat_id')
        else:
            result = {"status": 400, "msg": "Chat ID cannot be empty"}
            return jsonify(result)

        # A single turn is a group of user messages and bot responses right after
        turn = {
            'user_messages': [],
            'bot_messages': []
        }

        # turns[chat_id]
        if chat_id not in turns:
            turns[chat_id] = []

        turns[chat_id].append(turn)

        turn['user_messages'].append(prompt)
        prompt = ""
        from_index = max(len(turns[chat_id]) - max_turns_history - 1, 0) if max_turns_history >= 0 else 0
        for turn in turns[chat_id][from_index:]:
            # Each turn begins with user messages
            for user_message in turn['user_messages']:
                prompt += clean_text(user_message) + pipeline.tokenizer.eos_token
            for bot_message in turn['bot_messages']:
                prompt += clean_text(bot_message) + pipeline.tokenizer.eos_token

        # Generate bot messages
        bot_messages = generate_text(prompt, pipeline, **generator_kwargs)
        if len(bot_messages) == 1:
            bot_message = bot_messages[0]
        else:
            bot_message = message_selector(bot_messages)

        turn['bot_messages'].append(bot_message)
        app.logger.info('prompt: %s', prompt)
        app.logger.info('bot_message: %s', bot_message)
        app.logger.info('turns[chat_id]: %s', turns[chat_id])
        return jsonify(bot_message)

    handler = RotatingFileHandler(args.log, maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host=args.host, port=args.port)
