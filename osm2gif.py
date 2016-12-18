#!/usr/bin/python
import linecache
import sys
import dateutil.parser
from staticmap import StaticMap, CircleMarker, Polygon
import imageio
import csv
from StringIO import StringIO

# http://stackoverflow.com/a/20264059/1586231
def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)

class Day():
	# init a day
	def __init__(self):
		# dateutil.parser.parse(day).timestamp()
		self.nodes = []
		self.ways = []
	# add a node
	def add_node_to_day(self, node):
		self.nodes.append(node)
	# add a way
	def add_way_to_day(self, way):
		self.ways.append(way)

# to hold all our days
days = {}

def add_node(x, y, timestamp):
	# add the node
	marker = CircleMarker((x, y), 'white', 8)
	if not timestamp in days:
		days[timestamp] = Day()
	days[timestamp].add_node_to_day(marker)

def add_way(items, timestamp):
	# add the way
	polygon = Polygon([[i.lon, i.lat] for i in items], 'white', 'white', simplify)
	if not timestamp in days:
		days[timestamp] = Day()
	days[timestamp].add_way_to_day(polygon)


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
				for node in days[stamp].nodes:
					_map.add_marker(node)
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
				versions = csv.reader(StringIO(row[3][1:-1]))
				for row in versions:
					if len(row) == 2:
						stamp = row[1]
						parsd += 1
						if parsd % 10000 == 0:
							print("num nodes parsed: ", parsd)
						add_node(lon, lat, stamp)
		csvfile.close()
		with imageio.get_writer(video_name, mode='I') as writer:
			for stamp in days:
				# make the map
				_map = StaticMap(width, height, url_template='http://a.tile.osm.org/{z}/{x}/{y}.png')
				# add the nodes
				for node in days[stamp].nodes:
					_map.add_marker(node)
				# add the ways
				for way in days[stamp].ways:
					_map.add_polygon(way)
				# render
				_img = _map.render(zoom=zoom)
				# save
				_name = video_name + "/" + stamp + ".png"
				_img.save(_name)
				# now add to frames list for video
				frame = imageio.imread(_name)
				writer.append_data(frame)
				mapd += 1
				if mapd % 1000 == 0:
					print("num nodes mapped into video: ", mapd)
			# now exit gracefully
			print("all done.")
	except:
		PrintException()

# test
read_csv('/Users/maxvonhippel/Documents/OSMHistoryServer/nodes.csv', 500, 500, 5, "nepal-osm-vid")