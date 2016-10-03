#!/usr/bin/env python

"""
Sends out mailings.
"""

from __future__ import absolute_import
from __future__ import print_function

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import charset
import os
import random
import sys
import time
import datetime
import smtplib
import sqlite3

from bs4 import BeautifulSoup




DATADIR = '/your/spearfish/repo-directory/'
USER_EMAIL = 'your@yourdomain.com'
USER_NAME = 'yourname'
DATABASE = 'Source/spearphish.db'
LOGFILE = 'Logs/logfile.txt'

charset.add_charset('utf-8', charset.SHORTEST, charset.QP, 'utf-8')

def pull():
    """
    Make sure that the repo is up to date first.
    """
    try:
        os.chdir(ROOTDIR)
        print('[*] Making sure the database is up to date first (pulling repo changes)')
        os.system("git pull")
    except OSError:
        print('[-] Could not switch to {0}'.format(ROOTDIR))
        sys.exit(-1)

 
def commit(files, commit):
    """
    Commit the changed database to the repo
    """
    os.chdir(ROOTDIR)
    for filename in files:
        os.system("git add {0}".format(filename))
    os.system("git commit -c user.email='{0}' -c user.name='{1}' -m '{2}'".format(USER_EMAIL, USER_NAME, commit))
    os.system("git config --global push.default simple")
    os.system("git push -q")
    print('[+] Repo updated server-side. Don\'t forget to pull changes')


def sendall(sender, subject, text, html, usergroup, pretext):
    """
    Sends mail.
    Returns unique mailing ID
    """
    sent_mails = []
    mailing_id = random.randint(1, 100000000)
    try:
        conn = sqlite3.connect(ROOTDIR + DATABASE)
        cursor = conn.cursor()
        cursor.execute('select name, mail, md5sum from user where usergroup=?', (usergroup,))
        rows = cursor.fetchall()
        sendtime = datetime.datetime.utcnow().replace(microsecond=0).isoformat(' ')
        print('[+] sending mail to group {0} with pretext {1} and id {2}, subject {3}'.format(usergroup, pretext, mailing_id, subject.encode("ascii", "ignore")))
        for row in rows:
            recipient_name = row[0]
            recipient = row[1]
            md5sum = row[2]
            mail_html = html.replace('__victim__', md5sum.encode('ascii'))
            mail_html = mail_html.replace('__victim-name__', recipient_name.encode('utf-8'))
            mail_html = mail_html.replace('__ID__', str(mailing_id))
            mail_html = mail_html.replace('__pretext__', pretext.encode('ascii'))
            mail_text = text.replace('__victim__', md5sum.encode('ascii'))
            mail_text = mail_text.replace('__victim-name__', recipient_name.encode('ascii'))
            mail_text = mail_text.replace('__ID__', str(mailing_id))
            mail_text = mail_text.replace('__pretext__', pretext.encode('ascii'))
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient
            part1 = MIMEText(mail_text, 'plain', _charset='utf-8')
            part2 = MIMEText(mail_html, 'html', _charset='utf-8')
            msg.attach(part1)
            msg.attach(part2)
            s = smtplib.SMTP('localhost')
            s.sendmail(sender, recipient, msg.as_string())
            sent_mails.append((recipient, md5sum, pretext, int(time.time()), sender, mailing_id))
            print('[+] Sent mail to {0} ({1})'.format(recipient_name, recipient))
        add = conn.cursor()
        add.executemany('INSERT INTO `sent` (`recipient`,`md5sum`,`pretext`,`datestamp`,`sender`,`mailing_id`) VALUES (?, ?, ?, ?, ?, ?);', sent_mails)
        add.execute('INSERT INTO `mailing` (`mailing_id`,`usergroup`, `pretext`, `timestamp`) VALUES (?, ?, ?, ?);', (mailing_id, usergroup, pretext, sendtime))
        conn.commit()
    finally:
        conn.close()
    return mailing_id


if len(sys.argv) < 3:
    print("usage: pretextname sender filewithrecipients")
    print("example: hubot sendspearphish test test@radical.sexy usergroup")
    exit(0)

print("[+] Hey, ho, let's GO!\n")

#try:

#get the parameter

pretext = sys.argv[1]
sender = sys.argv[2]
usergroup = sys.argv[3]

#sendall(sender,name,"subjectabc",usergroup)

html = open('{0}pretexts/{1}.html'.format(ROOTDIR, pretext)).read()
text = open('{0}pretexts/{1}.txt'.format(ROOTDIR, pretext)).read()
subject = BeautifulSoup(html, "html.parser").title.string.strip()


pull()
mailing_id = sendall(sender, subject, text, html, usergroup, pretext)
commit([LOGFILE, DATABASE], 'sent {0} with ID {1} to {2}'.format(pretext, mailing_id, usergroup))

#except:

#    print "[-] something went wrong"
