#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Programmer: Zahid Bukhari
# URL: https://github.com/zbukhari/humblebundle/
# Purpose: To look through sales at the Humble Bundle store

# Adding changes needed for python3
import argparse
import urllib
import urllib.parse
import urllib.request
from urllib.error import URLError
import json
# import yaml
# import sys
# from datetime import datetime
import time
import logging
import hashlib
import os.path

import tempfile

# This is good but I need more TLC as now responses are gzip encode.
import gzip
# from StringIO import StringIO
# from io import StringIO

# This is needed because of how promos are really done
from bs4 import BeautifulSoup

import re

# Debugging stuff
# import pdb
from pprint import PrettyPrinter
pp = PrettyPrinter(indent=2)

# Logging configuration
logging.basicConfig(filename='hb-sales.log',
	level=logging.DEBUG,
	format='%(asctime)s %(levelname)s %(funcName)s %(message)s')

### Options! ###
parser = argparse.ArgumentParser(description='Parse Humble Bundle sales.')
parser.add_argument('--force', '-f', dest='force', action='store_true', default=False,
	help='Ignore the cache file and rebuild it.')
parser.add_argument('--promo', '-p', dest='promo', default=None,
	help='Pull down a specific promotion. This is usually just a hyphen delimited string such as "coffee-stain-publisher-sale"')

args = parser.parse_args()

### Important variables ###
# This seems to be the max - we can go lower but this is what I've found.
# This doesn't seem to be used as much. 20 is the default, so one can request less but.
# https://www.humblebundle.com/store/api/search?sort=bestselling&filter=onsale&request=1&page=0
# We manipulate this URL to get the data we want.

api_url = 'https://www.humblebundle.com/store/api'
promo_url = 'https://www.humblebundle.com/store/promo'

keys_we_want = ['sale_end', 'human_name', 'full_price', 'current_price',
	'delivery_methods', 'platforms', 'user_rating', 'other_links',
	'developers', 'system_requirements', 'description', 'human_url']

# Some items are "coming soon" (i.e. coming_soon) and we want to filter those out.
# Just run the script and enjoy.
legitimizing_key = u'cta_badge'
cache_dir = 'cache'

working_headers = {
	'Accept-Encoding': 'gzip, deflate, br',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla',
	# 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0
	# Added later because it stopped working again
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
	'Accept-Language': 'en-US,en;q=0.5',
	'Connection': 'keep-alive',
	'DNT': '1',
	'Host': 'www.humblebundle.com',
	'Sec-Fetch-Dest': 'document',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'none',
	'Sec-Fetch-User': '?1',
	'Sec-GPC': '1'
}

# If num_results or num_pages is 0 - we've gone too far - too far I tell you!
# num_results	0
# page_index	6
# request	1
# num_pages	0

# Returns dictionary
def parse_data(name):
	"""This parses the JSON files we have and returns a dictionary array we can use on our web page."""

	items = []
	i = 0
	while True:
		if name in ['onsale']:
			filename = os.path.sep.join([cache_dir, '{0:s}-{1:d}.json'.format(name, i)])
		else:
			filename = os.path.sep.join([cache_dir, 'promo-{0:s}-{1:d}.json'.format(name, i)])

		try:
			logging.info('Parsing {}.'.format(filename))
			with open(filename) as f:
				json_data = json.load(f)

				if name in ['onsale']:
					base = json_data['results']
					items.extend([item['machine_name'] for item in json_data['results']])

					for item in json_data['results']:
						logging.info('Adding {0:s} [{1:s}] to list for detail grab.'.format(
							item[u'human_name'],
							item[u'machine_name']
						))
						items.append(item['machine_name'])
				else:
					# Technically we're good
					if i == 0:
						items.extend(json_data['page']['entity_lookup_dict'].keys())
					else:
						items.extend(json_data['result']['entity_keys'])

		except IOError as e:
			logging.error(e)
			break

		i += 1

	return items

# Returns boolean. Use get_max to determine when to stop.
def get_data(name, i):
	if name in ['onsale']:
		filename = os.path.sep.join([cache_dir, '{0:s}-{1:d}.json'.format(name, i)])
		params = {
			'sort': 'bestselling',
			'filter': 'onsale',
			'page': '{0:d}'.format(i),
			'request': '{0:d}'.format(i+1)
		}
		url = api_url + '/search' + '?{0:s}'.format(urllib.parse.urlencode(params))
		req = urllib.request.Request(url, headers=working_headers)
	else:
		filename = os.path.sep.join([cache_dir, 'promo-{0:s}-{1:d}.json'.format(name, i)])
		if name in ['handheld-friendly']:
			component_key = 'deals_grid'
		else:
			component_key = 'others_grid'

		# For promos, we have to get the html file or we'll miss out on some promos!
		if i == 0:
			url = '{0:s}/{1:s}/'.format(promo_url, name)
			req = urllib.request.Request(url, headers=working_headers)
		else:
			params = {
				'path': '/promo/{}/'.format(name),
				'component_key': component_key,
				'chunk_index': '{0:d}'.format(i),
			}
			url = api_url + '/fetch_chunk' + '?{}'.format(urllib.parse.urlencode(params))
			req = urllib.request.Request(url, headers=working_headers)

	# If we have a file in cache, return True
	if os.path.isfile(filename):
		return True

	# Here we perform the actual get
	logging.debug('Opening URL {}.'.format(url))
	res = urllib.request.urlopen(req)

	if i == 0 and name not in ['onsale']:
		logging.info('Using TemporaryFile.')
		f = tempfile.TemporaryFile('wb+')
	else:
		logging.info('Writing to {}.'.format(filename))
		f = open(filename, 'wb+')

	if res.headers.get('Content-Encoding') == 'gzip':
		logging.info('Data is gzip compressed.')
		f.write(gzip.decompress(res.read()))
	else:
		logging.info('Data is plain text.')
		f.write(res.read())

	# If it was a promo i == 0 case ...
	if i == 0 and name not in ['onsale']:
		logging.debug('Passing {} through beautiful soup to extract JSON.'.format(filename))
		f.seek(0)
		soup = BeautifulSoup(f, 'html.parser')
		data = soup.find('script', {'id': 'storefront-webpack-json-data'}).text
		f.close()

		# Now lets write the JSON out to a file.
		with open(filename, 'w') as f:
			json.dump(json.loads(data), f)

	f.close()

	return True

def get_max(name):
	if name in ['onsale']:
		filename = os.path.sep.join([cache_dir, '{}-0.json'.format(name)])
		with open(filename) as f:
			data = json.load(f)
		val = data['num_pages']
	else:
		filename = os.path.sep.join([cache_dir, 'promo-{}-0.json'.format(name)])
		with open(filename) as f:
			data = json.load(f)

		try:
			return data['page']['store_components']['deals_grid']['total_chunks']
		except KeyError as e:
			logging.warning('{}. deals_grid not present, trying others_grid.'.format(e))
			# We want to fail hard here if we can't find it.
			val = data['page']['store_components']['others_grid']['total_chunks']

	return val

def get_details(titles):
	"""Meant to get extended details from the games found from the initial JSON data get.

	Args:
		games (list): Grabs details from humblebundle.com if cache is not present.

	Returns:
		Nothing.

"""

	for f in os.listdir(cache_dir):
		filename = os.path.sep.join([cache_dir, f])

	cached = []
	uncached = []

	for i in range(0, len(titles)):
		filename = os.path.sep.join([
			cache_dir,
			'title-{0:s}.json'.format(titles[i])
		])

		if os.path.isfile(filename):
			logging.info('{} details are cached.'.format(titles[i]))
			cached.append(titles[i])
		else:
			logging.info('{} details are not cached.'.format(titles[i]))
			uncached.append(titles[i])

	# We're going to try and get 20 at a time
	i = 1
	success = False
	while len(uncached) > 0:
		# This is actually the meat and potatoes, or well has more data such as
		# reviews and things.
		url = '{0:s}/lookup?products[]={1:s}&request={2:d}'.format(
			api_url,
			'&products[]='.join(map(urllib.parse.quote, uncached[:20])),
			i
		)
		try:
			logging.info('Opening URL {0:s}'.format(url))
			req = urllib.request.Request(url, headers=working_headers)
			with urllib.request.urlopen(req) as res:
				if res.headers.get('Content-Encoding') == 'gzip':
					logging.debug('Data is gzip compressed.')
					json_data = json.loads(gzip.decompress(res.read()))
				else:
					logging.debug('Data is plain text.')
					json_data = json.loads(res.read())

			for j in json_data['result']:
				machine_name = j['machine_name']
				filename = os.path.sep.join([
					cache_dir,
					'title-{0:s}.json'.format(machine_name)
				])
				logging.info('Writing {}.'.format(filename))
				with open(filename, 'w') as f:
					json.dump(j, f)
		except URLError as e:
			logging.error(e)
		except ValueError as e:
			logging.error(e)

		i += 1
		uncached = uncached[20:]

	return

def write_details(titles, hhf_titles=None):
	"""This will sanitize and write out the details to hb-sales.json for happy
		bootstrappy fun. Humble Bundle also has a handheld-friendly section but
		there's no way to know aside from the initial grab. So this will amend
		the data written out."""

	json_return_data = {'total':len(titles), 'rows':[]}

	desc_patt1 = re.compile(r'<[^<]+?>')
	desc_patt2 = re.compile(r'\s\s\s+')

	# sale_end, human_name, current_price, delivery_methods, platforms, user_rating, handheld_friendly
	for title in titles:
		busted = False
		row = {}
		filename = os.path.sep.join([
			cache_dir,
			'title-{}.json'.format(title)
		])

		logging.info('Opening {}.'.format(filename))
		with open(filename) as f:
			try:
				json_data = json.load(f)
			except json.decoder.JSONDecodeError as e:
				logging.error('{} -> {}'.format(e, filename))
				# logging.error(e)

		for k in keys_we_want:
			if k in json_data.keys():
				if k == 'description':
					row[k] = re.sub(
						desc_patt2,
						'\n\n',
						re.sub(
							desc_patt1,
							'',
							json_data[k]
						)
					)
				else:
					row[k] = json_data[k]
			else:
				if k == 'full_price':
					busted = True
					logging.warning('{} has no full_price key for whatever reason. Skipping.'.format(title))
					break
				else:
					row[k] = None

			if row['sale_end'] == None:
				row['onsale'] = 'N'
			else:
				row['onsale'] = 'Y'

		if busted:
			continue

		if hhf_titles:
			if json_data['machine_name'] in hhf_titles:
				row['handheld_friendly'] = 'Y'
			else:
				row['handheld_friendly'] = 'N'

		# Custom columns because I want them
		row['id'] = len(json_return_data['rows'])

		json_return_data['rows'].append(row)

	with open('hb-sales.json', 'w') as f:
		json.dump(json_return_data['rows'], f)

	return True

def clean_cache(force=False):
	"""This cleans out cache files older than 30 days in the cache dir that end in ".json"."""

	for f in os.listdir(cache_dir):
		filename = os.path.sep.join([cache_dir, f])

		if force:
			logging.info('Force option supplied. Deleting {}.'.format(filename))
			os.unlink(filename)
			continue

		tdiff = time.time() - os.path.getmtime(filename)

		if tdiff >= 86400:
			logging.info('{0:s} is at least 24h old. Deleting.'.format(filename))
			try:
				os.unlink(filename)
			except OSError as e:
				logging.error(e)
		else:
			logging.info('{0:s} is not 24h old. Keeping.'.format(filename))

	return True

if __name__ == "__main__":
	# Build cache:
	if not os.path.isdir(cache_dir):
		try:
			os.mkdir(cache_dir)
		except OSError as e:
			logging.error('Unable to create cache dir {0:s}'.format(e))

	# Clear cache
	clean_cache(args.force)

	# Get sales
	if get_data('onsale', 0):
		num_pages = get_max('onsale')

		for i in range(1, num_pages):
			if not get_data('onsale', i):
				logging.error('Failed to get onsale {0:d}.'.format(i))
	else:
		logging.error('Failed to get onsale {0:d}.'.format(i))

	# For promos, the use "chunk_total"
	if get_data('handheld-friendly', 0):
		chunk_total = get_max('handheld-friendly')

		for i in range(1, chunk_total):
			if not get_data('handheld-friendly', i):
				logging.error('Failed to get handheld-friendly {0:d}'.format(i))
	else:
		logging.error('Failed to get handheld-friendly {0:d}'.format(i))

	if args.promo:
		if get_data(args.promo, 0):
			chunk_total = get_max(args.promo)

		for i in range(1, chunk_total):
			if not get_data(args.promo, i):
				logging.error('Failed to get {0:s} {0:d}'.format(args.promo, i))
		else:
			logging.error('Failed to get {0:s} {0:d}'.format(args.promo, i))

	titles = []
	titles.extend(parse_data('onsale'))

	# We want to remember these titles when we generate our super special output
	hhf_titles = parse_data('handheld-friendly')
	titles.extend(hhf_titles)

	if args.promo:
		titles.extend(parse_data(args.promo))

	# We need to remove any dups which is happening for whatever reason
	titles = list(set(titles))
	hhf_titles = list(set(hhf_titles))

	get_details(titles)

	write_details(titles, hhf_titles)

	exitCode = 0

	if exitCode:
		SystemExit(0)
	else:
		SystemExit(2)
