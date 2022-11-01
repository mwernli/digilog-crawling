FROM flyway/flyway:8.0.0 AS dev

ENTRYPOINT ["sh", "-c"]
CMD ["flyway \
-url=jdbc:postgresql://${POSTGRES_SERVICE_HOST}:${POSTGRES_SERVICE_PORT}/ \
-user=${POSTGRES_USER} \
-password=${POSTGRES_PASSWORD} \
-schemas=${POSTGRES_DB} \
-baselineOnMigrate=true \
migrate \
-ignoreIgnoredMigrations=true"]

FROM dev AS packaged

COPY ./flywaymigrations/ /flyway/sql
