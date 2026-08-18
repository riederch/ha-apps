FROM golang:1.25-alpine AS builder

RUN apk add --no-cache git python3
WORKDIR /src
RUN git clone --depth 1 https://github.com/cnjack/gitea-mcp.git .
COPY patch_binary_upload.py /tmp/patch_binary_upload.py
RUN python3 /tmp/patch_binary_upload.py
RUN CGO_ENABLED=0 go build -o /out/gitea-mcp .

FROM alpine:3.21

RUN apk add --no-cache ca-certificates jq

COPY --from=builder /out/gitea-mcp /usr/local/bin/gitea-mcp
COPY run.sh /run.sh

RUN chmod 0755 /usr/local/bin/gitea-mcp /run.sh

EXPOSE 8080

ENTRYPOINT ["/run.sh"]
