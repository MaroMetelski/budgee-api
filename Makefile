include makefiles/database.mk
include makefiles/server.mk

run: gunicorn

run-dev:
	make run FLASK_ENV=development
