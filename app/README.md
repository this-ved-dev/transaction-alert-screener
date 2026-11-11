# app/

Django 5 + HTMX + Tailwind. Created by TRA-34 (Natalie). Planned apps: `accounts` (three roles), `alerts`,
`rules_admin` (maker-checker console), `audit`, `exports`, `agent`, `customers`, `evaluation`.
The alert detail template includes `rules/<id>_<slug>/evidence.html` once per hit; see docs/05-architecture.md.
`/healthz` must return 200 for the Docker healthcheck and the CI compose smoke.
