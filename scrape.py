#!/usr/bin/python
# vim: set fileencoding=utf-8
"""Voting Records scraper.

Scrape the voting records of the Georgian Parliament.
"""
import sys, os, getopt, urllib2, re, json, time
from BeautifulSoup import BeautifulSoup


HOST = 'http://www.parliament.ge/'
DOC = 'index.php'
PARAMS = '?sec_id=1530&lang_id=GEO&kan_name=&kan_num=&kan_mp=&Search=ძიება'
ROOT = HOST + DOC + PARAMS
NEXT_PAGE = ROOT + '&limit='
#HOST = 'file:///home/shensche/votingrecord/Parliament.ge-VotingRecord-Scraper/'
#ROOT = HOST + 'first.html'
SLEEP = 1 # how long to wait between request
JSON_INDENT = 2 # indentation for JSON output
OUTDIR = os.getcwd() + os.sep # default output directory



class ScrapeError (Exception):
    """Generic scrape exception."""
    def __init__(self, value):
        super(ScrapeError, self).__init__()
        self.value = value
    def __str__(self):
        return repr(self.value)


class VotingRecordsScraper (object):
    """Class to scrape the voting records."""

    def __init__ (self, outdir):
        """Constructor

        @param outdir output directory
        """
        if outdir[-1] != os.sep:
            self.outdir = outdir + os.sep
        else:
            self.outdir = outdir


    def not_in_hidethis (self, tags):
        """Get tags which are not inside a parent tag with class 'hidethis'.

        @param tags list BeautifulSoup.Tag to search in
        @return list of BeautifulSoup.Tag
        """
        data = []
        for tag in tags:
            hidethis = False
            for attr in tag.parent.parent.parent.parent.attrs:
                if attr[0] == 'class' and attr[1] == 'hidethis':
                    hidethis = True
            for attr in tag.parent.parent.parent.attrs:
                if attr[0] == 'class' and attr[1] == 'hidethis':
                    hidethis = True
            if not hidethis:
                data.append(tag)
        return data


    def get_kan_id (self, tag):
        """Get kan_id in given 'a'-tag.

        kan_id seems to be the only identifier for the voting records data.

        @param tag BeautifulSoup.Tag representing an HTML <a>
        @return string containing the kan_id
        """
        return tag.attrs[0][1].split('=')[-1]


    def bill_det (self, soup):
        """Find all det (? nomenclature of parliament.ge) on current page.

        A det contains info about uri to the actual bill, name and kan_id.

        @param soup BeautifulSoup.BeautifulSoup
        @return list of bill records: relative uri, name, kan_id
        """
        regex = re.compile('kan_det=det')
        tags = self.not_in_hidethis(soup.findAll('a', attrs={'href':regex}))

        data = []
        for anchor in tags:
            data.append({
                'uri': anchor.attrs[0][1],
                'name': anchor.contents[0].string.strip(),
                'kan_id': self.get_kan_id(anchor)
            })
        return data


    def bill_number (self, soup):
        """Find all bill numbers on current page.

        @param soup BeautifulSoup.BeautifulSoup
        @return list of bill numbers
        """
        regex = re.compile('^\s?\d\S*') # can't mach [-–], so using \S ??
        tags = soup.findAll('td', attrs={'width':'50', 'align':'center'})
        tags = self.not_in_hidethis(tags)
        data = []
        for tag in tags:
            if len(tag.contents) == 0: # no bill number
                data.append(None)
            else:
                if re.match(regex, tag.contents[0].string):
                    data.append(tag.contents[0].string.strip())
        return data


    def bill_date (self, soup):
        """Find all bill dates on current page.

        @param soup BeautifulSoup.BeautifulSoup
        @return list of bill dates
        """
        regex = re.compile('^\d{4}-\d{2}-\d{2}$')
        tags = soup.findAll('td', attrs={'width':80, 'align':'center'})
        tags = self.not_in_hidethis(tags)
        data = []
        for tag in tags:
            if re.match(regex, tag.contents[0].string):
                data.append(tag.contents[0].string)
        return data


    def bill_result (self, soup):
        """Find all bill voting results on current page.

        @param soup BeautifulSoup.BeautifulSoup
        @return list of bill voting results
        """
        regex = re.compile('kan_det=res')
        tags = soup.findAll('a', attrs={'href':regex})
        data = []
        for anchor in tags:
            handle = urllib2.urlopen(HOST + anchor.attrs[0][1])
            #handle = urllib2.urlopen(HOST + 'res.html')
            result = BeautifulSoup(handle)
            table = result.find('table', attrs={
                'width': '500',
                'border':'0',
                'align':'left',
                'cellpadding':'3',
                'cellspacing':'2',
                'bgcolor':'#EEEEEE'
            })
            votes = []
            for tag in table.findAll('tr', attrs={'bgcolor':'#FFFFFF'}):
                children = tag.findChildren()
                votes.append({
                    'name': children[0].contents[0].string,
                    'vote': children[1].contents[0].string
                })
            handle.close()
            data.append(votes)
            time.sleep(SLEEP) # give the server some time to breathe
        return data


    def bill_amendments (self, soup, dets):
        """Find all bill amendments on current page.

        @param soup BeautifulSoup.BeautifulSoup
        @param dets det list
        @return list of bill amendments
        """
        # prepopulate data to be returned
        data = [[] for _ in xrange(len(dets))]

        # each div contains a list of amendments
        tags = soup.findAll('div', attrs={'class':'hidethis'})
        for div in tags:
            # find parent bill's index for this div's kan_id
            bill = div.parent.parent.findPreviousSibling()
            kan_id = self.get_kan_id(bill.find('td').find('a'))
            for det in dets:
                if det['kan_id'] == kan_id:
                    idx = dets.index(det)
                    break

            # find amendment numbers
            nums = []
            for row in div.findAll('tr'):
                cols = row.findAll('td')
                if len(cols[1].contents) == 0:
                    nums.append(None)
                else: # use bill number
                    nums.append(cols[1].contents[0])
            data[idx] = nums

        return data


    def next_page (self, soup, is_root=False):
        """Determine the URL of the next page to scrape.

        @param soup BeautifulSoup.BeautifulSoup
        @param is_root boolean if current page is the root page
        @return string containing URL of the next page to scrape
        """
        regex = re.compile('limit=')
        tags = soup.findAll('a', attrs={'href':regex})
        if len(tags) < 5 and not is_root: # last page
            return None

        limit = ''
        for attr in tags[-2].attrs: # -2 is next page
            if attr[0] == 'href':
                limit = attr[1].split('=')[-1]
        return NEXT_PAGE + limit.encode('utf-8')


    def write_record (self, data):
        """Write a complete voting record to (JSON) file.

        @param data dict containing all voting record data
        """
        print 'Voting record for bill %s, kan_id %s' % (
            data['number'], data['kan_id']
        )

        out = self.outdir + data['kan_id'] + '.json'
        handle = open(out, 'w')
        json.dump(data, handle, indent=JSON_INDENT)
        handle.close()


    def page (self, soup):
        """Scrape a whole page and write it to file.

        @param soup BeautifulSoup.BeautifulSoup
        """
        det = self.bill_det(soup)
        len_det = len(det)
        if len_det == 0:
            print 'WARNING: No bills found. Is this the right document?'
            return False

        number = self.bill_number(soup)
        len_number = len(number)
        if len_number != len_det:
            fmt = 'Number mismatch: bill number %d != bill det %d'
            raise ScrapeError(fmt % (len_number, len_det))

        date = self.bill_date(soup)
        len_date = len(date)
        if len_date != len_det:
            fmt = 'Number mismatch: bill date %d != bill det %d'
            raise ScrapeError(fmt % (len_date, len_det))

        result = self.bill_result(soup)
        len_result = len(result)
        if len_result != len_det:
            for i in xrange(abs(len_det - len_result)): # fill with empty values
                result.append('')

        amendments = self.bill_amendments(soup, det)

        for i in xrange(len_det):
            record = {
                'kan_id': det[i]['kan_id'],
                'url': HOST + det[i]['uri'],
                'name': det[i]['name'],
                'number': number[i],
                'date': date[i],
                'result': result[i],
                'amendments': amendments[i]
            }
            self.write_record(record)

        return True


    def scrape (self, url, is_root=False):
        """Scrape one page and return the next page's URL.

        @param url URL of the page to scrape
        @param is_root boolean if current page is the root page
        @return string containing URL of the next page to scrape
        """
        time_start = time.time()
        print 'Scraping %s' % url

        handle = urllib2.urlopen(url)
        soup = BeautifulSoup(handle)
        self.page(soup)
        handle.close()

        nxt = self.next_page(soup, is_root)
        print 'Took %d seconds.' % (time.time() - time_start)
        return nxt


    def run (self):
        """Run the scraping process."""
        print 'Writing to directory %s' % self.outdir
        time_start_global = time.time()

        nxt = self.scrape(ROOT, is_root=True)
        while nxt:
            nxt = self.scrape(nxt, is_root=False)
            time.sleep(SLEEP) # give the server some time to breathe

        print 'The whole scraping took %d seconds.' % (
            time.time() - time_start_global
        )


def main():
    """Main function in case the class isn't used directly."""
    # parse command line options
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'ho:', ['help', 'output='])
    except getopt.error, msg:
        print msg
        print 'For help use --help'
        sys.exit(2)

    # process options
    outdir = None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        elif opt in ("-o", "--output"):
            outdir = arg

    if not outdir:
        outdir = OUTDIR
    if not os.path.exists(outdir):
        os.mkdir(outdir)

    VotingRecordsScraper(outdir).run()


if __name__ == "__main__":
    main()
