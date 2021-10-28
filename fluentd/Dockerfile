FROM fluent/fluentd:v1.14-1

USER root

RUN ["gem", "install", "fluent-plugin-elasticsearch", "--no-document", "--version", "5.1.1"]

USER fluent
