#!/usr/bin/env python3

import bibtexparser
import json
import os
import re
from pathlib import Path
from slugify import slugify
import pprint

"""
Sync Paperpile BibTeX export to Obsidian markdown files.
Creates a new markdown file for each paper in the Papers folder of your Obsidian vault.
This version preserves user notes when updating files.
"""

# Configuration
# BIB_PATH = 'references_TEST.bib'
BIB_PATH = 'references.bib'
ARCHIVE_PATH = 'obsidian_archive.json'

# Set your Obsidian vault path here - update this to your actual vault path
OBSIDIAN_VAULT_PATH = os.path.expanduser('~/Documents/Obsidian Vault')  # Change this!
PAPERS_FOLDER = 'Papers'


def clean_str(s):
    """Clean string for markdown use"""
    if not s:
        return ''
    s = re.sub(r'[^A-Za-z0-9\s&.,-;:/?()"\']+', '', s) 
    return ' '.join(s.split())


def format_authors(test_string):
    """Format authors from BibTeX format to readable format"""
    if not test_string:
        return ''
    
    authors = [a.split(',') for a in test_string.split(';')]
    formatted_authors = [] 
    for a in authors:
        if len(a) == 1:
            formatted_authors.append(a[0].strip())
        elif len(a) == 2:
            formatted_authors.append(a[1].strip() + ' ' + a[0].strip())
        else:
            formatted_authors.append(' '.join(a).strip())
    return ', '.join(formatted_authors)


def create_safe_filename(title, ref_id):
    """Create a safe filename for the markdown file"""
    # Maximum filename length for most filesystems (leaving some buffer)
    MAX_FILENAME_LENGTH = 250
    
    if title:
        # Use title with normal spaces and casing, just remove invalid filename characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title.strip()
        
        # Calculate space needed for ref_id and file extension
        ref_id_part = f" ({ref_id}).md"
        available_space = MAX_FILENAME_LENGTH - len(ref_id_part)
        
        # Truncate title if needed
        if len(safe_title) > available_space:
            safe_title = safe_title[:available_space].rstrip()
        
        filename = f"{safe_title}{ref_id_part}"
    else:
        filename = f"{ref_id}.md"
    
    # Final safety check - if somehow still too long, truncate more aggressively
    if len(filename) > MAX_FILENAME_LENGTH:
        base_name = filename.rsplit('.', 1)[0]  # Remove .md
        truncated_base = base_name[:MAX_FILENAME_LENGTH - 3]  # Leave room for .md
        filename = f"{truncated_base}.md"
    
    return filename


def get_bib_entry(entry):
    """Extract and format data from a BibTeX entry"""
    ref_id = entry.get('ID', '')
    title = ''
    authors = ''
    year = ''
    link = None
    abstract = ''
    journal = ''
    booktitle = ''

    if 'title' in entry:
        title = entry['title']
        title = clean_str(title)

    if 'author' in entry:
        authors = entry['author']
        authors = authors.replace(' and ', '; ')
        authors = authors.replace(' And ', '; ')
        authors = clean_str(authors)
        authors = format_authors(authors)
           
    if 'year' in entry:
        year = entry['year']
        year = clean_str(year)

    if 'url' in entry:
        link = entry['url']

    if 'abstract' in entry:
        abstract = entry['abstract']
        abstract = ' '.join(abstract.split())
        abstract = clean_str(abstract)

    if 'journal' in entry:
        journal = clean_str(entry['journal'])
        
    if 'booktitle' in entry:
        booktitle = clean_str(entry['booktitle'])

    # Keywords removed - not needed
    
    formatted_entry = {
        'title': title,
        'authors': authors,
        'year': year,
        'ref_id': ref_id,
        'link': link,
        'abstract': abstract,
        'journal': journal,
        'booktitle': booktitle
    }
           
    return ref_id, formatted_entry


def extract_user_content_from_markdown(filepath):
    """Extract user-added content from existing markdown file"""
    if not filepath.exists():
        return {'notes': ''}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return {'notes': ''}
    
    # Extract everything after the YAML frontmatter as notes
    # Split on the closing --- of frontmatter
    notes = ''
    if '---\n\n' in content:
        parts = content.split('---\n\n', 1)
        if len(parts) > 1:
            notes_content = parts[1].strip()
            # Only keep content if it's not just the placeholder comment
            if notes_content and notes_content != '<!-- Add your notes here -->':
                notes = notes_content

    
    return {'notes': notes}


def create_markdown_content(entry, user_content=None):
    """Create markdown content for a paper with YAML frontmatter"""
    title = entry.get('title', 'Untitled')
    authors = entry.get('authors', '')
    year = entry.get('year', '')
    ref_id = entry.get('ref_id', '')
    link = entry.get('link', '')
    abstract = entry.get('abstract', '')
    journal = entry.get('journal', '')
    booktitle = entry.get('booktitle', '')
    
    # Get user content or use defaults
    if user_content is None:
        user_content = {'notes': ''}
    
    notes = user_content.get('notes', '')
    
    # Create YAML frontmatter
    content = "---\n"
    content += f"title: \"{title}\"\n"
    if authors:
        content += f"authors: \"{authors}\"\n"
    if year:
        content += f"year: {year}\n"
    if journal:
        content += f"journal: \"{journal}\"\n"
    if booktitle:
        content += f"conference: \"{booktitle}\"\n"
    if abstract:
        # Escape quotes in abstract for YAML
        escaped_abstract = abstract.replace('"', '\\"')
        content += f"abstract: \"{escaped_abstract}\"\n"
    if link:
        content += f"url: \"{link}\"\n"
    content += f"ref_id: \"{ref_id}\"\n"
    content += "type: paper\n"
    content += "---\n\n"
    
    # Notes section - preserve user content or use placeholder
    if notes:
        content += f"{notes}\n\n"
    else:
        content += "<!-- Add your notes here -->\n\n"
    
    return content


def find_existing_file_by_ref_id(papers_folder, ref_id):
    """Find existing file for a given ref_id, even if filename differs"""
    pattern = f"*({ref_id}).md"
    matching_files = list(papers_folder.glob(pattern))
    
    # Return only files directly in papers_folder (not in subfolders)
    for file_path in matching_files:
        if file_path.parent == papers_folder:
            return file_path
    return None


def create_obsidian_file(entry, papers_folder, user_content=None):
    """Create or update an Obsidian markdown file for a paper"""
    ref_id = entry.get('ref_id', '')
    new_filename = create_safe_filename(entry.get('title', ''), ref_id)
    new_filepath = papers_folder / new_filename
    
    # Check if a file with this ref_id already exists (possibly with different title)
    existing_file = find_existing_file_by_ref_id(papers_folder, ref_id)
    
    # Extract existing user content
    if user_content is None:
        if existing_file:
            # Extract from existing file (even if it has a different name)
            user_content = extract_user_content_from_markdown(existing_file)
        else:
            user_content = extract_user_content_from_markdown(new_filepath)
    
    # Handle file renaming if title changed
    if existing_file and existing_file.name != new_filename:
        print(f"Title changed - renaming: {existing_file.name} → {new_filename}")
        try:
            # If target filename already exists, we need to handle the conflict
            if new_filepath.exists():
                # This shouldn't happen normally, but let's be safe
                print(f"Warning: Target file {new_filename} already exists. Backing up existing file.")
                backup_name = f"{new_filepath.stem}_backup_{ref_id}{new_filepath.suffix}"
                new_filepath.rename(papers_folder / backup_name)
            
            # Rename the existing file to match new title
            existing_file.rename(new_filepath)
            
        except Exception as e:
            print(f"Error renaming file {existing_file.name}: {e}")
            # Continue with the existing file path if rename failed
            new_filepath = existing_file
    
    content = create_markdown_content(entry, user_content)
    
    # Write the file
    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return new_filepath, user_content


def load_archive():
    """Load the archive of previously processed entries"""
    if os.path.exists(ARCHIVE_PATH):
        with open(ARCHIVE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_archive(archive):
    """Save the archive of processed entries"""
    with open(ARCHIVE_PATH, 'w', encoding='utf-8') as f:
        json.dump(archive, f, indent=2, ensure_ascii=False)


def entries_are_equal(archive_entry, bib_entry):
    """Compare archive entry with bib entry to detect changes"""
    if isinstance(archive_entry, dict) and 'entry' in archive_entry:
        # New format archive entry
        return archive_entry['entry'] == bib_entry
    else:
        # Old format archive entry - treat as different to force update
        return False


def cleanup_removed_papers(papers_folder, current_ref_ids, archive):
    """Move papers that are no longer in Paperpile to Removed Papers folder"""
    removed_folder = papers_folder / "Removed Papers"
    removed_folder.mkdir(exist_ok=True)
    
    moved_count = 0
    
    # Find papers in archive that are no longer in current BibTeX
    for ref_id in list(archive.keys()):
        if ref_id not in current_ref_ids:
            # Find the file for this ref_id
            # Look for files ending with (ref_id).md
            pattern = f"*({ref_id}).md"
            matching_files = list(papers_folder.glob(pattern))
            
            for file_path in matching_files:
                # Only move if it's directly in papers_folder (not already in subfolder)
                if file_path.parent == papers_folder:
                    new_path = removed_folder / file_path.name
                    try:
                        file_path.rename(new_path)
                        print(f"Moved to Removed Papers: {file_path.name}")
                        moved_count += 1
                    except Exception as e:
                        print(f"Error moving {file_path.name}: {e}")
            
            # Remove from archive
            del archive[ref_id]
    
    return moved_count


def main():
    """Main function to sync BibTeX to Obsidian"""
    
    # Check if Obsidian vault path exists
    vault_path = Path(OBSIDIAN_VAULT_PATH)
    if not vault_path.exists():
        print(f"Error: Obsidian vault path does not exist: {OBSIDIAN_VAULT_PATH}")
        print("Please update OBSIDIAN_VAULT_PATH in the script to point to your actual Obsidian vault.")
        return
    
    # Create Papers folder if it doesn't exist
    papers_folder = vault_path / PAPERS_FOLDER
    papers_folder.mkdir(exist_ok=True)
    
    # Load the BibTeX file
    if not os.path.exists(BIB_PATH):
        print(f"Error: BibTeX file not found: {BIB_PATH}")
        return
        
    print(f"Loading BibTeX file: {BIB_PATH}")
    
    # Use older bibtexparser API
    parser = bibtexparser.bparser.BibTexParser()
    parser.ignore_nonstandard_types = True
    parser.homogenize_fields = False
    parser.interpolate_strings = False
    
    with open(BIB_PATH) as bib_file:
        bibliography = bibtexparser.load(bib_file, parser=parser)
    
    # Load archive of previously processed entries
    archive = load_archive()
    
    # Collect current ref_ids for cleanup
    current_ref_ids = set()
    
    # Process entries
    processed_count = 0
    new_count = 0
    updated_count = 0
    
    for entry in bibliography.entries:
        ref_id, formatted_entry = get_bib_entry(entry)
        current_ref_ids.add(ref_id)
        ref_id, formatted_entry = get_bib_entry(entry)
        
        # Check if this entry has changed since last processing
        if ref_id in archive and entries_are_equal(archive[ref_id], formatted_entry):
            continue  # No changes, skip
        
        # Create or update the Obsidian file
        # The create_obsidian_file function will extract existing user content from the file
        # and merge it with any user content from the archive
        try:
            filepath, user_content = create_obsidian_file(
                formatted_entry, 
                papers_folder
            )
            
            if ref_id in archive:
                updated_count += 1
                print(f"Updated: {filepath.name}")
            else:
                new_count += 1
                print(f"Created: {filepath.name}")
            
            # Update archive with formatted entry and user content
            archive[ref_id] = {
                'entry': formatted_entry, 
                'notes': user_content.get('notes', '')
            }
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {ref_id}: {e}")
    
    # Clean up removed papers
    moved_count = cleanup_removed_papers(papers_folder, current_ref_ids, archive)
    
    # Save updated archive
    save_archive(archive)
    
    # Print summary
    print(f"\nSync complete!")
    print(f"Total entries in BibTeX: {len(bibliography.entries)}")
    print(f"New files created: {new_count}")
    print(f"Files updated: {updated_count}")
    print(f"Files processed this run: {processed_count}")
    if moved_count > 0:
        print(f"Files moved to Removed Papers: {moved_count}")
    print(f"Papers folder: {papers_folder}")


if __name__ == "__main__":
    main()
