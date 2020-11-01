import argparse

from gpt2bot.flask_bot import run_server
from gpt2bot.utils import parse_config

if __name__ == '__main__':
    # Script arguments can include path of the config
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--config', type=str, default="chatbot.cfg")
    arg_parser.add_argument('--host', type=str, default="0.0.0.0")
    arg_parser.add_argument('--port', type=str, default="5011")
    arg_parser.add_argument('--log', type=str, default="../logs/gtp2bot.log")
    args = arg_parser.parse_args()
    config_path = args.config

    config = parse_config(config_path)
    run_server(args, **config)