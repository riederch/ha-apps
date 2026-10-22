ARG BUILD_ARCH=amd64
ARG UPSTREAM_VERSION=7.0.19
FROM ghcr.io/homeassistant-apps/cloudflared/${BUILD_ARCH}:${UPSTREAM_VERSION}

USER root

ARG BUILD_ARCH=amd64
# Upstream app 7.0.19 already packages cloudflared 2026.10.3 with the
# certificate trust security fix. Avoid a second, unchecked binary download.
RUN apk add --no-cache nginx \
    && mv /etc/s6-overlay/s6-rc.d/prepare/run.sh /etc/s6-overlay/s6-rc.d/prepare/run-upstream.sh \
    && mv /run.sh /run-upstream.sh

COPY rootfs /

RUN chmod 0755 \
    /etc/s6-overlay/s6-rc.d/prepare/run.sh \
    /run.sh

LABEL org.opencontainers.image.source="https://github.com/riederch/ha-apps" \
      org.opencontainers.image.description="Cloudflared Home Assistant app with per-host Basic/Bearer access protection"
