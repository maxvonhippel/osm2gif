#!/usr/bin/python
from __future__ import print_function
import os
import linecache
import sys
import dateutil.parser
from staticmap import StaticMap, CircleMarker, Polygon
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

def render_video(sigma, video_name, width, height, zoom):
	# iff sigma == True, each frame contains all previous frames' stuff
	# otherwise only stuff from that specific day
	try:
		# http://stackoverflow.com/a/35943809/1586231
		if not video_name.endswith('.gif'):
			video_name += '.gif'
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
		for single_date in daterange(youngest, eldest):
			day = single_date.strftime("%Y-%m-%d")
			# make the map
			_map = StaticMap(int(float(width)), int(float(height)), url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')
			if day in days.keys():
				print("day is in days")
				# add the nodes
				for node in days[day]['nodes']:
					marker = CircleMarker([int(float(node[0])), int(float(node[1]))], '#ff0000', 8)
					_map.add_marker(marker)
				# add the ways
				for way in days[day]['ways']:
					poly = Polygon([[int(float(node[0])), int(float(node[1]))] for node in coords], '#ff0000', '#ff0000', True)
					_map.add_polygon(poly)
			else:
				print("empty map")
				# get the empty image of average location for this list
				# set it to be the "open_image"
				_map.set_extent(83.676659, 28.220671, 83.804604, 28.409901)
			# render
			print("zoom: ", int(float(zoom)))
			_img = _map.render(zoom=5)
			# save
			_name = str(day) + ".png"
			_img.save(_name)
			# now add to frames list for video
			sequence.append(Image.open(_name))

		# https://github.com/python-pillow/Pillow/blob/master/Scripts/gifmaker.py
		frames = [frame.copy() for frame in ImageSequence.Iterator(sequence)]
		fp = open(video_name, "wb")
		im = Image.open(fp)
		im.save(frames, save_all=True)
		fp.close()
		print("all done!")
		clean_up_frames(sequence)
	
	except:
		PrintException()

def clean_up_frames(frames):
	for frame in frames:
		os.remove(frame)

# for OSM (.osm, .osh, .pbf) files
def read_osm(file, width, height, zoom, video_name, sigma):
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
		render_video(sigma, video_name, width, height, zoom)
	except:
		PrintException()

# for .csv files
# format: id,longitude,latitude,"{[Name:timestamp], ... }"
def read_csv(file, width, height, zoom, video_name, sigma):
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
						if parsd % 100000 == 0:
							print("num nodes parsed: ", parsd)
						add_node(lon, lat, stamp)
		csvfile.close()
		render_video(sigma, video_name, width, height, zoom)
	except:
		PrintException()

# test
read_csv('/Users/maxvonhippel/Documents/OSMHistoryServer/nodes.csv', 500, 500, 5, "nepal-osm-vid", False)