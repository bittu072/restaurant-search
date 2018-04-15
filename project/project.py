from flask import Flask, render_template, request, redirect
from flask import session as login_session

import json
import os
import random
import string

app = Flask(__name__)


@app.route('/')
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    # always turn off debugging
    # when the application moves to production environment.
    app.debug = True
    # defines which port to use
    port = int(os.environ.get("PORT", 5000))
    # defines to consider host as localhost
    app.run(host='0.0.0.0', port=port)
