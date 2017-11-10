import os
import random

import boto3
from flask import json

CFG_FILE_NAME = 'config.json'
PATHS_TO_SEARCH = ['', '/tmp/']
PATH_FOR_S3_CACHE = '/tmp/' + CFG_FILE_NAME


class PyfightConfig:
    @classmethod
    def get(cls, key):
        if key in os.environ:
            return os.environ.get(key)

        for path in PATHS_TO_SEARCH:
            potential_config_path = os.path.join(path, CFG_FILE_NAME)
            if random.uniform(0, 1) > 0.9:
                if os.path.isfile(potential_config_path):
                    print("Config Cache Bust")
                    os.remove(CFG_FILE_NAME)

            if os.path.isfile(potential_config_path):
                with open(potential_config_path) as json_data:
                    d = json.load(json_data)
                    if key in d:
                        return d[key]

        if 'CFG_BUCKET_NAME' not in os.environ:
            return None
        print("Attempting S3 config download")
        s3 = boto3.client('s3')
        s3.download_file(os.environ.get('CFG_BUCKET_NAME'), 'config.json', PATH_FOR_S3_CACHE)
        with open(PATH_FOR_S3_CACHE) as json_data:
            print("wrote config file")
            d = json.load(json_data)
            if key in d:
                return d[key]

        return None
