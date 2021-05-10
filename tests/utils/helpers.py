import json
import os
from dotenv import load_dotenv

load_dotenv()


def read_file_data(filename):
    with open(filename, encoding="utf8") as data_file:
        json_data = json.load(data_file)
    return json_data


def print_d_msg(_msg):
    debug = os.getenv('DEBUG')
    if debug:
        print(_msg)
