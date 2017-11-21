from argparse import ArgumentParser
from bs4 import BeautifulSoup
from itertools import chain
import csv
import json
import logging
import re
import requests
import sys
import yaml

from mappings import AVAILABLE_LISTS

BASE_URL = 'https://pitchfork.com'


def _find_list_pages(soup):
    """Find the urls for each page of a given list; typically 10."""
    for link in soup.find_all('a', class_='fts-pagination__list-item__link'):
        yield link.get('href')


def _find_section_pages(soup):
    pass


def _get_list_url(period, kind):
    return AVAILABLE_LISTS['pitchfork'][period][kind]


def _make_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def get_list(period, kind, output='csv'):
    list_url = _get_list_url(period, kind)
    starter_soup = _make_soup(list_url)

    entries = []
    for url in _find_list_pages(starter_soup):
        full_url = BASE_URL + url
        soup = _make_soup(full_url)
        list_items = soup.find('div', class_='contents').find_all('strong')

        for item in list_items:
            e = _parse_entry(item)
            e['source_url'] = full_url
            entries.append(e)

            if output == 'csv':
                writer = csv.DictWriter(sys.stdout, delimiter='\t', fieldnames=e.keys())
                writer.writerow(e)
            elif output == 'json':
                json.dump(e, sys.stdout)
    return entries


def _parse_entry(entry):
    # use full parent <p> instead of just <strong> -- more reliable
    rank_artist, album, label_release = entry.parent.get_text().split('\n')
    rank, _, artist = rank_artist.partition(':')
    record_label, _, year_released = re.sub('\[|\]', '', label_release).partition(';')
    return {
        'rank': int(rank.strip()),
        'artist': artist.strip(),
        'album': album.strip(),
        'record_label': record_label.strip(),
        'year_released': year_released.strip()
    }


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--period', help='Period for list you want')
    parser.add_argument('--kind', help='albums or tracks')
    parser.add_argument('--output', default='csv', help='csv or json')
    args = parser.parse_args()

    get_list(args.period, args.kind, args.output)
