# -*- coding: utf-8 -*-
import os
import logging
import pathlib
import subprocess as sp
from datetime import datetime
from urllib.request import urlopen, Request

from lxml import etree

from .exceptions import GeoAlchemyError


logger = logging.getLogger('geo-alchemy')


DEFAULT_RETRIES = 3
DEFAULT_REMAIN_SECONDS = 604800
DEFAULT_HEADERS = {
    'user-agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/'
        '537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    )
}


def get_request(url):
    logger.info(f'accessing {url}.')
    request = Request(url)
    for key, value in DEFAULT_HEADERS.items():
        request.add_header(key, value)
    return urlopen(request)


def remove_namespace(tree):
    """
    remove namespace of a tree

    Args:
        tree: lxml.etree._ElementTree object
    Returns:
        lxml.etree._Element without namespace
    """
    for element in tree.iter():
        element.tag = etree.QName(element).localname
    etree.cleanup_namespaces(tree)
    return tree


def date_from_geo_string(geo_string):
    """get date from GEO release date、last update date、submission date string"""
    return datetime.strptime(geo_string, '%Y-%m-%d').date()


class BaseDownloader(object):
    def __init__(self, retries=3):
        self.retries = retries

    def dl(self, url, *args, **kwargs):
        i = 1
        while True:
            if i > self.retries:
                break
            try:
                return self.start_dl(url, *args, **kwargs)
            except Exception as exc:
                logger.error(f'Error occurred when download {url}')
                logger.exception(exc)
                i += 1
        raise GeoAlchemyError(f'Error occurred when download {url}')

    def start_dl(self, url, *args, **kwargs):
        raise NotImplemented


class HttpDownloader(BaseDownloader):
    def start_dl(self, url, outfile=None):
        req = urlopen(url)
        if outfile:
            with open(outfile, 'wb') as fp:
                fp.write(req.read())
            return outfile
        return req


class AsperaDownloader(BaseDownloader):
    def __init__(
            self, retries=3,
            exe='~/.aspera/connect/bin/ascp',
            private_key_file='~/.aspera/connect/etc/asperaweb_id_dsa.openssh',
            max_rate='100m',
    ):
        self.exe = os.path.expanduser(exe)
        self.private_key_file = private_key_file
        self.max_rate = max_rate
        super(AsperaDownloader, self).__init__(retries)

    def check(self):
        if os.path.exists(
                self.exe
        ) and os.path.exists(
            self.private_key_file
        ):
            return True
        return False

    def get_command(self, url, outfile):
        return [
            self.exe, '-i', self.private_key_file, '-k1',
            '-Tr', f'-l{self.max_rate}', url, outfile
        ]

    def start_dl(self, url, outfile):
        if not self.check():
            raise GeoAlchemyError('Aspera connect is not installed correctly.')
        command = self.get_command(url, outfile)
        logger.info('running command %s', ' '.join(command))
        proc = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE)
        try:
            proc.check_returncode()
            return outfile
        except sp.CalledProcessError:
            logger.error('run command %s failed.', ' '.join(command))
            logger.error('stdout:')
            logger.error(proc.stdout.decode('utf-8'))
            logger.error('stderr:')
            logger.error(proc.stderr.decode('utf-8'))
            raise


def can_be_used(file, remain_seconds=604800):
    """
    check if file can be used
    """
    if not os.path.exists(file):
        return False
    created_time = pathlib.Path(file).stat().st_ctime
    now = datetime.now().timestamp()
    if now - created_time < remain_seconds:
        return True
    return False
