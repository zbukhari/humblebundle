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
cache_dir = 'hb-sales-cache'

### This is where we do magic ###
def get_page(url, items):
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
		try:
			logging.debug('Opening URL {0:s}'.format(url))
			f = urllib2.urlopen(url)
			jsonData = json.load(f)
			f.close()
		except urllib2.URLError, e:
			logging.error(e)
			return 0
		except ValueError, e:
			logging.error(e)
			return 0

		# Build cache:
		if not os.path.isdir(cache_dir):
			try:
				os.mkdir(cache_dir)
			except OSError, e:
				logging.warn('Unable to create cache dir {0:s}'.format(e))

		try:
			f = open(filename, 'w')
		except IOError, e:
			logging.warn('Unable to create cache file {0:s}: {1:s}'.format(filename, e))
		else:
			f.write(json.dumps(jsonData, indent=2))
			f.close()
	# else we will just use the cache
	else:
		try:
			f = open(filename, 'r')
			jsonData = json.load(f)
			f.close()
		except IOError, e:
			logging.error('Unable to use cache file {0:s}: {1:s}'.format(filename, e))
		except ValueError, e:
			logging.error(e)

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

		saleList.append(item[u'machine_name'])

	# This is actually the meat and potatoes, or well has more data such as reviews and things.
	url = '{0:s}/lookup?products[]={1:s}&request=1'.format(baseurl, '&products[]='.join(map(urllib2.quote, saleList)))

	filename = os.path.sep.join([cache_dir, '{0:s}.json'.format(hashlib.md5(url).hexdigest())])

	try:
		logging.debug('Retrieving mtime for {0:s}'.format(filename))
		age = time.time() - os.path.getmtime(filename)
	except OSError, e:
		logging.warn('Unable to find cache file.  Okay for first run. {0:s}'.format(e))
		# We need to set build_cache to true here as well - make no assumptions
		build_cache = True
	else:
		if age < 86400:
			build_cache = False

	# However if we want to rebuild the cache here we set it to true
	if args.force:
		build_cache = True

	if build_cache:
		try:
			logging.debug('Opening URL {0:s}'.format(url))
			f = urllib2.urlopen(url)
			jsonData2 = json.load(f)
			f.close()
		except urllib2.URLError, e:
			logging.error(e)
		except ValueError, e:
			logging.error(e)

		try:
			f = open(filename, 'w')
		except IOError, e:
			logging.warn('Unable to create cache file {0:s}: {1:s}'.format(filename, e))
		else:
			f.write(json.dumps(jsonData2, indent=2))
			f.close()
	# else we will just use the cache
	else:
		try:
			f = open(filename, 'r')
			jsonData2 = json.load(f)
			f.close()
		except IOError, e:
			logging.error('Unable to use cache file {0:s}: {1:s}'.format(filename, e))
		except ValueError, e:
			logging.error(e)

        for item in jsonData2[u'result']:
		if items.has_key(item[u'machine_name']):
			# So - I kept running into UTF-8 issues here but found %s done like this vs format works.
			# I couldn't find a definitive answer and so am leaving it this way - if anyone cares to
			# enlighten me - please do.
			logging.warn('Duplicate key: %s' % item[u'machine_name'])
			continue

		items[item[u'machine_name']] = {}
		for key in keys_we_want:
			if item.has_key(key):
				items[item[u'machine_name']][key] = item[key]

		# News to me - some sale items don't have a sale_end.
		if item.has_key(u'sale_end'):
			if (item[u'sale_end'] - time.time()) > 864000:
				items[item[u'machine_name']][u'human_sale_end'] = 'More than 10 days'
			else:
				items[item[u'machine_name']][u'human_sale_end'] = datetime.isoformat(datetime.fromtimestamp(item[u'sale_end']))
		else:
			logging.warn('''{0} / {1} has no 'sale_end'.'''.format(item[u'human_name'], item[u'machine_name']))
			items[ item[u'machine_name'] ][u'human_sale_end'] = 'No sale end date.'
			items[ item[u'machine_name'] ][u'sale_end'] = 0xffffffff

		# More news to me - some sale items don't have a price.
		if not item.has_key(u'current_price'):
			logging.warn('''{0} / {1} has no 'current_price'.'''.format(item[u'human_name'], item[u'machine_name']))

			# Maybe it's listed on sale but is only available at full price
			if item.has_key(u'full_price'):
				logging.warn('''{0} / {1} has no 'current_price' but has a 'full_price'.  Using 'full_price' as 'current_price'.'''.format(item[u'human_name'], item[u'machine_name']))
				items[ item[u'machine_name'] ][u'current_price'] = item[u'full_price']
			else:
				logging.warn('''{0} / {1} has no 'current_price' or 'full_price'.'''.format(item[u'human_name'], item[u'machine_name']))
				items[ item[u'machine_name'] ][u'current_price'] = [ 0.00, 'USD' ]

	# This was done to force a full pull down or something
	if args.other:
		return 0xffffffffffffffff
	else:
		return jsonData[u'num_pages']

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

# We'll emulate a do while loop of sorts.  We'll reset pages after our first page.
i = 0
pages = 1
items = {}

while i < pages:
	# The numbering of pages is such that if the page equals or goes past numpages - we've gone too far.
	if i >= pages:
		break

	if args.other:
		url = '{0:s}/fetch_chunk?path=%2Fpromo%2F{1:s}%2F&component_key=others_grid&chunk_index={2:d}'.format(baseurl, urllib2.quote(args.other, safe=''), i)
	else:
		url = '{0:s}/search?sort=discount&filter=onsale&request=1&page_size={1:d}&page={2:d}'.format(baseurl, page_size, i)
	pages = get_page(url, items)
	i += 1

# Alright - let's sort it and print it
# sorted_dict = sorted(items.iteritems(), key=lambda (k,v): v['sale_end'])
sorted_keys = map(lambda f: f[0], sorted(items.iteritems(), key=lambda (k,v): v['sale_end']))

for i in sorted_keys:
	### Filter ###
	# By cost
	if args.cost:
		if items[i]['current_price'][0] > args.cost:
			continue

	# By platform
	if args.platform:
		# If j is still 0 we won't print.
		j = 0
		for p in args.platform.lower().split(','):
			try:
				z = items[i]['platforms'].index(p)
			except ValueError, e:
				logging.debug('Unable to find platform {0:s}'.format(e))
			else:
				j += 1

		if j == 0:
			continue

	# By date
	if args.date:
		if (items[i][u'sale_end'] - time.time()) > 86400:
			continue

	# https://www.humblebundle.com/store/api/lookup?products[]=lastdayofjune_storefront&products[]=monsterlovesyou_storefront&request=1

	print 'Title: {0}'.format(items[i]['human_name'].encode('utf-8'))

	for k, v in items[i].iteritems():
		# May want to figure out how to make this pretty in console view but we have human_sale_end.
		if k in ['system_requirements','description', 'sale_end']:
			continue

		# Special objects.
		if k == 'other_links': # List of dictionaries
			print '\tOther links:'
			for tmpDict in v:
				# In more news ... apparently other links can exist and not have details ... well I'll be.
				# Traceback (most recent call last):
				#  File "./hb-sales.py", line 301, in <module>
				#    print '\t\t{0} : {1}'.format(unicode(tmpDict[u'other-link-title']).encode('utf-8'), unicode(tmpDict[u'other-link']).encode('utf-8'))
				#KeyError: u'other-link-title'
				if tmpDict.has_key(u'other-link-title'):
					print '\t\t{0} : {1}'.format(unicode(tmpDict[u'other-link-title']).encode('utf-8'), unicode(tmpDict[u'other-link']).encode('utf-8'))
				else:
					print logging.warn('{0} has other_links but not other-link-title. Follow keys {1} - may pprint.'.format(items[i]['human_name'].encode('utf-8'), tmpDict.keys()))

				# for (sub_k, sub_v) in tmpDict.iteritems():
				# 	print '\t\t{0} : {1}'.format(unicode(sub_k).encode('utf-8'), unicode(sub_v).encode('utf-8'))
	
			continue

		if k == 'developers': # List of dictionaries - but more useless than other_links - ugh!
			print '\tDevelopers'
			for tmpDict in v:
				# print '\t\t{0} : {1}'.format(unicode(tmpDict[u'developer-name']).encode('utf-8'), unicode(tmpDict[u'developer-url']).encode('utf-8'))
				for (sub_k, sub_v) in tmpDict.iteritems():
					print '\t\t{0} : {1}'.format(unicode(sub_k).encode('utf-8'), unicode(sub_v).encode('utf-8'))

			continue

		# try-catch useful here - I think this needs recursion but ... we will see.
		if type(v) == type([]) or type(v) == type(()):
			print '\t{0} : {1}'.format(k, ', '.join(map(unicode, v)).encode('utf-8'))
		elif type(v) == type({}):
			print '\t{0:s} :'.format(k)
			for (sub_k, sub_v) in v.iteritems():
				print '\t\t{0} : {1}'.format(sub_k, unicode(sub_v).encode('utf-8'))
		else:
			print '\t{0} : {1}'.format(k, v.encode('utf-8'))
		# I suspect I'll be missing something here but meh :-)


### output ###
## url = 'https://www.humblebundle.com/store/api/search?sort=discount&filter=onsale&request=1&page_size=20' ##
## url: https://www.humblebundle.com/store/api/lookup?products[]=lastdayofjune_storefront&products[]=monsterlovesyou_storefront&request=1

## Special promo URLs
## curl 'https://www.humblebundle.com/store/api/fetch_chunk?path=%2Fpromo%2Fbandai-namco-anime-sale%2F&component_key=others_grid&chunk_index=1' -H 'Host: www.humblebundle.com' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:58.0) Gecko/20100101 Firefox/58.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Referer: https://www.humblebundle.com/store/promo/bandai-namco-anime-sale/' -H 'X-Requested-With: XMLHttpRequest' -H 'Cookie: csrf_cookie=KGOmCYwfy40AVtia-1-1507937636; _simpleauth_sess="eyJ1c2VyX2lkIjo0NjgyMzg3NTU1NDgzNjQ4LCJpZCI6IklRVXl6ZGlWNWEiLCJyZWZlcnJlcl9jb2RlIjoiIiwiYXV0aF90aW1lIjoxNTEyNDc5ODg3fQ\075\075|1515622547|fbaf9f77ddb1f616e065adb4c992b8f8c67b16c5"; _ga=GA1.2.81153090.1507937649; pnctest=1; __ssid=b43637c5-4853-4591-8b0e-97d6a04bec98; hbguard="1xzceOOeZZ7uikjdDpmEaVvaB88+spqSuDGoUwxbinY\075"; session-set=true; hb_f946d4f040be03979f676c3e21bc2e34796d3281=1; hb_age_check=29; amazon-pay-abtesting-new-widgets=false; hmb_source=humble_home; hmb_campaign=mosaic_section_1_layout_index_1_layout_type_twos_tile_index_2; hmb_medium=product_tile' -H 'DNT: 1' -H 'Connection: keep-alive'

# Ubisoft sale
# curl 'https://www.humblebundle.com/store/api/fetch_chunk?path=%2Fpromo%2Fubisoft-sale%2F&component_key=others_grid&chunk_index=1' -H 'Host: www.humblebundle.com' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:58.0) Gecko/20100101 Firefox/58.0' -H 'Accept: application/json, text/javascript, */*; q=0.01' -H 'Accept-Language: en-US,en;q=0.5' --compressed -H 'Referer: https://www.humblebundle.com/store/promo/ubisoft-sale/' -H 'X-Requested-With: XMLHttpRequest' -H 'Cookie: csrf_cookie=KGOmCYwfy40AVtia-1-1507937636; _simpleauth_sess="eyJ1c2VyX2lkIjo0NjgyMzg3NTU1NDgzNjQ4LCJpZCI6IklRVXl6ZGlWNWEiLCJyZWZlcnJlcl9jb2RlIjoiIiwiYXV0aF90aW1lIjoxNTEyNDc5ODg3fQ\075\075|1515622547|fbaf9f77ddb1f616e065adb4c992b8f8c67b16c5"; _ga=GA1.2.81153090.1507937649; pnctest=1; __ssid=b43637c5-4853-4591-8b0e-97d6a04bec98; hbguard="1xzceOOeZZ7uikjdDpmEaVvaB88+spqSuDGoUwxbinY\075"; session-set=true; hb_f946d4f040be03979f676c3e21bc2e34796d3281=1; hb_age_check=29; hmb_source=humble_home; hmb_campaign=mosaic_section_3_layout_index_7_layout_type_fours_tile_index_2; hmb_medium=product_tile; amazon-pay-abtesting-new-widgets=false' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Pragma: no-cache' -H 'Cache-Control: no-cache'
