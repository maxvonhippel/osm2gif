#!/usr/bin/python
import linecache
import sys
import dateutil.parser
from staticmap import StaticMap, CircleMarker, Polygon
import imageio
import csv
from StringIO import StringIO
__author__ = 'Robert'
from images2gif import writeGif
from PIL import Image
import os

# http://stackoverflow.com/a/20264059/1586231
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

# to hold all our days
days = {}

def add_node(x, y, timestamp):
	# add the node
	marker = CircleMarker((x, y), 'white', 8)
	if not timestamp in days:
		days[timestamp] = []
	days[timestamp].append([x, y])

# for OSM (.osm, .osh, .pbf) files
def read_osm(file, width, height, zoom, video_name):
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
		# on complete, render frames into a video
		# http://stackoverflow.com/a/35943809/1586231
		if not video_name.str.endswith('.gif'):
			video_name += '.gif'
		with imageio.get_writer(video_name, mode='I') as writer:
			for stamp in days:
				# make the map
				_map = StaticMap(width, height, url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')
				# add the nodes
				for node in days[stamp]:
					marker = CircleMarker((int(float(node[0])), int(float(node[1]))), '#ff0000', 8)
					_map.add_marker(marker)
				# add the ways
				for way in days[stamp].ways:
					_map.add_polygon(way)
				# render
				_img = _map.render(zoom=zoom)
				# save
				_name = stamp + ".png"
				_img.save(_name)
				# now add to frames list for video
				frame = imageio.imread(_name)
				writer.append_data(frame)
			# now exit gracefully
			print("all done.")
	except:
		PrintException()

# for .csv files
# format: id,longitude,latitude,"{[Name:timestamp], ... }"
def read_csv(file, width, height, zoom, video_name):
	parsd = 0
	mapd = 0
	try:
		if not video_name.endswith('.gif'):
			video_name += '.gif'
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
						if parsd % 10000 == 0:
							print("num nodes parsed: ", parsd)
						add_node(lon, lat, stamp)
		csvfile.close()
		# with imageio.get_writer(video_name, mode='I') as writer:
		images = []
		for stamp in days:
			# make the map
			_map = StaticMap(int(float(width)), int(float(height)), url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')
			# add the nodes
			for node in days[stamp]:
				marker = CircleMarker((int(float(node[0])), int(float(node[1]))), '#ff0000', 8)
				_map.add_marker(marker)
			# render
			_img = _map.render(zoom=int(float(zoom)))
			# save
			# print("stamp: ", stamp, " versions: ", days[stamp])
			_name = "_osm2gif" + stamp + ".png"
			_img.save(_name)
			# now add to frames list for video
			# frame = imageio.imread(_name)
			# writer.append_data(frame)
			open_image = Image.open(_name)
			images.append(open_image)
			open_image.thumbnail((width, height), Image.ANTIALIAS)

			mapd += 1
			if mapd % 100 == 0:
				print writeGif.__doc__
				writeGif(str(mapd / 100) + video_name, images, duration=0.2)
				images = []
		# now exit gracefully
		print writeGif.__doc__
		writeGif(video_name, images, duration=0.2)
		print("all done.")
	except:
		PrintException()

# test
read_csv('/Users/maxvonhippel/Documents/OSMHistoryServer/nodes.csv', 500, 500, 5, "nepal-osm-vid")