FROM docker.gitea.com/gitea-mcp-server:1.8.0 AS upstream

FROM alpine:3.24.1

RUN apk add --no-cache ca-certificates jq python3

COPY --from=upstream /app/gitea-mcp /usr/local/bin/gitea-mcp
COPY run.sh /run.sh
COPY mcp_bridge.py /usr/local/lib/gitea-mcp-bridge.py

RUN chmod 0755 /usr/local/bin/gitea-mcp /run.sh

EXPOSE 8080

ENTRYPOINT ["/run.sh"]
