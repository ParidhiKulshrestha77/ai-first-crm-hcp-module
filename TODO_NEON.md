# Neon setup checklist (hcp-crm)

- [x] Add Neon-specific section to `hcp-crm/README.md`
- [x] Ensure `hcp-crm/backend/.env.example` exists and documents `DATABASE_URL` for Neon/Postgres
- [ ] Create/obtain Neon Postgres connection string
- [ ] Copy `hcp-crm/backend/.env.example` -> `hcp-crm/backend/.env`
- [ ] Set `GROQ_API_KEY` and `DATABASE_URL` to Neon connection string
- [ ] Run backend and verify `/api/health`
- [ ] Optionally run `POST /api/dev/seed` and check `/api/hcps`

