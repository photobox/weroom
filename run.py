from application import app
import logging
app.logger.setLevel(logging.DEBUG)
app.run(debug=True)
