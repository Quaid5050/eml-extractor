# eml-extractor

Turn `.eml` files into clean folders—headers, plain/HTML body, and attachments—ready for review, AI pipelines, or archiving.

**No install.** Python 3.9+ standard library only.

## Quick start

```bash
git clone <your-repo-url>
cd eml-extractor

# 1. Copy .eml files into input/
cp ~/Downloads/some-message.eml input/

# 2. Extract
make extract
# or: python3 extract.py
```

Each message becomes one folder under `output/`:

```
output/
  some-message/
    email.md               # headers + bodies (GitHub/IDE preview)
    email.html             # HTML body when present (open in browser)
    report.pdf             # attachments (same folder)
```

## Requirements

- Python **3.9+**
- Optional: `make` (convenience only)

## Commands

| Command | Description |
|---------|-------------|
| `make extract` | Process every `.eml` in `input/` |
| `make clean` | Delete generated files in `output/` |
| `make help` | Show targets |

Direct Python:

```bash
python3 extract.py                    # all files in input/
python3 extract.py path/to/one.eml    # specific file(s)
```

## What you get

### `email.md`

Markdown summary per message (renders nicely on GitHub and in VS Code):

- **Title** from Subject
- **Headers table:** Date, From, To, Cc, …
- **Plain text body** in a fenced block
- **HTML body:** saved as `email.html` for browser preview; raw HTML in a collapsible section in the `.md`
- **Attachment links**

### Attachments

Decoded and saved in the same folder (PDFs, images, etc.).

## Run summary

After each batch you see counts, for example:

```
SUCCESS quote-request.eml -> output/quote-request/
UPDATED follow-up.eml -> output/follow-up/

────────────────────────────────────────
Extract summary
  Total in batch:         2
  Success (new):          1
  Updated (re-extract):   1
  Skipped:                0
  Skipped (dup input):    0
  Failed:                 0
  Duplicate dirs removed: 0
────────────────────────────────────────
```

| Status | Meaning |
|--------|---------|
| **Success** | New output folder created |
| **Updated** | Same `.eml` name re-run; folder overwritten |
| **Skipped** | Not a file, wrong extension, or duplicate name in one batch |
| **Failed** | Parse/write error (see message above summary) |
| **Duplicate dirs removed** | Old `name_2`, `name_3` folders cleaned up |

Re-running the same `.eml` **does not** create `folder_2` copies—it refreshes the single folder.

## How to export `.eml` files

- **Gmail:** open message → ⋮ → **Download message**
- **Outlook:** drag message to desktop, or **File → Save As**
- **Apple Mail:** select message → **File → Save As…**
- **Thunderbird:** **File → Save As → File**

Save into `input/` then run `make extract`.

## Project layout

```
eml-extractor/
├── extract.py      # main script
├── Makefile
├── README.md
├── input/          # put .eml files here (gitignored)
└── output/         # generated (gitignored)
```

## Use cases

- Prep emails for **LLM / RAG** ingestion (`email.md` + files)
- **Quote intake** or support workflows with roof reports, PDFs, images
- **Bulk archive** exports from legal/compliance mail dumps
- Local inspection without opening a mail client

## Publishing this repo

`input/` and `output/` contents are **gitignored** so you can commit the tool without private mail. Only `.gitkeep` placeholders ship with the template.

## License

MIT — use freely; no warranty.
