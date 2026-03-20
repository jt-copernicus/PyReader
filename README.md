# PyReader - NCurses Ebook Reader

A terminal-based ebook reader supporting FB2 and EPUB formats with a simple ncurses interface.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

## Features

- **Supported Formats**: FB2 (FictionBook) and EPUB
- **Library Management**: Scan multiple directories for books
- **Search**: Search by title, author, or book number
- **Reading Position**: Remembers last position in each book
- **Responsive Layout**: Adjusts text to terminal size
- **Keyboard Navigation**: Full keyboard control

## Installation

### Requirements
- Python 3.7+
- Unix/Linux terminal with ncurses support

### Setup
```bash
git clone https://github.com/jt-copernicus/PyReader.git
cd PyReader/
chmod +x install.sh
sudo ./install.sh
```

Or run directly with Python:
```bash
python3 pyreader.py
```

### Uninstall
```bash
chmod +x uninstall.sh
sudo ./uninstall.sh
```


## Usage

### First Run
On first launch, you'll be prompted to enter the path to your books directory.

### Library View Controls

| Key | Action |
|-----|--------|
| `↑`/`↓` | Navigate book list |
| `Enter` | Open selected book |
| `Ctrl+W` | Search books (by title, author, or #) |
| `Ctrl+L` | Add another library path |
| `0-9` | Type number, press Enter to jump to that book |
| `ESC` | Press once for exit warning, twice to quit |
| `q` | Same as ESC |

### Reader View Controls

| Key | Action |
|-----|--------|
| `→`/`↓` or `PgDn` | Next page |
| `←`/`↑` or `PgUp` | Previous page |
| `Space` | Scroll one line down |
| `Home` | Go to first page |
| `End` | Go to last page |
| `ESC` or `q` | Return to library |

### Search Function
1. Press `Ctrl+W` in library view
2. Type part of a title, author name, or book number
3. Press `Enter` to search
4. Navigate results with arrow keys

## Configuration

Settings are stored in `~/.pyreader_config.json`:
- Library paths
- Last opened book
- Reading position

## File Locations

Books are sorted alphabetically by filename and assigned numbers for quick access.

## Screen Layout

### Library View
```
┌─────────────────────────────────────┐
│        PyReader - Library           │
│  Ctrl+W: Search | Ctrl+L: Add Path  │
│  Books: 42                          │
│                                     │
│  1. Alice in Wonderland - Carroll   │
│  2. Dracula - Stoker               │
│  3. Frankenstein - Shelley          │
│  ...                                │
│                                     │
│  Libraries: 2 path(s)               │
└─────────────────────────────────────┘
```

### Reader View
```
┌─────────────────────────────────────┐
│        Alice in Wonderland          │
│                                     │
│  Chapter I: Down the Rabbit-Hole   │
│                                     │
│  Alice was beginning to get very   │
│  tired of sitting by her sister    │
│  on the bank, and of having...     │
│                                     │
│                                     │
│  Page 12/156                        │
└─────────────────────────────────────┘
```

## Notes

- The reader automatically rescans the library on each startup to detect new books
- Reading progress is saved when you return to the library
- Long lines are automatically wrapped to fit the terminal width
