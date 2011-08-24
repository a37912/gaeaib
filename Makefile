all: build

build: buildout.cfg bin/buildout
	bin/buildout



templates: bin/jinja2_compile
	env PYTHONPATH=src/distlib bin/jinja2_compile
