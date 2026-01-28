# Project Cards

Generates 15cm x 10cm card images for Obsidian project notes.

## How it works

Scans the vault for files matching `⌬*.md`, extracts the first embedded image
from each note, and renders a card with the project image on the left and the
project title on the right.

## Config keys

| Key | Description |
|---|---|
| `vault_path` | Root path of the Obsidian vault |
| `vault_media_path` | Path to the vault media/attachments folder |
| `project_cards_output_folder` | Output directory for card PNGs (default: `output/project_cards`) |

## Image resolution

Images are resolved from the Obsidian `![[ref]]` syntax. The `|width` suffix
is stripped. The actual file is located by checking, in order:

1. `vault_media_path / ref`
2. Same directory as the note
3. `vault_path / ref`

## Output

Each card is saved as `{title}.png` in the output folder. The title is derived
from the filename by stripping the `⌬` prefix.

Cards are 567 x 378 px (15cm x 10cm at 96 DPI), rendered via wkhtmltoimage or
Chromium.
