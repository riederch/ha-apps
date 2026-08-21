FROM docker.gitea.com/gitea-mcp-server:1.6.0 AS upstream

FROM alpine:3.24.1

RUN apk add --no-cache ca-certificates jq

COPY --from=upstream /app/gitea-mcp /usr/local/bin/gitea-mcp
COPY run.sh /run.sh

RUN chmod 0755 /usr/local/bin/gitea-mcp /run.sh

EXPOSE 8080

ENTRYPOINT ["/run.sh"]
