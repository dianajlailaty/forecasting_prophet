import prophet_listener
import logging.config


def main():
	e = prophet_listener.Prophet()
	#try:
	#    e.start()
	#except KeyboardInterrupt:
	#    e.stop()
	e.start()
	while True:
		pass

if __name__ == '__main__':
	logging.config.fileConfig('/morphemic_project/logging.ini', disable_existing_loggers=False)
	main()

