ARG BUILD_ARCH=amd64
ARG UPSTREAM_VERSION=7.0.13
FROM ghcr.io/homeassistant-apps/cloudflared/${BUILD_ARCH}:${UPSTREAM_VERSION}

USER root

# nginx is used only as a loopback-bound per-origin header injection proxy.
RUN apk add --no-cache nginx \
    && mv /etc/s6-overlay/s6-rc.d/prepare/run.sh /etc/s6-overlay/s6-rc.d/prepare/run-upstream.sh \
    && mv /run.sh /run-upstream.sh

COPY rootfs /

RUN chmod 0755 \
    /etc/s6-overlay/s6-rc.d/prepare/run.sh \
    /run.sh

LABEL org.opencontainers.image.source="https://github.com/riederch/ha-apps" \
      org.opencontainers.image.description="Cloudflared Home Assistant app with per-origin Basic/Bearer Authorization support"
