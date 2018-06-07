#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Programmer: Zahid Bukhari
# URL: https://github.com/zbukhari/humblebundle/
# Purpose: To look through sales at the Humble Bundle store

import argparse
from pprint import PrettyPrinter
import urllib2
import json
# import yaml
import sys
from datetime import datetime
import time
import logging
import hashlib
import os.path

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
page_size = 20
# We manipulate this URL to get the data we want.
baseurl = 'https://www.humblebundle.com/store/api'
# List of keys we care for - you should be okay to adjust this.
keys_we_want = [u'sale_end', u'human_name', u'current_price',
	u'delivery_methods', u'platforms', u'user_rating', u'other_links',
	u'developers', u'system_requirements', u'description']
# Some items are "coming soon" (i.e. coming_soon) and we want to filter those out.
# Just run the script and enjoy.
legitimizing_key = u'cta_badge'
cache_dir = 'hb-sales-cache'

# If num_results or num_pages is 0 - we've gone too far - too far I tell you!
# num_results	0
# page_index	6
# request	1
# num_pages	0

### This is where we do magic ###
# def get_page(url, items):
def get_page(url):
	build_cache = True
	filename = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(url).hexdigest())])

	# If the file is less than 1 day old we will use the cache
	try:
		logging.debug('Retrieving mtime for {0:s}'.format(filename))
		age = time.time() - os.path.getmtime(filename)
	except OSError, e:
		logging.warn('Unable to find cache file.  Okay for first run. {0:s}'.format(e))
	else:
		# Within a day
		if age < 86400:
			build_cache = False
		# Older than 10 days
		elif age > 86400 * 10:
			logging.warn('Cache file {0:s} is older than 10 days'.format(filename))
		# Older than 30 days
		elif age > 86400 * 30:
			logging.warn('Cache file {0:s} is older than 30 days - purging.'.format(filename))

	# However if we want to rebuild the cache here we set it to true
	if args.force:
		build_cache = True

	# If this is true then we will use the data response from the URL and build the cache.
	if build_cache:
		# Get a file handle for reading
		try:
			logging.debug('Opening URL {0:s}'.format(url))
			fr = urllib2.urlopen(url)
		except urllib2.URLError, e:
			logging.error(e)
			return False

		# file handle for writing - read in `fr` above and write to `fw`
		try:
			fw = open(filename, 'w')
			fw.write(fr.read())
		except IOError, e:
			logging.warn('Unable to create cache file {0:s}: {1:s}'.format(filename, e))
			return False
		else:
			logging.info('Writing out cache file: {0:s}'.format(filename))
			fr.close()
			fw.close()

	try:
		f = open(filename, 'r')
		jsonData = json.load(f)
	except IOError, e:
		logging.error('Unable to use cache file {0:s}: {1:s}'.format(filename, e))
	except ValueError, e:
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
		jsonData = json.load(f)
	except IOError, e:
		logging.error('Unable to use cache file {0:s}: {1:s}'.format(filename, e))
		return False
	except ValueError, e:
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
			logging.warn('{0:s} [{1:s}] is not available (i.e. coming soon).'.format(unicode(item[u'human_name']).encode('utf-8'), unicode(item[u'machine_name']).encode('utf-8')))
		else:
			logging.info('Adding {0:s} [{1:s}] to list for detail grab.'.format(unicode(item[u'human_name']).encode('utf-8'), unicode(item[u'machine_name']).encode('utf-8')))
			saleList.append(item[u'machine_name'])

	# Now we have a legitimate list of items from the file, lets make a list we need to perform a lookup for.
	detailList = []
	lookupList = []
	for machine_name in saleList:
		gameFile = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(machine_name).hexdigest())])
		if os.path.isfile(gameFile):
			try:
				age = time.time() - os.path.getmtime(gameFile)
			except OSError, e:
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
				except IOError, e:
					logging.error('Unable to open cache file for {0:s} (i.e. {1:s}).  {2:s}.'.format(unicode(machine_name).encode('utf-8'), gameFile, e))
		else:
			lookupList.append(machine_name)

	# This is actually the meat and potatoes, or well has more data such as reviews and things.
	url = '{0:s}/lookup?products[]={1:s}&request=1'.format(baseurl, '&products[]='.join(map(urllib2.quote, lookupList)))

	try:
		logging.debug('Opening URL {0:s}'.format(url))
		f = urllib2.urlopen(url)
		jsonData = json.load(f)
		f.close()
	except urllib2.URLError, e:
		logging.error(e)
	except ValueError, e:
		logging.error(e)

	# Here we add the data to the list and create a cache file for the game.
        for item in jsonData[u'result']:
		gameFile = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(item[u'machine_name']).hexdigest())])
		try:
			detailList.append(item)
			logging.debug('Attempting to create cache file for {0:s} (i.e. {1:s}).'.format(item[u'machine_name'], gameFile))
			f = open(gameFile, 'w')
			f.write(json.dumps(item))
			f.close()
		except IOError, e:
			logging.warn('Unable to create cache file for {0:s} (i.e. {1:s}).  {2:s}'.format(item[u'machine_name'], gameFile, e))

	# Now what do we do with the data???
	# Return it - parse it below.
	return detailList

def writeDetails(detailList):
	"""This will sanitize and write out the details to hb-sales.json for happy bootstrappy fun"""

	# We can't use for to pass by reference but boss mode activate!
	for i in range(len(detailList)):
		# items[item[u'machine_name']] = {}
		# for key in keys_we_want:
		# 	if item.has_key(key):
		# 		items[item[u'machine_name']][key] = item[key]

		# Simple manipulations
		detailList[i][u'current_price'] = ' '.join(map(str, detailList[i][u'current_price']))
		detailList[i][u'delivery_methods'] = ', '.join(detailList[i][u'delivery_methods'])
		detailList[i][u'platforms'] = ', '.join(detailList[i][u'platforms'])
		if detailList[i].has_key(u'user_rating'):
			detailList[i][u'user_rating'] = '''{steam_percent}% | {review_text}'''.format(**detailList[i][u'user_rating'])

		# News to me - some sale items don't have a sale_end.
		if (detailList[i][u'sale_end'] - time.time()) > 864000:
			detailList[i][u'sale_end'] = 'More than 10 days'
		else:
			detailList[i][u'sale_end'] = datetime.isoformat(datetime.fromtimestamp(detailList[i][u'sale_end']))

	try:
		f = open('hb-sales.json', 'w')
		f.write(json.dumps(detailList, indent=4))
		f.close()
	except IOError, e:
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
		except OSError, e:
			logging.error('Unable to unlink {0:s}: {1:s}'.format(filename, e))
		else:
			logging.info('Unlinked {0:s}'.format(filename))

if __name__ == "__main__":
	# Build cache:
	if not os.path.isdir(cache_dir):
		try:
			os.mkdir(cache_dir)
		except OSError, e:
			logging.error('Unable to create cache dir {0:s}'.format(e))

	# We'll emulate a do while loop of sorts.  We'll reset pages after our first page.
	i = 0
	daData = []

	while True:
		if args.other:
			url = '{0:s}/fetch_chunk?path=%2Fpromo%2F{1:s}%2F&component_key=others_grid&chunk_index={2:d}'.format(baseurl, urllib2.quote(args.other, safe=''), i)
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
