#!python3.4/bin/python

# Deprecated when running via uwsgi and nginx

from app import app
if __name__ == "__main__":
    app.run(host='localhost', debug=True)
