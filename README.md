README
======

* Installation

```
virtualenv venv
source venv/bin/activate
pip install numpy
pip install --upgrade cython
pip install lxml
pip install dragnet
pip install redis 
pip install readability-lxml
pip install requests
pip install cherrypy

mkdir images
mkdir cache
python newscorpse/server.py
```

* Usage

```
http://127.0.0.1:8080/url-without-the-http
```