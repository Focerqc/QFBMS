# Public engineering dashboard

This is the static, read-only GitHub Pages edition of the local dashboards. It contains a dated progress snapshot, schematic PDF exports, part-choice notes, and a link to the repository's dashboard feedback issue form.

The local dashboards in `_tools/` still need KiCad and a local Python server. They are not exposed by this site. To refresh the hosted snapshot, update this page and its PDF exports deliberately, then merge the changes to `main`. The Pages workflow runs only when `site/**` changes on `main`, or when manually started from GitHub Actions; routine hardware commits do not publish a new site build.

## Publish

1. In the repository's **Settings → Pages**, set the build and deployment source to **GitHub Actions**.
2. Merge the site files to `main` or run **Publish engineering dashboard** from the Actions tab.
3. GitHub Pages will show the published URL in the workflow deployment summary. For a project site, it will normally be `https://focerqc.github.io/QFBMS/`.

The feedback link opens a GitHub issue form. Submitters need a GitHub account. The repository must have Issues enabled.

The public page contains expandable part notes, review priorities and PDF downloads. Interactive Board Boxes selection and prompt generation remain in the local KiCad dashboard; reviewers can submit general feedback without generating a placement prompt.

## Refresh schematic PDFs

Using KiCad 10, export from the intended checkout and replace the files in `files/`:

```powershell
kicad-cli sch export pdf --output site/files/main-schematic-draft.pdf qfbms32.kicad_sch
kicad-cli sch export pdf --output site/files/monitor-schematic-draft.pdf qfbms32-bq-monitors.kicad_sch
```

The PDFs are for review convenience. The page labels the main and separate monitor projects as drafts because they are not reconciled into a verified system schematic.

When refreshing, update the visible snapshot date, source revision and pinned evidence links together. Refresh `files/snapshot.json` with the full source commit, SHA-256 of each schematic source and PDF, and PDF page counts. The initial snapshot at `41740fd` contains one main schematic page and five monitor-project pages. Review current evidence before updating part statuses; historical decisions may have been superseded.
