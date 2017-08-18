''' Chainer-UI API '''

import os
import argparse

from flask import Flask, render_template, jsonify, url_for
from flask_apscheduler import APScheduler

from models import Result
from database import init_db

from util import crawl_result_table


APP = Flask(__name__)


# static url cache buster
@APP.context_processor
def override_url_for():
    ''' override_url_for '''
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    ''' dated_url_for '''
    # todo: utilとかに移動したい
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(APP.root_path, endpoint, filename)
            values['_'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@APP.route('/')
def index():
    ''' / '''
    return render_template('index.html')


@APP.route('/api/v1/results', methods=['GET'])
def get_experiments():
    ''' /api/v1/results '''
    results = Result.query.all()
    return jsonify({'results': [result.serialize for result in results]})


if __name__ == '__main__':
    init_db()

    PARSER = argparse.ArgumentParser(description='chainer ui')
    PARSER.add_argument('-p', '--port', required=False, type=int, help='port', default=5000)
    ARGS = PARSER.parse_args()

    APP.config['DEBUG'] = True

    class CrawlJobConfig(object):
        ''' job config '''
        JOBS = [
            {
                'id': 'job1',
                'func': crawl_result_table,
                'trigger': 'interval',
                'seconds': 5
            }
        ]

    APP.config.from_object(CrawlJobConfig())

    SCHEDULER = APScheduler()
    SCHEDULER.init_app(APP)

    SCHEDULER.start()
    APP.run(port=ARGS.port)