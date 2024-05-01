#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Programmer: Zahid Bukhari
# URL: https://github.com/zbukhari/humblebundle/
# Purpose: To look through sales at the Humble Bundle store

# Adding changes needed for python3
import argparse
from pprint import PrettyPrinter
import urllib
import urllib.request
from urllib.error import URLError
import json
# import yaml
import sys
from datetime import datetime
import time
import logging
import hashlib
import os.path

# This is good but I need more TLC as now responses are gzip encoded
import gzip
# from StringIO import StringIO
from io import StringIO

# This is needed because of how promos are really done
from bs4 import BeautifulSoup

# Logging configuration
logging.basicConfig(filename='hb-sales.log',level=logging.DEBUG, format='%(asctime)s %(levelname)s %(funcName)s %(message)s')

# Debuggy helper
pp = PrettyPrinter(indent=2)

### Options! ###
parser = argparse.ArgumentParser(description='Parse Humble Bundle sales.')
parser.add_argument('--force', '-f', dest='force', action='store_true', default=False,
	help='Ignore the cache file and rebuild it.')
parser.add_argument('--cost', '-c', dest='cost', type=int, default=False,
	help='Display items that cost less than x, where x is a positive integer.')
parser.add_argument('--platform', '-p', dest='platform', default=False,
	help='Display items that run on the specified platform(s).  Where platforms is a comma separated list (i.e. windows,mac,linux)')
parser.add_argument('--date', '-d', dest='date', default=False, action='store_true',
	help='Display items that will end by 24 hours.')
parser.add_argument('--other', '-o', dest='other', default=False, type=str,
	help='Show another promo.  For example for https://www.humblebundle.com/store/promo/ubisoft-sale/')

args = parser.parse_args()

### Important variables ###
# This seems to be the max - we can go lower but this is what I've found.
# This doesn't seem to be used as much. 20 is the default, so one can request less but.
# https://www.humblebundle.com/store/api/search?sort=bestselling&filter=onsale&request=1&page=0
page_size = 20
# We manipulate this URL to get the data we want.
baseurl = 'https://www.humblebundle.com/store/api'
# https://www.humblebundle.com/store/api/search?sort=bestselling&filter=onsale&page=1&request=1
# List of keys we care for - you should be okay to adjust this.
keys_we_want = [u'sale_end', u'human_name', u'current_price',
	u'delivery_methods', u'platforms', u'user_rating', u'other_links',
	u'developers', u'system_requirements', u'description']
# Some items are "coming soon" (i.e. coming_soon) and we want to filter those out.
# Just run the script and enjoy.
legitimizing_key = u'cta_badge'
cache_dir = 'cache'

# If num_results or num_pages is 0 - we've gone too far - too far I tell you!
# num_results	0
# page_index	6
# request	1
# num_pages	0

### This is where we do magic ###
def get_pages(promo = None):
	# promos are going to require more work.
	i = 0

	if promo:
		promo = promo.lower().replace(' ', '-')

		filename = os.path.sep.join([cache_dir, 'promo-{0:s}-{1:d}.json'.format(promo, i)])

		if i == 0:
			# Let's format the request
			url = 'https://www.humblebundle.com/store/promo/{0:s}/'.format(promo)

			req = urllib.request.Request(url, headers = {
				'Accept-Encoding': 'gzip, deflate, br',
				'Upgrade-Insecure-Requests': '1',
				'User-Agent': 'Mozilla'
			})

			soup = BeautifulSoup(response, 'html.parser')
			f = open(filename, 'w')
			f.write(soup.find('script', {'id': 'storefront-webpack-json-data'}).text)
		else:
			url = baseurl + '/fetch_chunk'

			req = urllib.request.Request(url,
				data = {
					'path': urllib.parse.urlencode('''/promo/{0:s}/'''.format(promo)),
					'component_key': 'others_grid',
					'chunk_index': '{0:d}'.format(i)
				},
				headers = {
					'Accept-Encoding': 'gzip, deflate, br',
					'Upgrade-Insecure-Requests': '1',
					'User-Agent': 'Mozilla'
				}
			)

		i += 1
	else:
		if i == 0:

		filename = os.path.sep.join([cache_dir, 'onsale-{0:d}.json'.format(i)])

		# Let's format the request
		url = baseurl + '/search'
		req = urllib.request.Request(url,
				data = {
					'sort': 'bestselling',
					'filter': 'onsale',
					'page': '0',
					'request': '1'
				},
				headers = {
					'Accept-Encoding': 'gzip, deflate, br',
					'Upgrade-Insecure-Requests': '1',
					'User-Agent': 'Mozilla'
				}
		)

	build_cache = True
	print(req)

	# If the file is less than 1 day old we will use the cache
	try:
		logging.debug('Retrieving mtime for {0:s}'.format(filename))
		age = time.time() - os.path.getmtime(filename)
	except OSError as e:
		# logging.warning('Unable to find cache file.  Okay for first run. {0:s}'.format(e))
		logging.warning('Unable to find cache file.  Okay for first run. {0:s}'.format(filename))
		logging.warning(e)
	else:
		# Within a day
		if age < 86400:
			build_cache = False
		# Older than 10 days
		elif age > 86400 * 10:
			logging.warning('Cache file {0:s} is older than 10 days'.format(filename))
		# Older than 30 days
		elif age > 86400 * 30:
			logging.warning('Cache file {0:s} is older than 30 days - purging.'.format(filename))

	# However if we want to rebuild the cache here we set it to true
	if args.force:
		build_cache = True

	# If this is true then we will use the data response from the URL and build the cache.
	if build_cache:
		# Get a file handle for reading
		try:
			logging.debug('Opening URL {0:s}'.format(url))
			req = urllib.request.Request(url,
				# urllib.parse.urlencode({'spam': 1, 'eggs': 2, 'bacon': 0})
				headers = {
					# 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
					'Accept-Encoding' : 'gzip, deflate, br',
					# 'Accept-Language' : 'en-US,en;q=0.5',
					# 'Connection' : 'keep-alive',
					# 'DNT' : '1',
					# 'Host' : 'www.humblebundle.com',
					# 'Sec-Fetch-Dest' : 'document',
					# 'Sec-Fetch-Mode' : 'navigate',
					# 'Sec-Fetch-Site' : 'cross-site',
					# 'Sec-GPC' : '1',
					# 'TE' : 'trailers',
					'Upgrade-Insecure-Requests' : '1',
					'User-Agent' : 'Mozilla'
					# 'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
				})
			fr = urllib.request.urlopen(req)
			# print(fr.headers)
			# print(fr.headers.get('Content-Encoding'))
			# gzip.decompress
		except URLError as e:
			logging.error(e)
			return False

		# file handle for writing - read in `fr` above and write to `fw`
		try:
			fw = open(filename, 'wb')
			logging.info('Attempting to write to {}'.format(filename))
			if fr.headers.get('Content-Encoding') == 'gzip':
				fw.write(gzip.decompress(fr.read()))
			else:
				fw.write(fr.read())
		except IOError as e:
			logging.warning('Unable to create cache file {0:s}: {1:s}'.format(filename, e))
			return False
		else:
			logging.info('Writing out cache file: {0:s}'.format(filename))
			fr.close()
			fw.close()

	try:
		f = open(filename, 'r')
		jsonData = json.load(f)
	except IOError as e:
		logging.error('Unable to use cache file {0:s}: {1:s}'.format(filename, e))
	except ValueError as e:
		logging.error(e)
	else:
		f.close()

	# Test object
	if jsonData[u'num_results'] == 0 or jsonData[u'num_pages'] == 0:
		return False
	else:
		return filename

def getDetails(filename):
	"""Meant to get details from the initial JSON data get.

	Args:
		filename (str): Reads the supplied file for JSON data to use to attain details

	Returns:
		List of games or files - haven't decided - to further parse.

"""

	try:
		f = open(filename, 'r')
		# sio_fh = StringIO(gzip_fh.read())
		# f = gzip.GzipFile(fileobj=sio_fh)
		jsonData = json.load(f)
		# sio_fh.close()
		# gzip_fh_close()
	except IOError as e:
		logging.error('Unable to use cache file {0:s}: {1:s}'.format(filename, e))
		return False
	except ValueError as e:
		logging.error(e)
		return False
	else:
		f.close()

	# Promo sales have a different base and we have a different way of determining the last page.
	if args.other:
		base = jsonData[u'result'][u'entity_keys']
	else:
		base = jsonData[u'results']

	# I'm going to leave the promo code here but it actually doesn't need to exist unless someone
	# only wants to see what's on sale for the promo.  The normal sale page shows all sale items.

	# Good place to create temp key for *other* lookup
	saleList = []
	for item in base:
		# If we are using "other" then we actually want to redefine item.
		if args.other:
			entity_key = item
			item = jsonData[u'result'][u'entity_lookup_dict'][entity_key]

		if item[legitimizing_key] == u'coming_soon':
			logging.warning('{0:s} [{1:s}] is not available (i.e. coming soon).'.format(
				item[u'human_name'],
				item[u'machine_name']
			))
		else:
			logging.info('Adding {0:s} [{1:s}] to list for detail grab.'.format(
				item[u'human_name'],
				item[u'machine_name']
			))
			saleList.append(item[u'machine_name'])

	# Now we have a legitimate list of items from the file, lets make a list we need to perform a lookup for.
	detailList = []
	lookupList = []
	for machine_name in saleList:
		# gameFile = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(url.encode('utf-8')).hexdigest())])
		gameFile = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(machine_name.encode('utf-8')).hexdigest())])
		if os.path.isfile(gameFile):
			try:
				age = time.time() - os.path.getmtime(gameFile)
			except OSError as e:
				logging.info('''Unable to retrieve mtime for {0:s}'s cache file (i.e. {1:s})'''.format(machine_name, gameFile))

			# Get mtime and if legit pop from stack
			if age > 86400 or args.force:
				# saleList.pop(saleList.index(machine_name)) # Returns value so ... lessee other options
				lookupList.append(machine_name)
			# Let's get the data from cache!  Like a boss!
			else:
				try:
					logging.debug('Attempting to open cache file for {0:s} (i.e. {1:s}).'.format(unicode(machine_name).encode('utf-8'), gameFile))
					f = open(gameFile, 'r')
					detailList.append(json.load(f))
					f.close()
				except IOError as e:
					logging.error('Unable to open cache file for {0:s} (i.e. {1:s}).  {2:s}.'.format(unicode(machine_name).encode('utf-8'), gameFile, e))
		else:
			lookupList.append(machine_name)

	# This is actually the meat and potatoes, or well has more data such as reviews and things.
	url = '{0:s}/lookup?products[]={1:s}&request=1'.format(baseurl, '&products[]='.join(map(urllib.parse.quote, lookupList)))

	try:
		logging.debug('Opening URL {0:s}'.format(url))
		req = urllib.request.Request(url,
			headers = {
				'Upgrade-Insecure-Requests' : '1',
				'User-Agent' : 'Mozilla',
				'Accept-Encoding' : 'gzip, deflate, br'
			})
		f = urllib.request.urlopen(req)
		jsonData = json.load(f)
		f.close()
	except URLError as e:
		logging.error(e)
	except ValueError as e:
		logging.error(e)

	# Here we add the data to the list and create a cache file for the game.
	# print(jsonData.keys())
	for item in jsonData[u'results']:
		gameFile = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(item[u'machine_name'].encode('utf-8')).hexdigest())])
		try:
			detailList.append(item)
			logging.debug('Attempting to create cache file for {0:s} (i.e. {1:s}).'.format(item[u'machine_name'], gameFile))
			f = open(gameFile, 'w')
			f.write(json.dumps(item))
			f.close()
		except IOError as e:
			logging.warning('Unable to create cache file for {0:s} (i.e. {1:s}).  {2:s}'.format(item[u'machine_name'], gameFile, e))

	# Now what do we do with the data???
	# Return it - parse it below.
	return detailList

def writeDetails(detailList):
	"""This will sanitize and write out the details to hb-sales.json for happy bootstrappy fun"""

	jsonData = {'total':len(detailList), 'rows':[]}
	# We can't use for to pass by reference but boss mode activate!
	for i in range(len(detailList)):
		# items[item[u'machine_name']] = {}
		# for key in keys_we_want:
		# 	if item.has_key(key):
		# 		items[item[u'machine_name']][key] = item[key]

		# Creating an ID field
		detailList[i][u'id'] = i
		# Simple manipulations
		### We're going to process these via JavaScript
		# detailList[i][u'delivery_methods'] = ', '.join(detailList[i][u'delivery_methods'])
		# detailList[i][u'platforms'] = ', '.join(detailList[i][u'platforms'])
		# detailList[i][u'current_price'] = ' '.join(map(str, detailList[i][u'current_price']))

		if not detailList[i].has_key(u'user_rating'):
			detailList[i][u'user_rating'] = None
		# 	detailList[i][u'user_rating'] = '''{steam_percent}% | {review_text}'''.format(**detailList[i][u'user_rating'])
		# else:

		# News to me - some sale items don't have a sale_end.
		# if (detailList[i][u'sale_end'] - time.time()) > 864000:
		# 	detailList[i][u'sale_end'] = 'More than 10 days'
		# else:
		# 	detailList[i][u'sale_end'] = datetime.isoformat(datetime.fromtimestamp(detailList[i][u'sale_end']))

		jsonData['rows'].append(detailList[i])

	try:
		f = open('hb-sales-json.js', 'wb')
		f.write(b'var rawJsonData = ')
		# f.write(json.dumps(jsonData['rows'], indent=4))
		f.write(bytes(json.dumps(jsonData, indent=4).encode('utf-8')))
		f.write(b''';\nvar jsonData = rawJsonData['rows'];\n''')
		f.close()
	except IOError as e:
		logging.error('Unable to write hb-sales.json file.  {0:s}.'.format(e))
		return False
	else:
		return True

### Clean cache
def clean_cache():
	"""This cleans out cache files older than 30 days in the cache dir that end in ".json"."""

	fileList = map(lambda f: os.path.sep.join([cache_dir, f]), filter(lambda f: f.endswith('.json'), filter(lambda f: (time.time() - os.path.getmtime(f)) > 86400 * 30, os.listdir(cache_dir))))

	for f in fileList:
		filename = os.path.sep.join([cache_dir, f])

		try:
			os.unlink(filename)
		except OSError as e:
			logging.error('Unable to unlink {0:s}: {1:s}'.format(filename, e))
		else:
			logging.info('Unlinked {0:s}'.format(filename))

if __name__ == "__main__":
	# Build cache:
	if not os.path.isdir(cache_dir):
		try:
			os.mkdir(cache_dir)
		except OSError as e:
			logging.error('Unable to create cache dir {0:s}'.format(e))

	# We'll emulate a do while loop of sorts.  We'll reset pages after our first page.
	i = 0
	daData = []

	while True:
		if args.other:
			url = '{0:s}/fetch_chunk?path=%2Fpromo%2F{1:s}%2F&component_key=others_grid&chunk_index={2:d}'.format(baseurl, urllib.parse.quote(args.other, safe=''), i)
		else:
			url = '{0:s}/search?sort=discount&filter=onsale&request=1&page_size={1:d}&page={2:d}'.format(baseurl, page_size, i)

		filename = get_page(url)
		if filename:
			daData.extend(getDetails(filename))
			i += 1
		else:
			break

	exitCode = writeDetails(daData)

	if exitCode:
		SystemExit(0)
	else:
		SystemExit(2)
# Request headers (FF):
#
# Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
# Accept-Encoding: gzip, deflate, br
# Accept-Language: en-US,en;q=0.5
# Connection: keep-alive
# DNT: 1
# Host: www.humblebundle.com
# Sec-Fetch-Dest: document
# Sec-Fetch-Mode: navigate
# Sec-Fetch-Site: cross-site
# Sec-GPC: 1
# TE: trailers
# Upgrade-Insecure-Requests: 1
# User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0

# Response headers:
#
# date: Sun, 21 Apr 2024 20:04:34 GMT
# content-type: application/json
# content-length: 4758
# cf-ray: 877ffbe3980ee100-ORD
# cf-cache-status: DYNAMIC
# cache-control: private
# content-encoding: gzip
# expires: Sun, 21 Apr 2024 20:04:34 GMT
# set-cookie: _simpleauth_sess=eyJpZCI6IkVEeUlDQmJOcE0ifQ==|1713729874|1261f1aee74fc999db690540cdbe46c14111f0ed; Domain=.humblebundle.com; Expires=Sat, 20-Jul-2024 20:04:34 GMT; Secure; HttpOnly; Path=/; SameSite=None
# vary: Cookie, Accept-Encoding
# x-cloud-trace-context: 8ae655637286035c42f33d56a7c6a1df
# set-cookie: __cf_bm=zCkgSdt10MIct6GTVLBSvQma3jfP4WxJh9P9enDXZFE-1713729874-1.0.1.1-X1PTHDFvCoMVdjpDZq9WUHFjDhIqrB2EEXvQHlbxZHzW5Wpz0ey5kGY4ISvAni4BWL3Zr1TvZKhgVfejJl4UYw; path=/; expires=Sun, 21-Apr-24 20:34:34 GMT; domain=.humblebundle.com; HttpOnly; Secure; SameSite=None
# server: cloudflare

