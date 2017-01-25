#!/usr/bin/python
from __future__ import print_function
import os
import linecache
import dateutil.parser
from staticmap.staticmap.staticmap import StaticMap, CircleMarker, Polygon
import sys
import imageio
import csv
from StringIO import StringIO
__author__ = 'Max von Hippel'
from images2gif import writeGif
from PIL import Image, ImageSequence
from datetime import datetime, timedelta

# http://stackoverflow.com/a/20264059/1586231
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

# to hold all our days
days = {}

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def add_node(x, y, timestamp):
	# add the node
	if not timestamp in days:
		days[timestamp] = {}
		days[timestamp]['nodes'] = []
		days[timestamp]['ways'] = []
	days[timestamp]['nodes'].append([x,y])

def add_way(members, timestamp):
	coords = [[member.location.lon, member.location.lat] for member in members]
	if not timestamp in days:
		days[timestamp] = {}
		days[timestamp]['nodes'] = []
		days[timestamp]['ways'] = []
	days[timestamp]['ways'].append(coords)

def append_day_to_map(_map, day):
	if day in days.keys():
		# add the nodes
		for node in days[day]['nodes']:
			marker = CircleMarker([int(float(node[0])), int(float(node[1]))], '#ff0000', 4)
			_map.add_marker(marker)
		# add the ways
		for way in days[day]['ways']:
			poly = Polygon([[int(float(node[0])), int(float(node[1]))] for node in coords], '#ff0000', '#ff0000', True)
			_map.add_polygon(poly)
	else:
		print("empty map")
		# get the empty image of average location for this list
		# set it to be the "open_image"

def render_day(single_date, width, height, zoom, cumulative, youngest):
	day = single_date.strftime("%Y-%m-%d")
	print("day: ", day)
	# make the map
	_map = StaticMap(int(float(width)), int(float(height)), url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')
	_map.set_extent(83.676659, 28.220671, 83.804604, 28.409901)
	append_day_to_map(_map, single_date)
	# if cumulative, add all prior stuff to the map
	if cumulative == True:
		for prior_date in daterange(youngest, single_date):
			append_day_to_map(_map, prior_date)
	# render
	_img = _map.render(zoom=zoom)
	# save
	_name = str(day) + ".png"
	_img.save(_name)


def render_video(width, height, zoom, cumulative):
	# iff sigma == True, each frame contains all previous frames' stuff
	# otherwise only stuff from that specific day
	try:
		# http://stackoverflow.com/a/35943809/1586231
		sequence = []
		# what is the earliest and last day in the list?
		alldays = []
		for stamp in days.keys():
			try:
				alldays.append(datetime.strptime(stamp, '%Y-%m-%d'))
			except:
				pass
		youngest = min(alldays)
		eldest = max(alldays)
		# now iterate
		print("keys: ", days.keys())
		empty_name = ""
		for single_date in daterange(youngest, eldest):
			render_day(single_date, width, height, zoom, cumulative, youngest)
		print("all done!")
	
	except:
		PrintException()

# for OSM (.osm, .osh, .pbf) files
def read_osm(file, width, height, zoom, cumulative):
	try:
		# imports
		import osmium

		# class to parse the nodes, relations, and ways
		class CounterHandler(osmium.SimpleHandler):
			# the init variables of the Counter Handler
		    def __init__(self):
		    	osmium.SimpleHandler.__init__(self)

		    def node(self, n):
		    	# handle a node
		    	add_node(n.location.lon, n.location.lat, n.timestamp)

		    def way(self, w):
		    	# handle a way
		    	add_way(w.nodes, w.timestamp)

		# instantiate one    	
		map_handler = CounterHandler()
		map_handler.apply_file(file)

		# render video
		render_video(sigma, width, height, zoom, cumulative)
	except:
		PrintException()

# for .csv files
# format: id,longitude,latitude,"{[Name:timestamp], ... }"
def read_csv(file, width, height, zoom, cumulative):
	parsd = 0
	mapd = 0
	try:
		with open(file, 'rb') as csvfile:
			reader = csv.reader(csvfile)
			for row in reader:
				lon = row[1]
				lat = row[2]
				versions = csv.reader(str(row[3][1:-1]))
				for row in versions:
					subrow = str(row)[3:-3].split(",")
					if len(subrow) == 2:
						stamp = subrow[1]
						parsd += 1
						if parsd % 1000000 == 0:
							print("num nodes parsed: ", parsd)
						add_node(lon, lat, stamp)
		csvfile.close()
		render_video(width, height, zoom, cumulative)
	except:
		PrintException()

# test
read_csv('/Users/maxvonhippel/Documents/OSMHistoryServer/nodes.csv', 500, 500, 5, True)