import os

from api.project import app

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    # always turn off debugging
    # when the application moves to production environment.
    app.debug = True
    # defines which port to use
    port = int(os.environ.get("PORT", 5000))
    # defines to consider host as localhost
    app.run(host='0.0.0.0', port=port)
