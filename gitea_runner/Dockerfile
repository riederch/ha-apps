FROM docker.io/gitea/runner:5.4.1

USER root

ARG BUILD_VERSION=5.4.1-rch1
ARG BUILD_ARCH=amd64

RUN apk add --no-cache bash ca-certificates git jq python3 tini

# Detect upstream CLI flag drift during the multi-arch image build, before
# upgrading a runner that already owns persistent registration data.
RUN set -eu; \
    gitea-runner register --help >/tmp/runner-register-help.txt; \
    for flag in --no-interactive --instance --token-file --name --labels; do \
        grep -q -- "$flag" /tmp/runner-register-help.txt; \
    done; \
    gitea-runner daemon --help >/tmp/runner-daemon-help.txt; \
    grep -q -- '--labels' /tmp/runner-daemon-help.txt; \
    rm -f /tmp/runner-register-help.txt /tmp/runner-daemon-help.txt

COPY run.sh /run-ha.sh
COPY clean-env.sh /clean-env.sh
RUN chmod 0755 /run-ha.sh /clean-env.sh

WORKDIR /data

LABEL io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.source="https://github.com/riederch/ha-apps" \
      org.opencontainers.image.description="Home Assistant wrapper for Gitea Runner 5.4.1"

ENTRYPOINT ["/clean-env.sh", "/sbin/tini", "--", "/run-ha.sh"]
