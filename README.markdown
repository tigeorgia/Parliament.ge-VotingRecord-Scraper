Parliament.ge Voting Record Scraper
===================================

Requirements
------------

- [Python](http://python.org "Python") (2.7, but older and newer versions might work)
- [BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/ "Beautiful Soup")
  To install, e.g.:
  $ sudo apt-get install python-beautifulsoup
  or
  $ sudo pip install BeautifulSoup


Configuration
-------------
You should be able to run the scraper as is.
If something on parliament.ge changes, edit HOST, DOC, PARAMS and NEXT\_PAGE accordingly.


Usage
-----
$ python scrape.py --output=<outdir>

It outputs data in JSON format for each voting record (by kan\_id, some bills don't have a number) into the given <outdir>. The script will output status messages about each record being written and the time it took to scrape one page.



Enjoy.
