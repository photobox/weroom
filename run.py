from application import app
import logging, sys
app.logger.setLevel(logging.DEBUG)

if 'test' in sys.argv:
    app.run(debug=True)
else:
    app.run(host='0.0.0.0', ssl_context=('cert.pem','key.pem'))
