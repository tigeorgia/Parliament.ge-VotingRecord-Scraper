Parliament.ge Voting Record Scraper
===================================

Description
-----------

A tool to scrape voting records of passed / draf bills from [Georgia's parliament website](http://parliament.ge "parliament.ge"). The results are placed into JSON files for each individual bill.



Requirements
------------

- [Python](http://python.org "Python") 2.7
  But older and newer versions might work.
- [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/ "Beautiful Soup") 3.2.0
  To install, e.g.:
  $ sudo apt-get install python-beautifulsoup
  or
  $ sudo pip install BeautifulSoup

- [epydoc](http://epydoc.sourceforge.net/ "epydoc")
- [make](http://www.gnu.org/software/make/ "make")
  If you want to generate API documentation.



Configuration
-------------
You should be able to run the scraper as is.
If something on parliament.ge changes, edit HOST, DOC, PARAMS and NEXT\_PAGE accordingly.



Usage
-----
$ python scrape.py --output=<outdir>

It outputs data in JSON format for each voting record (by kan\_id, some bills don't have a number) into the given <outdir>. The script will output status messages about each record being written and the time it took to scrape one page.



Documentation
-------------
If you have epydoc and make installed, you can create the API documentation using
$ make doc



Enjoy.
