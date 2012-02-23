#!/usr/bin/make

.PHONY: doc
doc:
	/usr/bin/epydoc --verbose --graph all --output=./doc ./scrape.py
