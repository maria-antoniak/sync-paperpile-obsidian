# Paperpile to Obsidian Sync Tool

This tool synchronizes your Paperpile bibliography with your Obsidian vault by creating, updating, and organizing individual markdown files for each paper in the "Papers" folder of your vault.

<br>

## Features

- **Creates individual markdown files** for each paper in your Obsidian vault's "Papers" folder
- **YAML frontmatter metadata** including title, authors, year, journal/conference, abstract, URL, ref_id, and type - fully compatible with Obsidian's Dataview plugin
- **Preserves user notes** - any content you add after the YAML frontmatter is preserved during sync operations
- **Human-readable filenames** using the format "Title (ref_id).md" with proper spacing and casing
- **Automatic title change detection** - when paper titles change in Paperpile, existing files are automatically renamed while preserving your notes
- **Automatic cleanup** - papers removed from Paperpile are detected and their markdown files are moved to a "Removed Papers" subfolder
- **Archive-based sync** - uses `obsidian_archive.json` to track changes and avoid unnecessary file rewrites for better performance
- **Safe filename handling** - removes invalid filesystem characters and handles filename length limits
- **Comprehensive logging** - detailed console output shows what files were created, updated, renamed, or moved

<br>

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements_obsidian.txt
```

Or install individually:
```bash
pip install bibtexparser python-slugify
```

### 2. Configure Obsidian Vault Path

Edit the `sync_obsidian.py` file and update the `OBSIDIAN_VAULT_PATH` variable to point to your Obsidian vault:

```python
# Set your Obsidian vault path here - update this to your actual vault path
OBSIDIAN_VAULT_PATH = os.path.expanduser('~/Documents/My Obsidian Vault')  # Change this!
```

### 3. Set up Paperpile BibTeX Export

1. In Paperpile, click the gear icon (Settings) in the top-right
2. Go to "Workflows and Integrations"
3. Add a new "BibTeX Export" workflow:
   - Repository: Your GitHub repository (or local folder)
   - Export path: `references.bib`
   - Set up automatic sync if desired
  
### 4. Create Obsidian Folders

1. Create an empty `Papers/` folder in your Obsidian vault
2. Create an empty `Removed Papers/` folder inside of that folder

### 5. Turn On Dataview Plugin in Obsidian

1. Open Obsidian and open "Settings" from the file menu
2. Click on "Community plugins" in the sidebar
3. Click "Browse" and search for "Dataview"
4. Install and enable the plugin

This will format the frontmatter in your notes, which is where all the paper information will go.

<br>

## Usage

### Manual Sync

Place your `references.bib` file in the same directory as the script and run:

```bash
python sync_obsidian.py
```

If you are automatically syncing your bibtex file using the Paperpile bot, then make sure you pull the newest version of that file to your local machine before running the script. 

### What Gets Created

For each paper, a markdown file is created with:

- **YAML frontmatter** containing all metadata (title, authors, year, journal, abstract, URL, ref_id, type)
- **Notes section** below the frontmatter for your personal annotations
- **Filename format**: "Title (ref_id).md" with natural spacing and casing

NOTE: Tags or keywords are currently excluded, as Paperpile mixes together your custom tags with existing bibtex keywords. I hate this but if you want those tags, it's easy to modify the script to add them.

### Example Output

```markdown
---
title: "Understanding BERT: A Comprehensive Analysis"
authors: "John Smith, Jane Doe"
year: 2023
journal: "Nature Machine Intelligence"
abstract: "This paper provides a comprehensive analysis of BERT and its applications in natural language processing tasks..."
url: "https://example.com/paper"
ref_id: "Smith2023-ab"
type: "article"
---

<!-- Add your personal notes here. This section is preserved during sync updates. -->
```

<br>

## File Management

- Files are created in a `Papers/` folder within your Obsidian vault
- The script keeps track of processed papers in `obsidian_archive.json`
- Only changed papers are re-processed on subsequent runs
- Filename format: `{title}_{reference_id}.md` (sanitized for file systems)

<br>

## Customization

You can customize the script by modifying:

- `PAPERS_FOLDER`: Change the folder name within your vault
- `create_markdown_content()`: Modify the markdown template
- `create_safe_filename()`: Change filename generation logic

<br>

## Troubleshooting

### Common Issues

1. **"Obsidian vault path does not exist"**
   - Update `OBSIDIAN_VAULT_PATH` in the script to your actual vault location

2. **"BibTeX file not found"**
   - Ensure `references.bib` is in the same directory as the script
   - Check your Paperpile export is working correctly

3. **Import errors**
   - Install the required dependencies: `pip install -r requirements_obsidian.txt`
  
4. **Need to start over?**
   - Open your `Papers/` folder and delete all the paper files (you can do this in Obsidian, in your file explorer, or at the command line)
   - Delete the `obsidian_archive.json` file inside of this directory (same directory where you put your bibtex file)

### Verification

After running the script, check:
- A `Papers/` folder exists in your Obsidian vault
- A `Removed Papers/` folder exists inside of that folder
- Markdown files are created for your papers
- Tags appear correctly in Obsidian
- Links in the metadata work properly

<br>

## Comparison with Notion Version

This tool is based off a previous version I made for syncing Paperpile with Notion. That code was based on [this repo](https://github.com/seba-1511/sync-paperpile-notion) by [Séb Arnold](https://github.com/seba-1511). At this point, I think there is very little that is similar to that codebase, but I still want to shout out that tool as my inspiration. That tool used Github actions to automatically detect changes to the bibtex file and push those changes to Notion, while this tool requires you to manually run the sync script. Since my Obsidian files are all local, I'm not sure of a good way to automate the process, though I'm sure one exists (probably via an actual Obsidian plug in).

| Feature | Notion Version | Obsidian Version |
|---------|---------------|------------------|
| Storage | Notion Database | Markdown Files |
| Search | Notion Search | Obsidian Search + Tags |
| Linking | Database Relations | Wiki Links |
| Notes | Notion Pages | Markdown Sections |
| Customization | Limited | Full Control |
| Offline Access | Requires Internet | Full Offline |

The Obsidian version provides better control over your data and works entirely offline, while the Notion version offers better collaboration features and structured database views.
