#!./python3.4/bin/python

import imaplib
import os
import re
import dkim
from PIL import Image


from html.parser import HTMLParser
from datetime import datetime

from email import policy
from email.utils import parsedate_to_datetime
from email.parser import Parser

from app import db
from app.article_models import Article
from app.article_models import ArticleAttachment
from app.user_models import UserEmailAddress
from app.user_models import User

imap_host = 'mail.layerzero.ca'
imap_user = 'debug@ariens.ca'
imap_pass = os.environ['DEBUG_MAIL_PASSWORD']
imap_box = 'Inbox'
detach_dir = '/srv/http/www/flask_apps/ariens_www/app/static/article_attachments'
allowed_publishers = ['dave@ariens.ca']
verify_dkim = True
imap_readonly = False

basedir = os.path.abspath(os.path.dirname(__file__)) + '/app/static/article_attachments'


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
    html = re.sub(r'(?i)<br[^>]*>', "\n\n", html)
    html = re.sub(r'(?i)<style>.*</style>', r'', html)
    html = strip_tags(html)
    html = re.sub(r'^\s+', r'', html)
    html = re.sub(r'\s+$', r'', html)
    html = re.sub("\n\n", "<br/><br/>", html)
    return html


def post_new_article(from_email, title, body, date):
    email = UserEmailAddress.query.filter_by(email_address=from_email).first()
    user = User.query.filter_by(id=email.user_id).first()
    print("found the user => id: {}, email: {}".format(user.id, email.email_address))
    article = Article()
    article.user_id = user.id
    article.user = user
    article.date_posted = parsedate_to_datetime(date)
    article.title = title
    article.body = body
    db.session.add(article)
    db.session.commit()
    print("*** successfully posted new article: id={} ***".format(article.id))
    return article


def save_attachment(part, attachment_name):
    file_name = "{}_{}_{}".format(article.id, datetime.utcnow().timestamp(), attachment_name)
    file_path = os.path.join(detach_dir, file_name)

    if not os.path.isfile(file_path):
        fp = open(file_path, 'wb')
        fp.write(part.get_payload(decode=True))
        fp.close()
        attachment = ArticleAttachment()
        attachment.article_id = article.id
        attachment.content_type = part.get_content_maintype()
        attachment.file_name = file_name
        if part.get_content_maintype() == "image":
            thumb_name = "thumb_{}".format(file_name)
            thumb_path = os.path.join(detach_dir, thumb_name)
            im = Image.open(file_path)
            im.thumbnail((200, 200))
            im.save(thumb_path)
            attachment.thumb_name = thumb_name

        db.session.add(attachment)
        db.session.commit()
        print("There was an attached file: {}".format(file_name))


try:
    server = imaplib.IMAP4_SSL(imap_host)
    server.login(imap_user, imap_pass)
    server.select(mailbox=imap_box, readonly=imap_readonly)
    response, unread_mail = server.search(None, ('UNSEEN'))
    print("type: {}, num_messages: {}".format(response, unread_mail))

    for mail_id in unread_mail[0].split():
        typ, mail_parts = server.fetch(mail_id, '(RFC822)')
        mail_body = mail_parts[0][1]
        msg = Parser(policy=policy.default).parsestr(mail_body.decode('UTF8'))
        simplest = msg.get_body(preferencelist=('text', 'plain', 'html'))
        richest = msg.get_body()

        if not msg['from'] in allowed_publishers:
            print("warning: ignoring message from {} with subject {}"
                  .format(msg['from'], msg['Subject']))
            continue

        if verify_dkim and not dkim.verify(mail_parts[0][1]):
            print("warning: ignoring non-DKIM verified mail from {} with subject {}"
                  .format(msg['from'], msg['Subject']))
            continue

        msg_body = None

        if richest['content-type'].maintype == 'text':
            if richest['content-type'].subtype == 'plain':
                msg_body = richest.get_content()
            elif richest['content-type'].subtype == 'html':
                msg_body = prepare_html_msg(richest.get_content())

        article = post_new_article(msg['From'], msg['Subject'], msg_body, msg['Date'])

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            if bool(part.get_filename()):
                save_attachment(part, part.get_filename())

except imaplib.IMAP4.error as error:
    print("error: ")



