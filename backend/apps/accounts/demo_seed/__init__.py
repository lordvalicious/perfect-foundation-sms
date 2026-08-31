"""Demo data seeding for the "OpenCode — Demo Data part 1-5" exercise.

Every module in this package creates idempotent, DEMO-EDU-scoped records.
Nothing here touches other schools and no command in this package executes
against production without an explicit ``--allow-prod`` flag (enforced by the
``seed_demo_data`` management command).
"""