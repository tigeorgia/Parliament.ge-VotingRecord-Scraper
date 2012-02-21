Parliament.ge Voting Record Scraper Suite
=========================================

[BeautifulSoup](http://www.crummy.com/software/BeautifulSoup/ "Beautiful Soup") is required.
To install, e.g.:
$ sudo apt-get install python-beautifulsoup
or
$ sudo pip install BeautifulSoup


Edit the HOST and ROOT document to start scraping from in the head of scrape.py and then run:

$ python scrape.py --output=<outdir>

It outputs data in JSON format for each bill (by bill number or date if the former is not available) into the given <outdir>. The script will output status messages about each bill being written and the time it took to scrape one page.

Enjoy.
