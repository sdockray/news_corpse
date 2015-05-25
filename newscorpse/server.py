# -*- coding: utf-8 -*-
import hashlib
import os, sys  
import re
import urlparse

import cherrypy
from cherrypy.lib.static import serve_file

from lxml import html  
import requests
from readability.readability import Document

MANIFESTO = """
Use plain.press to stop ad revenue and user data from your shares and 
clicks going to those corporations who are working against your values.  
"""

IMAGES = 'images'
CACHE = 'cache'
WHITELIST = ['smh.com.au','theage.com.au','theaustralian.com.au','afr.com.au','news.com.au','heraldsun.com.au','dailytelegraph.com.au','couriermail.com.au','abc.net.au']

current_dir = os.path.dirname(os.path.abspath(__file__))
images_dir = os.path.join(current_dir,'..',IMAGES)
cache_dir = os.path.join(current_dir,'..',CACHE)

# Is the page handled?
def whitelisted(url):
	for w in WHITELIST:
		if w in url:
			return True
	return False

# init with a url and then liberate to grab stripped down markup and images
class Rich(object):
	def __init__(self, url):
		self.url = 'http://%s' % url
		self.hashed = hashlib.md5(url).hexdigest()

	def get_images(self, text):
		body = html.fromstring(text)
		images = body.xpath('//img/@src')
		replacements = {}
		if images:
			images = [(urlparse.urljoin(self.url, url),url) for url in images]
			for url, original_url in images:
				try:
					r = requests.get(url)
					h = hashlib.md5(url).hexdigest()
					p = '%s/%s.%s' % (IMAGES, h, url.split('.')[-1])
					if not os.path.exists(p):
						f = open(p, 'w')
						f.write(r.content)
						f.close()
					replacements[original_url] = '/%s' % p
				except Exception as e:
					print e;
					pass
		return replacements

	def replace_images(self, content, images):
		for url in images:
			print "--- replace %s with %s" % (url, images[url])
			content = content.replace(url, images[url])
		return content

	def replace_links(self,content):
		body = html.fromstring(content)
		links = body.xpath('//a/@href')
		if links:
			for url in links:
				print "++=======" + url;
				content = content.replace(url,re.sub(r"https?://", "/", url))
		return content;

	def inject_meta(self, title, content):
		return content.replace(
			'<body>',
			'<head><title>%s</title>%s</head><body><h1>%s</h1>' % (
				title,
				"""
				<meta property="og:title" content="%s" /> 
	  		<meta property="og:description" content="%s" /> 
	  		""" % (title, MANIFESTO),
				title
		))

	def liberate(self):
		cached = os.path.join(cache_dir, self.hashed)
		# load from cache
		if os.path.exists(cached):
			with open(cached, 'r') as f:
				return f.read()
		# hit server
		try:
			r = requests.get(self.url, timeout=10)
		except:
			return "Was that a valid url?"
		if r.ok:
			title = Document(r.content).short_title()
			html = Document(r.content).summary()
			c = self.replace_images(html, self.get_images(r.text))
			c = self.replace_links(c)
			c = self.inject_meta(title, c)
			with open(cached, 'w') as f:
				f.write(c.encode('utf-8').strip())
			return c

# Gives liberated content to the masses
class Poor(object):
	@cherrypy.expose
	def default(self, *args, **kwargs):
		u = '/'.join(args)
		if not whitelisted(args[0]): 
			raise cherrypy.HTTPRedirect('http://'+u)
		return Rich(u).liberate() 

	@cherrypy.expose
	def images(self, name):
		print 'IMAGES';
		return serve_file(os.path.join(images_dir,name))

	@cherrypy.expose
	def index(self, url=None):
		if url:
			raise cherrypy.HTTPRedirect(cherrypy.request.base + '/' + re.sub(r"https?://", "", url))
		else:
			return """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html><head><title>plain.press</title></head><body style="text-align:center; margin-top:150px;">
<form method='get' style="width:100%; margin:'0px auto'">
<input value="" name="url" size='70' style="line-height: 20px;"/>
<input type='submit' value='plain.press' />
</form></body></html>
			"""

# Starting things up
if __name__ == '__main__':
	try:
		app = cherrypy.tree.mount(Poor(), '/')
		cherrypy.quickstart(app)
	except:
		print "Poor server couldn't start :("
