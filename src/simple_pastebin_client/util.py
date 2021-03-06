from bs4 import BeautifulSoup, SoupStrainer
from datetime import datetime
from pytz import timezone, utc
import tzlocal
from .consts import *
from time import mktime


def extract_date_from_html(html_page, tz='US/Central'):
    _span = BeautifulSoup(html_page, 'html.parser',
                          parse_only=SoupStrainer('span'))
    spans = [i for i in _span.find_all() if has_attr(i, 'title')]
    if len(spans) == 1:
        return extract_date(spans[0]['title'], tz=tz)

    # editied
    for s in spans:
        new_title = None
        try:
            new_title = s['title']
            if new_title.find('Last edit on: ') == 0:
                new_title = s['title'].replace('Last edit on: ', '')
                return extract_date(new_title, tz=tz)
        except:
            pass
    for s in spans:
        if 'title' not in s:
            continue
        try:
            return extract_date(s['title'], tz=tz)
        except:
            pass
    return ''


def date_to_timestamp(date_str, day=False):
    if date_str.isdigit():
        return int(date_str)
    if date_str == '':
        return -1
    unix_ts = 0
    if not day:
        unix_ts = mktime(datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").timetuple())
    else:
        date_str = date_str.split('T')[0]
        unix_ts = mktime(datetime.strptime(date_str, "%Y-%m-%d").timetuple())
    return int(unix_ts)


def extract_date(date_str, tz='US/Central'):
    tz = tzlocal.get_localzone().zone if tz is None else tz
    nd = date_str.replace('st ', ' ').replace('th ', ' ').replace(' of ', ' ')
    nd = nd.replace('rd ', ' ').replace('nd ', ' ').replace('Augu', 'August')
    try:
        dt = datetime.strptime(nd, EXPECTED_PB_TIME)
        dt_loc = timezone(tz).localize(dt)
        return dt_loc.astimezone(utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except:
        nnd = " ".join(nd.split()[:-1])
        dt = datetime.strptime(nnd, MEXPECTED_PB_TIME)
        dt_loc = timezone(tz).localize(dt)
        return dt_loc.astimezone(utc).strftime("%Y-%m-%dT%H:%M:%SZ")



def extract_date_user_page(date_str):
    tz = tzlocal.get_localzone().zone
    nd = date_str.replace(',', '').replace('st ', ' ')
    nd = nd.replace('th ', ' ').replace(' of ', ' ')
    nd = nd.replace('rd ', ' ').replace('nd ', ' ').replace('Augu', 'August')
    fixed_stirng = nd
    fixed_stirng = fixed_stirng.strip()
    dt = datetime.strptime(fixed_stirng, "%b %d %Y")
    dt_loc = timezone(tz).localize(dt)
    return dt_loc.astimezone(utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_elements(html_page, tag, attr, value_in=None):
    tags = BeautifulSoup(html_page, 'html.parser',
                         parse_only=SoupStrainer(tag))

    vals = []
    for i in [j for j in tags.find_all()]:
        if has_attr(i, attr):
            if value_in is None:
                vals.append(i)
            elif value_in in i[attr]:
                vals.append(i)
    return vals


def extract_single_element(html_page, tag, attr, value_in):
    vals = extract_elements(html_page, tag, attr, value_in)
    if len(vals) > 0:
        return vals[0]
    return None


def extract_paste_box_line1(html_page):
    tag = BeautifulSoup(html_page, 'html.parser',
                         parse_only=SoupStrainer('h1')).get_text()

    title = '' if tag is None else tag
    return {'title': title}


def extract_paste_box_line2(html_page, tz="US/Central"):
    tag, attr, value_in = [DIV, CLASS, PBOX_2]
    pbox2 = extract_single_element(html_page, tag, attr, value_in)
    # extract user
    _hrefs = BeautifulSoup(str(pbox2), 'html.parser',
                           parse_only=SoupStrainer('a'))
    pusers = [i.get('href').strip('/u/') for i in _hrefs.find_all()
              if has_attr(i, 'href') and i['href'].find('/u/') == 0]

    user = pusers[0] if len(pusers) > 0 else ''

    # extract date
    date = extract_date_from_html(str(pbox2), tz)
    unixts = date_to_timestamp(date)
    return {'user': user, 'timestamp': date, 'unix': unixts}


def extract_text_data(html_page):
    textarea = BeautifulSoup(str(html_page), 'html.parser',
                             parse_only=SoupStrainer(TEXTAREA))
    textdata = ''
    if textarea is not None:
        textdata = textarea.text
    return {'data': textdata}


def extract_paste_content(html_page, tz=None):
    r = {}
    r.update(extract_paste_box_line1(html_page))
    r.update(extract_paste_box_line2(html_page, tz=tz))
    r.update(extract_text_data(html_page))
    return r


def not_these(text, these=[]):
    return text not in these


def has_attr(node, attr='href'):
    return node.get(attr, None) is not None


def extract_pastes_titles(content):
    these = ['/scraping', '/messages', '/settings']

    _tables = BeautifulSoup(content, 'html.parser',
                            parse_only=SoupStrainer('table'))
    for t in _tables.find_all():
        if has_attr(t, 'class'):
            content = str(t)
            break

    _hrefs = BeautifulSoup(content, 'html.parser',
                           parse_only=SoupStrainer('a'))
    hrefs = [i.get('href') for i in _hrefs.find_all() if has_attr(i, 'href')]
    hrefs = [i for i in hrefs if len(i) == 9 and i[1:].isalnum()]
    hrefs = [i for i in hrefs if not_these(i, these=these)]

    pastes_titles = [[i['href'].strip('/'), i.text] for i in _hrefs.find_all()
                     if has_attr(i, 'href') and i['href'] in hrefs]
    return pastes_titles


def extract_user_row_info(table_row):
    _tds = BeautifulSoup(str(table_row), 'html.parser',
                         parse_only=SoupStrainer('td'))
    # NAME / TITLE  ADDED   EXPIRES HITS    SYNTAX
    tds = [i for i in _tds]
    if len(_tds) != 6:
        return None

    _hrefs = BeautifulSoup(str(tds[0]), 'html.parser',
                           parse_only=SoupStrainer('a')).find_all()
    paste = _hrefs[0]['href'].lstrip('/')
    title = _hrefs[0].text

    date = extract_date_user_page(tds[1].text)
    unixts = date_to_timestamp(date)
    expiration = tds[2].text
    hits = tds[3].text
    syntax = tds[4].text
    return {'paste_key': paste, 'title': title,
            'paste': URL+'/'+paste, 'timestamp': date,
            'hits': hits, 'syntax': syntax,
            'unix': unixts, 'expiration': expiration}


def extract_user_pastes_titles_date(content):

    _tables = BeautifulSoup(content, 'html.parser',
                            parse_only=SoupStrainer('table'))
    for t in _tables.find_all():
        if has_attr(t, 'class'):
            content = str(t)
            break

    _trs = BeautifulSoup(content, 'html.parser',
                         parse_only=SoupStrainer('tr'))
    results = []
    for tr in _trs:
        if 'class' in tr:
            continue
        r = extract_user_row_info(tr)
        if r is not None:
            results.append(r)

    return results


def extract_pages(content):
    _divs = BeautifulSoup(content, 'html.parser',
                          parse_only=SoupStrainer('div')).find_all()

    pagination = [i for i in _divs if 'class' in i.attrs and
                  'pagination' in i['class']]

    if len(pagination) == 0:
        return -1

    _hrefs = BeautifulSoup(str(pagination), 'html.parser',
                           parse_only=SoupStrainer('a')).find_all()

    pages = [1]
    for h in _hrefs:
        if h.text is None:
            continue

        if h.text.isdigit():
            pages.append(int(h.text))

    return max(pages)
