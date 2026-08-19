# Claude Code — Read AGENTS.md First

**AGENTS.md in this repo is binding and MUST be followed for every task.** It contains the
design system rules, page structure conventions, data-file protections, and git discipline
required to keep paperchase.online working.

Key rules in short:
- Never blanket-sync files from a workspace copy; never force-push; never hand-edit generated data.
- Use ONLY the design tokens/classes from `assets/design-system.css` — no inline `<style>`,
  no hardcoded hex colors, no second visual theme (including on blog pages).
- Reuse the standard topbar/container/footer structure on every page.
- Run `npm run test` before pushing.
