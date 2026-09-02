ARG BUILD_ARCH=amd64
ARG UPSTREAM_VERSION=7.0.14
FROM ghcr.io/homeassistant-apps/cloudflared/${BUILD_ARCH}:${UPSTREAM_VERSION}

USER root

ARG BUILD_ARCH=amd64
ARG CLOUDFLARED_VERSION=2026.8.3

# Keep the latest released Home Assistant Cloudflared app as the integration
# base, while updating the cloudflared binary to the current upstream release.
RUN apk add --no-cache nginx \
    && case "${BUILD_ARCH}" in aarch64) cloudflared_arch="arm64" ;; *) cloudflared_arch="${BUILD_ARCH}" ;; esac \
    && wget -q -O /usr/bin/cloudflared "https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-${cloudflared_arch}" \
    && chmod 0755 /usr/bin/cloudflared \
    && mv /etc/s6-overlay/s6-rc.d/prepare/run.sh /etc/s6-overlay/s6-rc.d/prepare/run-upstream.sh \
    && mv /run.sh /run-upstream.sh

COPY rootfs /

RUN chmod 0755 \
    /etc/s6-overlay/s6-rc.d/prepare/run.sh \
    /run.sh

LABEL org.opencontainers.image.source="https://github.com/riederch/ha-apps" \
      org.opencontainers.image.description="Cloudflared Home Assistant app with per-host Basic/Bearer access protection"
