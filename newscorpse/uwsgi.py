import cherrypy
from newscorpse.server import Poor

def application(environ, start_response):
	conf = {}
	cherrypy.config.update({
		'server.socket_port': 8080
	})
	app = cherrypy.tree.mount(Poor(), '/', config=conf)
	return cherrypy.tree(environ, start_response)
