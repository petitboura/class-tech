> [English version] · [Français](./README.fr.md)

# Live Tracking (Public Page)

Web page that displays project documentation for the public: it reads files live from the GitHub main branch and refreshes itself every 5 hours.

- Page: https://petitboura.github.io/class-tech/
- Repository read: petitboura/class-tech, main branch
- Refresh: every 5 hours (see `config.js`, `refreshMinutes`), and when returning to the tab if the interval has elapsed. "Last updated" shows the date and time of the last successful load, plus the countdown to the next one.

## Two views

Normal / Technical switch at the top of the page (Normal by default), same background, two levels of detail.

Normal: Home (status + hackathon context), Journal (progress grouped by hour, collapsed, newest or oldest first, plus the full journal), Bourama's Notes (empty until Bourama dictates something), Comments (visitor feedback, no account, with replies), Review, Decisions, Steps and documents, Context.

Technical: Home, Commits (latest commits on main, live), Tools (live registry: total, by tier, with a note when confirmation is required), Tests (totals quoted in the journal + test files on main), Architecture, Journal, Steps and documents, Comments.

Hourly grouping displays every time slot, including empty ones ("Nothing yet"), without ever skipping an hour.

## Files

- `index.html`: structure, Open Graph tags, script loading.
- `config.js`: the only place containing the repository, branch, document list, refresh interval, and hackathon context. Nothing else is hardcoded.
- `app.js`: document loading, navigation, views, rerendering.
- `md.js`: small custom Markdown renderer (headings, lists, tables, code, links). Tested against the real documents (see below).
- `progression.js`: groups the journal by hour.
- `technique.js`: reads the tool registry and test totals quoted in the journal.
- `commentaires-config.js`: Supabase address, public key, and comments table name. The only file to fill in.
- `commentaires.js`: list, indented replies, submission forms, loading and error states.
- `styles.css`: theme adapted from Classinus (gold tones, light and dark modes follow the phone).
- `favicon.svg`, `apercu.jpg`: icon and share-preview image.

## Comments

Comments section in both views, no account required (name optional, blank = Anonymous). Moderation is done by deleting entries in the Supabase dashboard (table `suivi_commentaires`); nothing needs to be coded on the page.

## Checks before making changes

- `node C:\Users\dell\suivi-live-test\verifier.js` checks rendering, grouping, and registry against the real documents.
- `node C:\Users\dell\suivi-live-test\tirets.js` checks that no displayed text contains a bare `--` or an em dash.
- `node C:\Users\dell\suivi-live-test\live.js` replays the exact live path (raw files + GitHub API). These probes live outside the repository and are not delivered.
- Displayed text: never use `--` or an em dash; use simple French.

## Deployment

The page is served by GitHub Pages from the `gh-pages` branch (root = contents of this directory). To republish after a change: commit this directory to main, then push the subtree to `gh-pages` (see command history in the 28/10/2026 session).