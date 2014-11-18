#!./python3.4/bin/python

import shutil
import os
import argparse

from PIL import Image
from datetime import datetime

from app import db
from app.article_models import Article
from app.article_models import ArticleImageAttachment
from app.user_models import UserEmailAddress
from app.user_models import User


def post_new_article(email_address, title):
    print(email_address)
    email = UserEmailAddress.query.filter_by(email_address=email_address).first()
    user = User.query.filter_by(id=email.user_id).first()
    print("found the user => id: {}, email: {}".format(user.id, email.email_address))
    article = Article()
    article.user_id = user.id
    article.user = user
    article.date_posted = datetime.utcnow()
    article.title = title
    db.session.add(article)
    db.session.commit()
    print("*** successfully posted new article: id={} ***".format(article.id))
    return article


parser = argparse.ArgumentParser(description='Post an article with local filesystem attachments')
parser.add_argument("email", type=str, help="The email address of the poster")
parser.add_argument("title", type=str, help="The title of the article to post")
parser.add_argument("files", metavar='file', type=str, nargs='+', help="The file to attach to the article")
args = parser.parse_args()
article = post_new_article(args.email, args.title);

detach_dir = os.path.abspath(os.path.dirname(__file__)) + '/app/static/article_attachments'

for file in args.files:
    directory, file_name = os.path.split(file)
    file_name = "{}_{}_{}".format(article.id, datetime.utcnow().timestamp(), file_name)
    file_path = os.path.join(detach_dir, file_name)
    print("file {} file_path {}".format(file, file_path))
    shutil.copy2(file, file_path)

    attachment = ArticleImageAttachment()
    attachment.article_id = article.id
    attachment.file_name = file_name

    thumb_name = "thumb_{}".format(file_name)
    thumb_path = os.path.join(detach_dir, thumb_name)
    im = Image.open(file_path)
    im.thumbnail((400, 400))
    im.thumbnail((200, 200), Image.ANTIALIAS)
    im.save(thumb_path)
    attachment.thumb_name = thumb_name

    db.session.add(attachment)
    db.session.commit()
    print("There was an attached file: {}".format(file_name))


