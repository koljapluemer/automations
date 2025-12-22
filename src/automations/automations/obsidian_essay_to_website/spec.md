Should find certain notes in obsidian vault, then convert them to a bespoke HTML format.
Needs the following config vars (otherwise immediate fail and end automation):

- `vault_path`
- `vault_media_path`
- `essay_include_string`
- `essay_output_folder`
- `essay_media_folder`

Goes to `vault_path` and finds .md files (resurive) which contain the `essay_include_string`. See [here](src/automations/automations/obsidian_essay_to_website/inspiration_note.md) for how such a note may look.
Find images mentioned in the .md ("![[]]" obsidian image embed syntax) and copies them over to the media folder .
Converts them from markdown to HTML.
Uses a template like `src/automations/automations/obsidian_essay_to_website/inspiration_site.md`, ensuring that images are wrapped in a card like in the example, and making sure images are correctly linked.