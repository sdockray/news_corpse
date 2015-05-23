# -*- coding: utf-8 -*-
import hashlib
import os, sys  
import urlparse

import cherrypy
from cherrypy.lib.static import serve_file

from lxml import html  
import requests
from dragnet import content_extractor
from readability.readability import Document

IMAGES = 'images'
CACHE = 'cache'

# requests a url and converts content to markdown
class Rich(object):
	def __init__(self, url):
		self.url = 'http://%s' % url
		self.hashed = hashlib.md5(url).hexdigest()

	def get_images(self, text):
		body = html.fromstring(text)
		images = body.xpath('//img/@src')
		replacements = {}
		if images:
			images = [urlparse.urljoin(self.url, url) for url in images]
			for url in images:
				try:
					r = requests.get(url)
					p = '%s/%s' % (IMAGES, url.split('/')[-1])
					if not os.path.exists(p):
						f = open(p, 'w')
						f.write(r.content)
						f.close()
					replacements[url] = '/%s' % p
				except:
					pass
		return replacements

	def replace_images(self, content, images):
		for url in images:
			content = content.replace(url, images[url])
		return content

	def emancipate(self):
		cached = os.path.join(cache_dir, self.hashed)
		# load from cache
		if os.path.exists(cached):
			with open(cached, 'r') as f:
				return f.read()
		# hit server
		r = requests.get(self.url, timeout=10)
		if r.ok:
			c = self.replace_images(Document(r.content).summary(), self.get_images(r.text))
			with open(cached, 'w') as f:
				f.write(c.encode('utf-8').strip())
			return c

# 
class Poor(object):
	@cherrypy.expose
	def default(self, *args, **kwargs):
		return Rich('/'.join(args)).emancipate()

	@cherrypy.expose
	def images(self, name):
		return serve_file(os.path.join(images_dir,name))

# Starting things up
if __name__ == '__main__':
	current_dir = os.path.dirname(os.path.abspath(__file__))
	images_dir = os.path.join(current_dir,'..',IMAGES)
	cache_dir = os.path.join(current_dir,'..',CACHE)
	try:
		app = cherrypy.tree.mount(Poor(), '/')
		cherrypy.quickstart(app)
	except:
		pass