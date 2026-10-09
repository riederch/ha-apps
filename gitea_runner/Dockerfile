FROM docker.io/gitea/runner:5.0.0

USER root

ARG BUILD_VERSION=5.0.0-rch1
ARG BUILD_ARCH=amd64

RUN apk add --no-cache bash ca-certificates git jq tini

COPY run.sh /run-ha.sh
RUN chmod 0755 /run-ha.sh

WORKDIR /data

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/riederch/ha-apps" \
      org.opencontainers.image.description="Home Assistant wrapper for Gitea Runner 5.0.0"

ENTRYPOINT ["/sbin/tini", "--", "/run-ha.sh"]
