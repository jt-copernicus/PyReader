#!/usr/bin/env python3
"""
PyReader - An ncurses ebook reader supporting FB2 and EPUB formats.

by Jonathan Torres

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
"""

import curses
import os
import re
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import html

# Configuration file path
CONFIG_FILE = Path.home() / ".pyreader_config.json"
SUPPORTED_FORMATS = ('.fb2', '.epub')


class Book:
    """Represents a book in the library."""

    def __init__(self, filepath: str, book_id: int = 0):
        self.filepath = filepath
        self.book_id = book_id
        self.title = self._extract_title()
        self.author = self._extract_author()
        self.display_text = f"{book_id}. {self.title}"
        if self.author:
            self.display_text += f" - {self.author}"

    def _extract_title(self) -> str:
        """Extract title from book file."""
        try:
            ext = Path(self.filepath).suffix.lower()
            if ext == '.fb2':
                return self._extract_fb2_title()
            elif ext == '.epub':
                return self._extract_epub_title()
        except Exception:
            pass
        return Path(self.filepath).stem

    def _extract_author(self) -> str:
        """Extract author from book file."""
        try:
            ext = Path(self.filepath).suffix.lower()
            if ext == '.fb2':
                return self._extract_fb2_author()
            elif ext == '.epub':
                return self._extract_epub_author()
        except Exception:
            pass
        return ""

    def _extract_fb2_title(self) -> str:
        """Extract title from FB2 file."""
        tree = ET.parse(self.filepath)
        root = tree.getroot()
        ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        title_elem = root.find('.//fb:book-name', ns)
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        title_elem = root.find('.//fb:description/fb:title-info/fb:book-title', ns)
        if title_elem is not None and title_elem.text:
            return title_elem.text.strip()
        return Path(self.filepath).stem

    def _extract_fb2_author(self) -> str:
        """Extract author from FB2 file."""
        tree = ET.parse(self.filepath)
        root = tree.getroot()
        ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
        author_elem = root.find('.//fb:description/fb:title-info/fb:author', ns)
        if author_elem is not None:
            first = author_elem.find('fb:first-name', ns)
            last = author_elem.find('fb:last-name', ns)
            parts = []
            if first is not None and first.text:
                parts.append(first.text)
            if last is not None and last.text:
                parts.append(last.text)
            if parts:
                return ' '.join(parts)
        return ""

    def _extract_epub_title(self) -> str:
        """Extract title from EPUB file."""
        with zipfile.ZipFile(self.filepath, 'r') as z:
            # Try to find content.opf or package.opf
            namelist = z.namelist()
            opf_path = None
            for name in namelist:
                if name.endswith('.opf'):
                    opf_path = name
                    break

            if opf_path:
                content = z.read(opf_path).decode('utf-8', errors='ignore')
                # Extract title from metadata
                match = re.search(r'<dc:title[^>]*>([^<]+)</dc:title>', content, re.I)
                if match:
                    return html.unescape(match.group(1).strip())

        return Path(self.filepath).stem

    def _extract_epub_author(self) -> str:
        """Extract author from EPUB file."""
        with zipfile.ZipFile(self.filepath, 'r') as z:
            namelist = z.namelist()
            for name in namelist:
                if name.endswith('.opf'):
                    content = z.read(name).decode('utf-8', errors='ignore')
                    match = re.search(r'<dc:creator[^>]*>([^<]+)</dc:creator>', content, re.I)
                    if match:
                        return html.unescape(match.group(1).strip())
        return ""


class BookContent:
    """Represents the content of a book."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.pages: List[List[str]] = []
        self.total_lines = 0

    def parse(self, width: int, height: int) -> None:
        """Parse book into pages based on screen dimensions."""
        ext = Path(self.filepath).suffix.lower()

        if ext == '.fb2':
            lines = self._parse_fb2()
        elif ext == '.epub':
            lines = self._parse_epub()
        else:
            lines = ["Unsupported file format"]

        self.total_lines = len(lines)
        self._paginate(lines, width, height)

    def _parse_fb2(self) -> List[str]:
        """Parse FB2 file into lines of text."""
        lines = []
        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            ns = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}

            # Extract all paragraphs
            for elem in root.iter():
                if elem.tag == f"{{{ns['fb']}}}p":
                    if elem.text:
                        text = elem.text.strip()
                        if text:
                            lines.append(text)
                            lines.append("")  # Empty line after paragraph
                elif elem.tag == f"{{{ns['fb']}}}title":
                    if elem.text:
                        text = elem.text.strip()
                        if text:
                            lines.append(f"*** {text} ***")
                            lines.append("")
                elif elem.tag == f"{{{ns['fb']}}}subtitle":
                    if elem.text:
                        text = elem.text.strip()
                        if text:
                            lines.append(f"-- {text} --")
                            lines.append("")
        except Exception as e:
            lines = [f"Error parsing FB2: {str(e)}"]

        return lines

    def _parse_epub(self) -> List[str]:
        """Parse EPUB file into lines of text."""
        lines = []
        try:
            with zipfile.ZipFile(self.filepath, 'r') as z:
                namelist = z.namelist()

                # Find the OPF file to determine reading order
                opf_path = None
                for name in namelist:
                    if name.endswith('.opf'):
                        opf_path = name
                        break

                content_files = []
                if opf_path:
                    opf_content = z.read(opf_path).decode('utf-8', errors='ignore')
                    # Extract content file references
                    content_files = re.findall(r'href="([^"]+\.(?:x?html?|xml))"', opf_content, re.I)
                    # Make paths relative to OPF
                    opf_dir = os.path.dirname(opf_path)
                    if opf_dir:
                        content_files = [os.path.join(opf_dir, f).replace('\\', '/') for f in content_files]

                # If we couldn't find reading order, find all HTML files
                if not content_files:
                    content_files = [f for f in namelist
                                     if f.endswith(('.html', '.htm', '.xhtml', '.xml'))
                                     and not f.startswith('META-INF')]

                for content_file in content_files:
                    if content_file in namelist:
                        try:
                            content = z.read(content_file).decode('utf-8', errors='ignore')
                            # Strip HTML tags
                            text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.S | re.I)
                            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S | re.I)
                            text = re.sub(r'<[^>]+>', ' ', text)
                            text = html.unescape(text)
                            # Split into paragraphs
                            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
                            for para in paragraphs:
                                # Wrap long lines
                                para = re.sub(r'\s+', ' ', para)
                                lines.append(para)
                                lines.append("")
                            lines.append("---")
                            lines.append("")
                        except Exception:
                            continue

        except Exception as e:
            lines = [f"Error parsing EPUB: {str(e)}"]

        return lines

    def _paginate(self, lines: List[str], width: int, height: int) -> None:
        """Split lines into pages based on screen size."""
        self.pages = []
        current_page = []
        lines_on_page = 0
        content_height = height - 2  # Reserve space for header/footer

        for line in lines:
            # Wrap long lines
            wrapped = self._wrap_line(line, width - 2)
            for wrapped_line in wrapped:
                if lines_on_page >= content_height:
                    self.pages.append(current_page)
                    current_page = [wrapped_line]
                    lines_on_page = 1
                else:
                    current_page.append(wrapped_line)
                    lines_on_page += 1

        # Don't forget the last page
        if current_page:
            self.pages.append(current_page)

        if not self.pages:
            self.pages = [["(Empty book)"]]

    def _wrap_line(self, line: str, width: int) -> List[str]:
        """Wrap a line to fit within the given width."""
        if len(line) <= width:
            return [line]

        words = line.split(' ')
        lines = []
        current_line = ""

        for word in words:
            if len(word) > width:
                # Long word, need to break it
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                for i in range(0, len(word), width):
                    chunk = word[i:i+width]
                    if i + width < len(word):
                        lines.append(chunk + "-")
                    else:
                        current_line = chunk
            elif len(current_line) + len(word) + (1 if current_line else 0) > width:
                lines.append(current_line)
                current_line = word
            else:
                current_line = word if not current_line else current_line + " " + word

        if current_line:
            lines.append(current_line)

        return lines if lines else [line]


class Config:
    """Application configuration manager."""

    def __init__(self):
        self.library_paths: List[str] = []
        self.last_book: Optional[str] = None
        self.last_position: int = 0
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.library_paths = data.get('library_paths', [])
                    self.last_book = data.get('last_book')
                    self.last_position = data.get('last_position', 0)
            except (json.JSONDecodeError, IOError):
                pass

    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'library_paths': self.library_paths,
                    'last_book': self.last_book,
                    'last_position': self.last_position
                }, f)
        except IOError:
            pass

    def add_library_path(self, path: str) -> bool:
        """Add a new library path."""
        if os.path.isdir(path) and path not in self.library_paths:
            self.library_paths.append(path)
            self.save()
            return True
        return False


class PyReader:
    """Main application class."""

    def __init__(self):
        self.config = Config()
        self.books: List[Book] = []
        self.filtered_books: List[Book] = []
        self.current_book: Optional[BookContent] = None
        self.current_book_path: Optional[str] = None
        self.current_page = 0
        self.current_line = 0
        self.selected_index = 0
        self.search_query = ""
        self.search_mode = False
        self.number_input = ""
        self.exit_warning = False
        self.stdscr: Optional[Any] = None

    def run(self, stdscr) -> None:
        """Main application loop."""
        self.stdscr = stdscr
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(-1)  # Blocking input

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)

        # Check if first run
        if not self.config.library_paths:
            self._prompt_for_library_path()

        # Scan library and load books
        self._scan_library()

        # Try to restore last book
        if self.config.last_book and os.path.exists(self.config.last_book):
            self._open_book(self.config.last_book, self.config.last_position)

        self._main_loop()

    def _prompt_for_library_path(self) -> None:
        """Prompt user for initial library path."""
        while True:
            path = self._input_dialog("Enter path to books directory:", "")
            if path:
                expanded = os.path.expanduser(path)
                if os.path.isdir(expanded):
                    self.config.add_library_path(expanded)
                    break
            self._show_message("Invalid directory. Please try again.")

    def _add_library_path_dialog(self) -> None:
        """Dialog to add additional library paths."""
        path = self._input_dialog("Add library path:", "")
        if path:
            expanded = os.path.expanduser(path)
            if os.path.isdir(expanded):
                if self.config.add_library_path(expanded):
                    self._show_message(f"Added: {expanded}")
                    self._scan_library()
                else:
                    self._show_message("Path already in library or invalid.")
            else:
                self._show_message("Directory not found.")

    def _scan_library(self) -> None:
        """Scan library paths for books."""
        book_files = []
        for path in self.config.library_paths:
            expanded = os.path.expanduser(path)
            if os.path.isdir(expanded):
                for root, _, files in os.walk(expanded):
                    for file in files:
                        if file.lower().endswith(SUPPORTED_FORMATS):
                            book_files.append(os.path.join(root, file))

        # Sort alphabetically and assign IDs
        book_files.sort(key=lambda x: Path(x).stem.lower())
        self.books = [Book(f, i + 1) for i, f in enumerate(book_files)]
        self.filtered_books = self.books.copy()
        self.selected_index = 0

    def _main_loop(self) -> None:
        """Main input/render loop."""
        while True:
            self._render()
            key = self.stdscr.getch()

            if key == -1:
                continue

            # Handle terminal resize
            if key == curses.KEY_RESIZE:
                if self.current_book and self.current_book_path:
                    # Re-parse book for new dimensions
                    self._open_book(self.current_book_path, self.current_page)
                continue

            if self.current_book:
                if self._handle_reader_input(key):
                    break
            else:
                if self._handle_library_input(key):
                    break

    def _handle_reader_input(self, key: int) -> bool:
        """Handle input in reader mode. Returns True to exit app."""
        if self.search_mode:
            if key == 27:  # ESC
                self.search_mode = False
                self.search_query = ""
            elif key == ord('\n') or key == curses.KEY_ENTER:
                self.search_mode = False
            elif key == curses.KEY_BACKSPACE or key == 127:
                self.search_query = self.search_query[:-1]
            elif 32 <= key < 127:
                self.search_query += chr(key)
            return False

        if key == 27:  # ESC - return to library
            self._close_book()
            return False

        if key == ord(' ') or key == curses.KEY_DOWN:
            # Scroll one line
            self._scroll_line(1)
        elif key == curses.KEY_UP:
            self._scroll_line(-1)
        elif key == curses.KEY_RIGHT or key == curses.KEY_NPAGE:
            self._change_page(1)
        elif key == curses.KEY_LEFT or key == curses.KEY_PPAGE:
            self._change_page(-1)
        elif key == curses.KEY_HOME:
            self.current_page = 0
            self.current_line = 0
        elif key == curses.KEY_END:
            if self.current_book:
                self.current_page = len(self.current_book.pages) - 1
                self.current_line = 0
        elif key == ord('q') or key == ord('Q'):
            self._close_book()

        return False

    def _handle_library_input(self, key: int) -> bool:
        """Handle input in library mode. Returns True to exit app."""
        if self.search_mode:
            if key == 27:  # ESC
                self.search_mode = False
                self.search_query = ""
                self.filtered_books = self.books.copy()
            elif key == ord('\n') or key == curses.KEY_ENTER:
                self._execute_search()
            elif key == curses.KEY_BACKSPACE or key == 127:
                self.search_query = self.search_query[:-1]
            elif 32 <= key < 127:
                self.search_query += chr(key)
            return False

        if self.number_input:
            if key == ord('\n') or key == curses.KEY_ENTER:
                self._select_by_number()
                return False
            elif key == 27:  # ESC
                self.number_input = ""
                return False
            elif key == curses.KEY_BACKSPACE or key == 127:
                self.number_input = self.number_input[:-1]
            elif ord('0') <= key <= ord('9'):
                self.number_input += chr(key)
            return False

        if key == 27:  # ESC
            if self.exit_warning:
                return True
            else:
                self.exit_warning = True
                return False

        self.exit_warning = False

        if key == ord('\n') or key == curses.KEY_ENTER:
            self._open_selected_book()
        elif key == curses.KEY_UP:
            self.selected_index = max(0, self.selected_index - 1)
        elif key == curses.KEY_DOWN:
            self.selected_index = min(len(self.filtered_books) - 1, self.selected_index + 1)
        elif key == curses.KEY_HOME:
            self.selected_index = 0
        elif key == curses.KEY_END:
            self.selected_index = len(self.filtered_books) - 1
        elif key == curses.KEY_PPAGE:
            self.selected_index = max(0, self.selected_index - 10)
        elif key == curses.KEY_NPAGE:
            self.selected_index = min(len(self.filtered_books) - 1, self.selected_index + 10)
        elif key == ord('q') or key == ord('Q'):
            if self.exit_warning:
                return True
            self.exit_warning = True
        elif key == 23:  # Ctrl+W - Search
            self.search_mode = True
            self.search_query = ""
        elif key == 12:  # Ctrl+L - Add library path
            self._add_library_path_dialog()
        elif ord('0') <= key <= ord('9'):
            self.number_input = chr(key)

        return False

    def _execute_search(self) -> None:
        """Execute search based on current query."""
        query = self.search_query.lower().strip()
        if not query:
            self.filtered_books = self.books.copy()
        else:
            # Check if query is a number
            if query.isdigit():
                book_id = int(query)
                self.filtered_books = [b for b in self.books if b.book_id == book_id]
            else:
                # Search by title/author
                self.filtered_books = [b for b in self.books
                                       if query in b.title.lower()
                                       or query in b.author.lower()]
        self.selected_index = 0
        self.search_mode = False

    def _select_by_number(self) -> None:
        """Select book by number input."""
        if self.number_input.isdigit():
            book_id = int(self.number_input)
            for book in self.filtered_books:
                if book.book_id == book_id:
                    self._open_book(book.filepath, 0)
                    break
        self.number_input = ""

    def _open_selected_book(self) -> None:
        """Open the currently selected book."""
        if 0 <= self.selected_index < len(self.filtered_books):
            book = self.filtered_books[self.selected_index]
            self._open_book(book.filepath, 0)

    def _open_book(self, filepath: str, position: int) -> None:
        """Open a book file."""
        try:
            self.current_book = BookContent(filepath)
            height, width = self.stdscr.getmaxyx()
            self.current_book.parse(width, height)
            self.current_book_path = filepath

            # Restore position
            if position < len(self.current_book.pages):
                self.current_page = position
            else:
                self.current_page = 0
            self.current_line = 0
        except Exception as e:
            self._show_message(f"Error opening book: {str(e)}")

    def _close_book(self) -> None:
        """Close current book and return to library."""
        if self.current_book and self.current_book_path:
            self.config.last_book = self.current_book_path
            self.config.last_position = self.current_page
            self.config.save()

        self.current_book = None
        self.current_book_path = None
        self.current_page = 0
        self.current_line = 0

    def _change_page(self, delta: int) -> None:
        """Change page by delta."""
        if not self.current_book:
            return
        new_page = self.current_page + delta
        new_page = max(0, min(len(self.current_book.pages) - 1, new_page))
        self.current_page = new_page
        self.current_line = 0

    def _scroll_line(self, delta: int) -> None:
        """Scroll by line within current page."""
        if not self.current_book:
            return

        height, _ = self.stdscr.getmaxyx()
        content_height = height - 2

        new_line = self.current_line + delta

        # Check if we need to change pages
        page_lines = len(self.current_book.pages[self.current_page])

        if new_line >= page_lines and self.current_page < len(self.current_book.pages) - 1:
            self.current_page += 1
            self.current_line = 0
        elif new_line < 0 and self.current_page > 0:
            self.current_page -= 1
            page_lines = len(self.current_book.pages[self.current_page])
            self.current_line = max(0, page_lines - content_height + 1)
        else:
            self.current_line = max(0, min(page_lines - 1, new_line))

    def _render(self) -> None:
        """Render the current screen."""
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        if self.current_book:
            self._render_reader(height, width)
        else:
            self._render_library(height, width)

        self.stdscr.refresh()

    def _render_library(self, height: int, width: int) -> None:
        """Render the library view."""
        # Header
        header = " PyReader - Library "
        if self.exit_warning:
            header = " PyReader - Press ESC again to exit "
        self.stdscr.addstr(0, 0, header[:width].center(width), curses.color_pair(1))

        # Search bar or number input indicator
        if self.search_mode:
            search_line = f"Search: {self.search_query}"
            self.stdscr.addstr(1, 0, search_line[:width], curses.color_pair(3))
        elif self.number_input:
            num_line = f"Go to #: {self.number_input}"
            self.stdscr.addstr(1, 0, num_line[:width], curses.color_pair(3))
        else:
            # Instructions
            instructions = "Ctrl+W: Search | Ctrl+L: Add Path | Enter: Open | ESC: Exit"
            self.stdscr.addstr(1, 0, instructions[:width], curses.color_pair(4))

        # Book count
        count_text = f"Books: {len(self.filtered_books)}"
        self.stdscr.addstr(2, 0, count_text[:width])

        # Book list
        list_start = 4
        list_height = height - list_start - 1

        if self.filtered_books:
            # Calculate visible range
            start_idx = max(0, self.selected_index - list_height // 2)
            end_idx = min(len(self.filtered_books), start_idx + list_height)

            for i in range(start_idx, end_idx):
                book = self.filtered_books[i]
                y = list_start + (i - start_idx)

                if y >= height - 1:
                    break

                line = book.display_text[:width - 1]
                if i == self.selected_index:
                    self.stdscr.addstr(y, 0, line.ljust(width - 1), curses.color_pair(2))
                else:
                    self.stdscr.addstr(y, 0, line)
        else:
            msg = "No books found. Press Ctrl+L to add library paths."
            self.stdscr.addstr(list_start, 0, msg[:width])

        # Footer with library paths
        footer = f"Libraries: {len(self.config.library_paths)} path(s)"
        self.stdscr.addstr(height - 1, 0, footer[:width], curses.color_pair(1))

    def _render_reader(self, height: int, width: int) -> None:
        """Render the reader view."""
        if not self.current_book:
            return

        content_height = height - 2

        # Header with title
        title = Path(self.current_book_path).stem[:width - 1] if self.current_book_path else "Unknown"
        self.stdscr.addstr(0, 0, title.center(width), curses.color_pair(1))

        # Content
        if 0 <= self.current_page < len(self.current_book.pages):
            page = self.current_book.pages[self.current_page]

            for i in range(content_height):
                line_idx = self.current_line + i
                if line_idx < len(page):
                    line = page[line_idx][:width - 1]
                    self.stdscr.addstr(i + 1, 0, line)
                else:
                    break

        # Footer with page info
        total_pages = len(self.current_book.pages)
        page_info = f"Page {self.current_page + 1}/{total_pages}"
        self.stdscr.addstr(height - 1, 0, page_info[:width], curses.color_pair(1))

    def _input_dialog(self, prompt: str, default: str = "") -> str:
        """Show an input dialog and return user input."""
        curses.echo()
        curses.curs_set(1)
        self.stdscr.timeout(-1)  # Blocking input
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        self.stdscr.addstr(height // 2 - 2, 2, prompt[:width - 4])
        self.stdscr.addstr(height // 2, 2, default)
        self.stdscr.refresh()

        try:
            self.stdscr.move(height // 2, 2)
            result = self.stdscr.getstr(height // 2, 2, 256).decode('utf-8').strip()
            return result
        except:
            return ""
        finally:
            curses.noecho()
            curses.curs_set(0)

    def _show_message(self, message: str) -> None:
        """Show a message and wait for key press."""
        self.stdscr.timeout(-1)  # Blocking input
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        self.stdscr.addstr(height // 2, 0, message[:width].center(width), curses.color_pair(3))
        self.stdscr.addstr(height // 2 + 2, 0, "Press any key to continue..."[:width].center(width))
        self.stdscr.refresh()
        self.stdscr.getch()


def main():
    """Entry point."""
    app = PyReader()
    curses.wrapper(app.run)


if __name__ == "__main__":
    main()
