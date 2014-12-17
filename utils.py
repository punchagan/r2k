# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

from os.path import abspath, dirname, join

from jinja2 import Environment, FileSystemLoader

HERE = dirname(abspath(__file__))

def get_template(name):
    env = Environment(loader=FileSystemLoader(join(HERE, 'templates')))
    return env.get_template(name)
