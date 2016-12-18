# osm2gif
Turns OSM files into animated GIFs.

# Dependencies (pip)

* [pyosmium](https://github.com/osmcode/pyosmium)
* [staticmap](https://github.com/komoot/staticmap)
* [imageio](https://imageio.github.io)

# Command-Line Use

Format is:

> python osm2gif.py file.osm outname width height zoom

For example:

> python osm2gif.py path/to/full-planet-dump.osh.pbf awesomegif 500 400 8

Honestly not sure if you could actually run this on a full history dump.  You probably couldn't.  I'd reccomend using something smaller.

Fairly certain this doesn't yet work.  It's close, though.
