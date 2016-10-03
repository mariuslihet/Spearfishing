#!/usr/bin/env python

import base64
import logging
import os
import sys
import urllib
import re

from bs4 import BeautifulSoup
import cssutils
import requests

DATADIR = '/your/spearfish/repo-directory/'
USER_EMAIL = 'your@yourdomain.com'
USER_NAME = 'yourname'

def pull():
    """
    Make sure that the repo is up to date first.
    """
    try:
        os.chdir(DATADIR)
        print('[*] Updating the repo')
        os.system("git pull 1>/dev/null")
    except OSError:
        print('[-] Could not switch to {0}'.format(DATADIR))
        sys.exit(-1)


def commit(pretext):
    """
    Commit the changed database to the repo
    """
    os.chdir(DATADIR)
    os.system("git add pretexts/{0}.* 1>/dev/null".format(pretext))
    os.system("git add Logs/logfile.txt 1>/dev/null")
    os.system("git commit -c user.email='{0}' -c user.name='{1}' -m 'added pretexts for {2}'".format(USER_EMAIL, USER_NAME, pretext))
    os.system("git config --global push.default simple")
    os.system("git push -q")
    print('[+] Repo updated with {0} pretexts. Don\'t forget to pull changes'.format(pretext))

#Replace a CSS @import directive with the contents of its target
def cssreplace(im):
    url = im.groups()[1].strip('"')
    if url.startswith('//'):
        url = 'http:' + url
    r = requests.get(url)
    if (200 == r.status_code or '' == r.content):
        #Lookup worked, return the content
        print "- imported css from " + url
        return r.content
    else:
        #Lookup failed, return the original string unchanged
        print '- content fetch failed from ' + url
        return im.groups()[0]

if len(sys.argv) < 2:
    print "usage: hubot shellcmd randomintcreatepretext name url [options]"
    print('options: inline        - Inline images')
    print('         noinlinetrack - Don\'t inline images but rewrite link')
    print('         nobeacon      - Don\'t add a beacon background image')
    print('         sourcefile    - Read the content from an existing pretext file instead of the URL (URL is still used as base)')
    print('         unwraplinks   - Check if links hit a redirector, and if so, use the target URLs (good for "depersonalising" existing messages)')
    print('         nocommit      - Don\'t `git pull` before or `git commit` after running')
    print "example: hubot shellcmd randomintcreatepretext test https://www.test.de"
    exit(0)
print "ROS - Radically Open Spearphishing v0.2"

#get parameters
name = sys.argv[1]
url = sys.argv[2]
options = []
if len(sys.argv) > 3:
    options = sys.argv[3:]

print "[+] Enough params, getting pretext"
if 'nocommit' not in options:
    pull()

content = ''
if 'sourcefile' in options:
    print '- reading content from ' + '{0}pretexts/{1}.html'.format(DATADIR, name)
    with open('{0}pretexts/{1}.html'.format(DATADIR, name), 'r') as f:
        content = f.read()
else:
    print '- fetching content from ' + url
    r = requests.get(url)
    content = r.text

soup = BeautifulSoup(content, "html.parser")
# Each pretext should have its own random ID - to differentiate between mailings
#critical is enough
cssutils.log.setLevel(logging.CRITICAL)

#Insert a beacon image
if 'nobeacon' not in options:
    try:
        soup.find("body")["background"] = "http://your-trackingdomain.com/images/?m=__ID__&v=__victim__"
    except:
        pass

print "[+] removing Javascript"
for tag in soup("script"):
    tag.decompose()
REMOVE_ATTRS = [
    'onblur', 'onchange', 'onclick', 'ondblclick', 'onfocus',
    'onkeydown', 'onkeypress', 'onkeyup', 'onload', 'onmousedown',
    'onmousemove', 'onmouseout', 'onmouseover', 'onmouseup',
    'onreset', 'onselect', 'onsubmit', 'onunload'
]
for tag in soup():
    for attribute in REMOVE_ATTRS:
        del tag[attribute]

print "[+] replacing links"
for link in soup.find_all('a'):
    try:
        if not link.has_attr("href"):
            link["href"] = "http://your-trackingdomain.com/track/?m=__ID__&v=__victim__&to={0}".format(urllib.quote(url))
            continue
        if "http://your-trackingdomain.com" in link["href"]:
            #Ignore links we've already rewritten
            continue
        if "http" in link["href"]:
            if 'unwraplinks' in options:
                #If the link does a redirect, grab the target URL (1 layer only)
                r = requests.head(link.get("href"), allow_redirects=False)
                if ((r.status_code == 301 or r.status_code == 302) and "location" in r.headers):
                    link["href"] = r.headers["location"]
            link["href"] = "http://your-trackingdomain.com/track/?m=__ID__&v=__victim__&to={0}".format(urllib.quote(link.get("href")))
            continue
        elif "www" in link["href"]:
            link["href"] = "http://your-trackingdomain.com/track/?m=__ID__&v=__victim__&to=http://{0}".format(urllib.quote(link.get("href")))
        else:
            link["href"] = "http://your-trackingdomain.com/track/?m=__ID__&v=__victim__&to={0}".format(urllib.quote(url+link.get("href")))
            continue
    except Exception as ex:
        print('[-] error in link replacement of {0} ({1})'.format(link.get['href'], ex))


if 'inline' in options:
    print "[+] Inlining images"
    for images in soup.find_all("img", src=True):
        try:
            if "http" in images["src"]:
                images["src"] = "data:image/png;base64," + base64.b64encode(requests.get(images["src"]).content)
            else:
                images["src"] = "data:image/png;base64," + base64.b64encode(requests.get(url+images["src"]).content)
        except Exception as ex:
            print('[-] error in image replacement of {0} ({1})'.format(images['src'], ex))


if 'noinlinetrack' in options:
    for images in soup.find_all("img", src=True):
        try:
            if "://" in images["src"]:
                images['src'] = 'http://your-trackingdomain.com/images/?m=__ID__&v=__victim__&to={0}'.format(urllib.quote(images['src']))
            else:
                images["src"] = 'http://your-trackingdomain.com/images/?m=__ID__&v=__victim__&to={0}'.format(urllib.quote(url + images['src']))
        except Exception as ex:
            print('[-] error in replacing of {0} ({1})'.format(images['src'], ex))


print "[+] inline css"
for csslink in soup.find_all('link', rel='stylesheet'):
    try:
        if '://' in csslink.get('href'):
            css = requests.get(csslink.get('href'))
        else:
            css = requests.get(url + csslink.get('href'))
        if css.headers['Content-Type'] == "text/css":
            sheet = cssutils.parseString(css.text.encode("utf-8"))
            newcss = soup.new_tag("style")
            newcss.string = sheet.cssText
            soup.head.insert(0, newcss)
            print "- parsed " + csslink.get('href')
    except Exception as ex:
        print('[-] error in css replacement of {0} ({1})'.format(csslink.get('href'), ex))
#Also inline CSS imports
for css in soup.find_all('style'):
    try:
        #This pattern should probably be looser
        css.string = re.sub(r'(@import url\((.*)\);)', cssreplace, css.string)
    except Exception as ex:
        pass

open('{0}pretexts/{1}.html'.format(DATADIR, name), "w").write(soup.prettify().encode("utf-8"))

text = "Your email program can't read this newsletter. To view the newsletter online go to:\n\n{0}\n\n Click on the following link if you don't want to receive this newsletter anymore:\n 
http://__pretext__.us10.list-manage.com/unsubscribe?u=__victim__&id=__ID__".format(url)
open('{0}pretexts/{1}.txt'.format(DATADIR, name), "w").write(text)
open('{0}pretexts/{1}.from'.format(DATADIR, name), "w").write('nobody@example.com')

subject = BeautifulSoup(soup.prettify().encode("utf-8"), "html.parser").title.string
open('{0}pretexts/{1}.subject'.format(DATADIR, name), "w").write(subject)

if 'nocommit' not in options:
    commit(name)
