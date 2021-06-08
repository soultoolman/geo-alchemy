# -*- coding: utf-8 -*-
import logging

import click

from .pp import pp
from .reanno import reanno


@click.group()
@click.option(
    '-d', '--debug-mode', is_flag=True,
    help='enable debug mode'
)
@click.option(
    '-l', '--log-file', type=click.Path(exists=False),
    default='geo-alchemy.log', show_default=True, help='log file'
)
def geo_alchemy(debug_mode, log_file):
    """
    geo-alchemy command line suite
    """
    level = logging.DEBUG if debug_mode else logging.WARNING
    logging.basicConfig(level=level, filename=log_file)


geo_alchemy.command('pp')(pp)
geo_alchemy.command('reanno')(reanno)
