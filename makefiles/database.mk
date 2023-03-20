DB ?= budgee
DB_CONTAINER ?= budgee_db
DB_USER ?= postgres
DOCKER ?= docker

psql:
	$(DOCKER) exec -it $(DB_CONTAINER) psql -U $(DB_USER) $(DB)

.PHONY: psql
