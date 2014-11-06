#!./bin/python

import email
import imaplib
import os
import re
from email import policy
from email.parser import Parser
from html.parser import HTMLParser

imap_host = "mail.layerzero.ca"
imap_user = "debug@ariens.ca"
imap_pass = os.environ['DEBUG_MAIL_PASSWORD']
imap_box = "Inbox"
detach_dir = "/home/dave/python_hacking/imap/detach"


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def prepare_html_msg(html):
    return html
    html = re.sub(r'(?i)<br[^>]*>', "\n\n", html)
    html = re.sub(r'(?i)<style>.*</style>', r'', html)
    html = strip_tags(html)
    html = re.sub(r'^\s+', r'', html)
    html = re.sub(r'\s+$', r'', html)
    #html = re.sub("\n\n", "<br/><br/>", html)
    return html

try:
    server = imaplib.IMAP4_SSL(imap_host)
    server.login(imap_user, imap_pass)
    server.select(mailbox=imap_box, readonly=False)
    response, unread_mail = server.search(None, ('SEEN'))
    print("type: {}, num_messages: {}".format(response, unread_mail))

    for mail_id in unread_mail[0].split():
        print("-----------------------------------------------------------------------------------------")
        typ, mail_parts = server.fetch(mail_id, '(RFC822)')
        mail_body = mail_parts[0][1]
        mail = email.message_from_string(mail_body.decode('UTF8'))
        msg = Parser(policy=policy.default).parsestr(mail_body.decode('UTF8'))
        simplest = msg.get_body(preferencelist=('text', 'plain', 'html'))
        richest = msg.get_body()

        print('To:', mail['to'])
        print('From:', mail['from'])
        print('Subject:', mail['subject'])

        if richest['content-type'].maintype == 'text':
            if richest['content-type'].subtype == 'plain':
                for line in richest.get_content().splitlines():
                    print(line)
            elif richest['content-type'].subtype == 'html':
                print(prepare_html_msg(richest.get_content()))

        for part in mail.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()
            if bool(file_name):
                filePath = os.path.join(detach_dir, 'attachments', file_name)
                if not os.path.isfile(filePath):
                    print(file_name)
                    fp = open(filePath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()

except imaplib.IMAP4.error as error:
    print("error: ")



