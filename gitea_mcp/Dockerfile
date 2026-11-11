FROM docker.gitea.com/gitea-mcp-server:1.11.0 AS upstream

FROM alpine:3.24.1

RUN apk add --no-cache ca-certificates jq python3

COPY --from=upstream /app/gitea-mcp /usr/local/bin/gitea-mcp
COPY run.sh /run.sh
COPY mcp_bridge.py /usr/local/lib/gitea-mcp-bridge.py
COPY binary_upload.py /usr/local/lib/binary_upload.py

RUN chmod 0755 /usr/local/bin/gitea-mcp /run.sh

# Assert that the pinned official binary still supports the transport and
# authorization flags used by run.sh. Buildx runs this on both architectures.
RUN set -eu; \
    /usr/local/bin/gitea-mcp --help >/tmp/gitea-mcp-help.txt 2>&1; \
    for flag in --host --port --read-only; do \
        grep -q -- "$flag" /tmp/gitea-mcp-help.txt; \
    done; \
    rm -f /tmp/gitea-mcp-help.txt

EXPOSE 8080

ENTRYPOINT ["/run.sh"]
