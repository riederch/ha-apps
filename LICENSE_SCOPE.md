# Licensing scope

## Original local code

The independently authored code controlled by the maintainers of
`riederch/ha-apps`, including the Local EMS Home Assistant integration under
`custom_components/local_ems/` and its associated tests, is licensed under
the **GNU General Public License, version 3 or (at your option) any later
version** (`GPL-3.0-or-later`).

The complete license terms are provided in the root [LICENSE](LICENSE).
This license notice applies **only to parts for which the maintainers have
the right to grant that license**; it does not override other copyright
holders' licenses.

## Upstream components and independent programs

Some directories include copied, adapted, bundled, or independently
executed third-party works, including Home Assistant app wrappers and
external container/runtime images. These parts continue to be subject to
their respective upstream terms, copyright notices, and conditions,
as described in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

In particular, the documented MIT upstream notices for the Gitea app,
Gitea MCP, Gitea Runner, Vaultwarden app, and Cloudflared app remain in
force for any material to which they apply. Their notices must be retained
when those materials are redistributed. An external container image is
not relicensed by placing the integration in the same Git repository.

## Distributions

If redistributing a combined derivative work that includes GPL-covered
code and compatible third-party code, satisfy all applicable conditions
and retain original notices. Mere aggregation of separate programs in a
repository does not by itself change the license of each program.

This file clarifies the intended licensing scope; it does not modify the
text of the GNU GPL or grant rights in software owned by third parties.

## Embedded Power Flow Card Plus

The file `custom_components/local_ems/frontend/vendor/power-flow-card-plus-v0.4.0-beta.1.mjs`
contains third-party code from Power Flow Card Plus and retains its original
**MIT license**, Copyright (c) 2023-2026 flixlix. The bundled original
is not relicensed under the root GPL-3.0-or-later license.
The full original MIT text is in `custom_components/local_ems/frontend/vendor/LICENSE-PFCP`.
The upstream commit and changes are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
Our independently written wrapper (`local-ems-flow-card.mjs`),
adapter (`pfcp-adapter.mjs`), and Local EMS backend remain GPL-3.0-or-later.
