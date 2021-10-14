import logging
from prophet import prophet_listener

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

e = prophet_listener.Prophet()
#try:
#    e.start()
#except KeyboardInterrupt:
#    e.stop()
e.start()
while True:
	pass
