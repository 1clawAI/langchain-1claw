# LangChain official integration — next steps

`langchain-1claw` v0.1.0 is live on PyPI. LangChain no longer accepts integration code in `langchain-ai/langchain` or `langchain-community` (sunset May 2026). The current process is **standalone PyPI package + docs listing PR**.

Official references (2025/2026):

- [Contributing integrations](https://docs.langchain.com/oss/python/contributing/integrations-langchain)
- [Publish an integration](https://docs.langchain.com/oss/python/contributing/publish-langchain)
- [Implement a LangChain integration](https://docs.langchain.com/oss/python/contributing/implement-langchain)
- Docs repo listing file: [`scripts/data/integration_external_docs.yaml`](https://github.com/langchain-ai/docs/blob/main/scripts/data/integration_external_docs.yaml)

## What we already have

| Requirement | Status |
|-------------|--------|
| Standalone PyPI package (`langchain-1claw`) | Done — [pypi.org/project/langchain-1claw](https://pypi.org/project/langchain-1claw/) |
| Own GitHub repo (`1clawAI/langchain-1claw`) | Done |
| MIT license | Done |
| LangChain component(s) (`BaseTool`, etc.) | Done — tools in `src/langchain_1claw/tools/` |
| Partner docs | Done — [docs.1claw.xyz/docs/integrations/langchain](https://docs.1claw.xyz/docs/integrations/langchain) |
| CI + trusted publishing on tag | Done — `.github/workflows/ci.yml` |

## Recommended listing path (under 50k monthly downloads)

Most integrations are listed via YAML only — **no hosted MDX page**.

1. **Optional but recommended:** add LangChain [standard tests](https://docs.langchain.com/oss/python/contributing/standard-tests-langchain) for tool integrations (`langchain-tests` dev dependency + subclass `IntegrationTests`).
2. **Open a PR to [langchain-ai/docs](https://github.com/langchain-ai/docs)** (not the main `langchain` repo):
   - Fork `langchain-ai/docs` under a personal account.
   - Add a row to `scripts/data/integration_external_docs.yaml` for **Tools / toolkits**.
   - Suggested fields:
     - **name:** `1Claw` (or `langchain-1claw`)
     - **package:** `langchain-1claw`
     - **docs_url:** `https://docs.1claw.xyz/docs/integrations/langchain` (partner docs preferred over PyPI)
     - **repo_url:** `https://github.com/1clawAI/langchain-1claw`
   - Follow their docs style guide; keep the PR documentation-only.
3. **Wait for maintainer review** — they may request changes to README, API surface, or test coverage.

## Hosted guide path (50k+ monthly downloads or featured)

Only pursue after sustained download volume or explicit maintainer invite:

- Copy a template from `src/oss/python/integrations/tools/TEMPLATE.mdx` in the docs repo.
- Add a page under `src/oss/python/integrations/tools/`.
- Requires functional code examples and frontmatter.

## Not in scope for LangChain listing

Per LangChain guidance, avoid submitting as:

- Document loaders, key-value stores, callbacks, or legacy text-completion LLMs.
- Code PRs to `langchain`, `langchain-community`, or `langchain-core`.

## Manual checklist before opening the docs PR

- [ ] README install snippet matches PyPI (`pip install langchain-1claw`).
- [ ] Example in `examples/` runs against production or documented mock mode.
- [ ] Version badge in README tracks PyPI.
- [ ] Contact email `ops@1claw.co` in `pyproject.toml` authors.
- [ ] Confirm `langchain-core` version bounds match current LangChain releases.

## Co-marketing (optional)

After listing merges, consider [LangChain co-marketing](https://docs.langchain.com/oss/python/contributing/comarketing) — blog post, integration spotlight, or joint webinar.
