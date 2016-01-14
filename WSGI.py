#!python/bin/python

# invoked via run.sh 

#from werkzeug.debug import DebuggedApplication

from app import app
if __name__ == "__main__":
    #app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
    #app.run(host='localhost', debug=True)
    app.run(host='localhost')
