#!/usr/bin/python
# vim: set fileencoding=utf-8
"""Voting Records scraper.

Scrapes the voting records from http://www.parliament.ge/index.php?sec_id=1530&lang_id=GEO .
"""
import sys, os, getopt, urllib2, re, json, time
from BeautifulSoup import BeautifulSoup


HOST = 'http://www.parliament.ge/'
ROOT = HOST + 'index.php?sec_id=1530&lang_id=GEO&kan_name=&kan_num=&kan_mp=&Search=ძიება'
#HOST = 'file:///home/shensche/votingrecord/Parliament.ge-VotingRecord-Scraper/'
#ROOT = HOST + 'first.html'
NEXT_PAGE = HOST + 'index.php?lang_id=GEO&sec_id=1530&kan_name=&kan_num=&kan_mp=&Search=ძიება&limit='
JSON_INDENT = 2
OUTDIR = os.getcwd() + os.sep



class ScrapeError (Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)


def not_in_hidethis (tags):
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


def get_kan_id (tag):
    return tag.attrs[0][1].split('=')[-1]


def bill_det (soup):
    regex = re.compile('kan_det=det')
    tags = not_in_hidethis(soup.findAll('a', attrs={'href':regex}))

    data = []
    for a in tags:
        data.append({
            'link': a.attrs[0][1],
            'name': a.contents[0].string,
            'kan_id': get_kan_id(a)
        })
    return data


def bill_number (soup):
    regex = re.compile('^\s?\d\S*') # can't mach [-–], so using \S ??
    tags = not_in_hidethis(soup.findAll('td', attrs={'width':'50', 'align':'center'}))
    data = []
    for td in tags:
        if len(td.contents) == 0: # no bill number
            data.append(None)
        else:
            if re.match(regex, td.contents[0].string):
                data.append(td.contents[0].string.strip())
    return data


def bill_date (soup):
    regex = re.compile('^\d{4}-\d{2}-\d{2}$')
    tags = not_in_hidethis(soup.findAll('td', attrs={'width':80, 'align':'center'}))
    data = []
    for td in tags:
        if re.match(regex, td.contents[0].string):
            data.append(td.contents[0].string)
    return data


def bill_result (soup):
    regex = re.compile('kan_det=res')
    tags = soup.findAll('a', attrs={'href':regex})
    data = []
    for a in tags:
        fp = urllib2.urlopen(HOST + a.attrs[0][1])
        #fp = urllib2.urlopen(HOST + 'res.html')
        result = BeautifulSoup(fp)
        table = result.find('table', attrs={'width': '500', 'border':'0', 'align':'left', 'cellpadding':'3', 'cellspacing':'2', 'bgcolor':'#EEEEEE'})
        votes = []
        for tr in table.findAll('tr', attrs={'bgcolor':'#FFFFFF'}):
            children = tr.findChildren()
            votes.append({
                'name': children[0].contents[0].string,
                'vote': children[1].contents[0].string
            })
        fp.close()
        data.append(votes)
        time.sleep(1) # give the server some time to breathe
    return data


def bill_amendments (soup, det):
    data = [[] for num in xrange(len(det))]
    # each div contains a list of amendments
    tags = soup.findAll('div', attrs={'class':'hidethis'})
    for div in tags:
        # find parent bill's index for this div's kan_id
        bill = div.parent.parent.findPreviousSibling()
        kan_id = get_kan_id(bill.find('td').find('a'))
        for d in det:
             if d['kan_id'] == kan_id:
                idx = det.index(d)
                break

        # find amendment numbers
        nums = []
        for tr in div.findAll('tr'):
            td = tr.findAll('td')
            if len(td[1].contents) == 0:
                nums.append(None)
            else: # use bill number
                nums.append(td[1].contents[0])
        data[idx] = nums

    return data



def next_page (soup, is_root=False):
    regex = re.compile('limit=')
    tags = soup.findAll('a', attrs={'href':regex})
    if len(tags) < 5 and not is_root: # last page
        return None

    limit = ''
    for attr in tags[-2].attrs: # -2 is next page
        if attr[0] == 'href':
            limit = attr[1].split('=')[-1]
    return NEXT_PAGE + limit.encode('utf-8')



def write_record (data):
    global OUTDIR # might have been changed by opts
    print 'Voting record for bill %s, kan_id %s' % (data['number'], data['kan_id'])
    out = OUTDIR + data['kan_id'] + '.json'
    fp = open(out, 'w')
    json.dump(data, fp, indent=JSON_INDENT)
    fp.close()


def page (soup):
    det = bill_det(soup)
    len_det = len(det)
    if len_det == 0:
        print 'WARNING: No bills found. Is this the right document?'
        return False

    number = bill_number(soup)
    len_number = len(number)
    if len_number != len_det:
        raise ScrapeError('Number mismatch: bill number %d != bill det %d' % (len_number, len_det))

    date = bill_date(soup)
    len_date = len(date)
    if len_date != len_det:
        raise ScrapeError('Number mismatch: bill date %d != bill det %d' % (len_date, len_det))

    # fix the bill numbers if necessary
    #for i in xrange(len(number)):
    #    if not number[i]:
    #        number[i] = date[i]

    result = bill_result(soup)
    len_result = len(result)
    if len_result != len_det:
        for i in xrange(abs(len_det - len_result)): # fill with empty values
            result.append('')
        #raise ScrapeError('Number mismatch: bill result %d != bill det %d' % (len_result, len_det))

    amendments = bill_amendments(soup, det)

    for i in xrange(len_det):
        record = {
            'kan_id': det[i]['kan_id'],
            'link': HOST + det[i]['link'],
            'name': det[i]['name'],
            'number': number[i],
            'date': date[i],
            'result': result[i],
            'amendments': amendments[i]
        }
        write_record(record)

    return True


def scrape (url, is_root=False):
    fp = urllib2.urlopen(url)
    soup = BeautifulSoup(fp)
    page(soup)
    fp.close()
    return next_page(soup, is_root)


def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ho:', ['help', 'output='])
    except getopt.error, msg:
        print msg
        print 'For help use --help'
        sys.exit(2)

    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        elif o in ("-o", "--output"):
            global OUTDIR
            OUTDIR = a
            if not os.path.exists(OUTDIR):
                os.mkdir(OUTDIR)
            if OUTDIR[-1] != os.sep:
                OUTDIR += os.sep

    print 'Writing to directory %s' % OUTDIR
    print 'Scraping %s' % ROOT
    time_start = time.time()
    time_start_global = time_start
    nxt = scrape(ROOT, is_root=True)
    print 'Took %d seconds.' % (time.time() - time_start)
    while nxt:
        print 'Scraping %s' % nxt
        time_start = time.time()
        nxt = scrape(nxt, is_root=False)
        print 'Took %d seconds.' % (time.time() - time_start)

    print 'The whole scraping took %d seconds.' % (time.time() - time_start_global)


if __name__ == "__main__":
    main()
