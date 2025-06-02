"""PDF exporter for journal entries.

This module implements PDF export functionality for journal entries, creating
professional, printable documents with proper formatting, table of contents,
and WSJ-inspired styling. The exporter uses ReportLab for PDF generation
and supports rich text formatting, pagination, and customizable templates.

The PDFExporter class provides:
    - Professional PDF document generation with cover page
    - Table of contents with page numbers
    - Rich text support with markdown parsing
    - WSJ-inspired typography and color scheme
    - Custom headers and footers with page numbers
    - Efficient memory usage for large documents
    - Template customization options

Example:
    Basic PDF export:
    
    >>> from src.exporters import PDFExporter, ExportOptions
    >>> from src.data_access import JournalDAO
    >>> 
    >>> options = ExportOptions(
    ...     extra_options={
    ...         'include_toc': True,
    ...         'include_cover': True,
    ...         'page_size': 'letter'
    ...     }
    ... )
    >>> exporter = PDFExporter(options)
    >>> entries = JournalDAO.get_journal_entries(start_date, end_date)
    >>> result = exporter.export(entries, 'journal_report.pdf')
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
import time
import os
import re
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4, landscape, portrait
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
        Table, TableStyle, KeepTogether, Flowable,
        Frame, PageTemplate, BaseDocTemplate,
        CondPageBreak
    )
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not installed. PDF export functionality will be unavailable.")

from .base_exporter import BaseExporter, ExportOptions, ExportResult
from ..models import JournalEntry
from ..version import __version__ as VERSION
from ..utils.error_handler import DataValidationError as ValidationError

logger = logging.getLogger(__name__)


if REPORTLAB_AVAILABLE:
    class NumberedCanvas(canvas.Canvas):
        """Custom canvas for page numbering and headers/footers."""
        
        def __init__(self, *args, **kwargs):
            """Initialize canvas with page tracking."""
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []
            self.page_offset = 0
            
        def showPage(self):
            """Save page state before showing."""
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
            
        def save(self):
            """Add page numbers and headers/footers to all pages."""
            num_pages = len(self._saved_page_states)
            for state in self._saved_page_states:
                self.__dict__.update(state)
                if hasattr(self, '_page_number'):
                    self.draw_page_number()
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)
            
        def draw_page_number(self):
            """Draw page number at bottom of page."""
            self.saveState()
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#8B7355"))
            
            # Skip page numbers on first few pages (cover, TOC)
            if self._pageNumber > self.page_offset:
                page_num = self._pageNumber - self.page_offset
                self.drawRightString(
                    letter[0] - inch,
                    0.75 * inch,
                    f"Page {page_num}"
                )
                
            # Add header
            self.drawString(inch, letter[1] - 0.75 * inch, "Health Journal")
            self.drawRightString(
                letter[0] - inch,
                letter[1] - 0.75 * inch,
                datetime.now().strftime("%B %Y")
            )
            
            # Draw header line
            self.setStrokeColor(colors.HexColor("#E8DCC8"))
            self.setLineWidth(0.5)
            self.line(inch, letter[1] - 0.85 * inch, 
                     letter[0] - inch, letter[1] - 0.85 * inch)
            
            self.restoreState()


    class PDFExporter(BaseExporter):
        """PDF format exporter for journal entries.
        
        Exports journal entries to professionally formatted PDF documents with
        support for cover pages, table of contents, rich text formatting, and
        custom styling. Uses WSJ-inspired design principles for typography
        and color scheme.
        
        The PDF structure includes:
            - Cover page with title and date range
            - Table of contents with clickable links
            - Individual entry pages with proper formatting
            - Headers and footers with page numbers
            - Professional typography and spacing
        """
    
        # WSJ-inspired color palette
        if REPORTLAB_AVAILABLE:
            COLORS = {
                'primary': HexColor("#FF8C42"),      # Warm orange for headers
                'secondary': HexColor("#8B7355"),    # Brown for body text
                'accent': HexColor("#FFD166"),       # Light orange for highlights
                'background': HexColor("#FFF8F0"),   # Subtle warm background
                'border': HexColor("#E8DCC8"),       # Light border color
                'text_dark': HexColor("#5D4E37"),    # Dark brown for emphasis
                'text_light': HexColor("#A0896F")    # Light brown for metadata
            }
        else:
            COLORS = {}
        
        def __init__(self, options: Optional[ExportOptions] = None):
            """Initialize PDF exporter with options.
            
            Args:
                options: Export configuration options.
            """
            super().__init__(options)
            self.styles = self._create_styles()
            self.toc = TableOfContents()
            self.story = []
            
        def export(self, entries: List[JournalEntry], output_path: str) -> ExportResult:
            """Export journal entries to PDF file.
            
            Creates a professionally formatted PDF document containing all
            journal entries with proper structure and styling.
            
            Args:
                entries: List of journal entries to export.
                output_path: Path where the PDF file should be saved.
                
            Returns:
                ExportResult: Export operation results and statistics.
                
            Raises:
                ValidationError: If entries are invalid.
                IOError: If file cannot be written.
            """
            if not REPORTLAB_AVAILABLE:
                return ExportResult(
                    success=False,
                    error_message="PDF export is not available. Please install reportlab: pip install reportlab",
                    entries_exported=0,
                    file_path=output_path,
                    file_size=0,
                    export_duration=0.0,
                    warnings=["ReportLab library not installed"]
                )
                
            self._start_time = time.time()
            
            # Validate entries
            warnings = self.validate_entries(entries)
            
            # Ensure output directory exists
            self.ensure_output_directory(output_path)
            
            # Apply max entries limit if specified
            if self.options.max_entries and len(entries) > self.options.max_entries:
                entries = entries[:self.options.max_entries]
                warnings.append(f"Limited export to {self.options.max_entries} entries")
            
            try:
                # Create PDF document
                doc = self._create_document(output_path)
                
                # Build document story
                self.story = []
                
                # Add cover page if requested
                if self.options.extra_options.get('include_cover', True):
                    self._add_cover_page(entries)
                    self.story.append(PageBreak())
                
                # Add table of contents if requested
                if self.options.extra_options.get('include_toc', True) and len(entries) > 5:
                    self._add_table_of_contents()
                    self.story.append(PageBreak())
                
                # Add entries
                self._add_entries(entries)
                
                # Build PDF
                doc.build(self.story, canvasmaker=NumberedCanvas)
                
                # Calculate final statistics
                duration = time.time() - self._start_time
                file_size = self.calculate_file_size(output_path)
                
                logger.info(f"Exported {len(entries)} entries to PDF: {output_path}")
                
                return ExportResult(
                    success=True,
                    entries_exported=len(entries),
                    file_path=output_path,
                    file_size=file_size,
                    export_duration=duration,
                    warnings=warnings,
                    metadata={
                        'pdf_pages': self._estimate_page_count(entries),
                        'include_toc': self.options.extra_options.get('include_toc', True),
                        'include_cover': self.options.extra_options.get('include_cover', True)
                    }
                )
                
            except Exception as e:
                logger.error(f"PDF export failed: {e}")
                return ExportResult(
                    success=False,
                    error_message=str(e),
                    warnings=warnings,
                    export_duration=time.time() - self._start_time
                )
        
        def _create_document(self, output_path: str) -> SimpleDocTemplate:
            """Create the PDF document with proper settings.
            
            Args:
                output_path: Path for the PDF file.
                
            Returns:
                SimpleDocTemplate: Configured document template.
            """
            # Get page size
            page_size_name = self.options.extra_options.get('page_size', 'letter').lower()
            page_size = letter if page_size_name == 'letter' else A4
            
            # Create document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=page_size,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
                title="Health Journal Export",
                author="Apple Health Monitor",
                subject=f"Journal entries export - {datetime.now().strftime('%B %d, %Y')}",
                creator=f"Apple Health Monitor v{VERSION}"
            )
            
            return doc
        
        def _create_styles(self) -> Dict[str, ParagraphStyle]:
            """Create custom paragraph styles for the PDF.
            
            Returns:
                Dict mapping style names to ParagraphStyle objects.
            """
            styles = {}
            
            # Title style
            styles['Title'] = ParagraphStyle(
                'Title',
                parent=getSampleStyleSheet()['Title'],
                fontSize=28,
                textColor=self.COLORS['primary'],
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            # Subtitle style
            styles['Subtitle'] = ParagraphStyle(
                'Subtitle',
                fontSize=18,
                textColor=self.COLORS['secondary'],
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica'
            )
            
            # Entry title style
            styles['EntryTitle'] = ParagraphStyle(
                'EntryTitle',
                fontSize=16,
                textColor=self.COLORS['primary'],
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold',
                keepWithNext=True
            )
            
            # Entry metadata style
            styles['EntryMeta'] = ParagraphStyle(
                'EntryMeta',
                fontSize=10,
                textColor=self.COLORS['text_light'],
                spaceAfter=10,
                fontName='Helvetica-Oblique'
            )
            
            # Body text style
            styles['BodyText'] = ParagraphStyle(
                'BodyText',
                fontSize=11,
                textColor=self.COLORS['text_dark'],
                spaceAfter=12,
                alignment=TA_JUSTIFY,
                fontName='Helvetica',
                leading=16
            )
            
            # TOC styles
            styles['TOCHeading'] = ParagraphStyle(
                'TOCHeading',
                fontSize=20,
                textColor=self.COLORS['primary'],
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            styles['TOCEntry'] = ParagraphStyle(
                'TOCEntry',
                fontSize=11,
                textColor=self.COLORS['secondary'],
                leftIndent=20,
                spaceAfter=5,
                fontName='Helvetica'
            )
            
            return styles
        
        def _add_cover_page(self, entries: List[JournalEntry]) -> None:
            """Add cover page to the document.
            
            Args:
                entries: List of entries for date range calculation.
            """
            # Title
            self.story.append(Spacer(1, 2 * inch))
            self.story.append(
                Paragraph("My Health Journal", self.styles['Title'])
            )
            
            # Subtitle
            self.story.append(
                Paragraph("Personal Health Reflections", self.styles['Subtitle'])
            )
            
            self.story.append(Spacer(1, inch))
            
            # Date range
            if entries:
                min_date = min(e.entry_date for e in entries)
                max_date = max(e.entry_date for e in entries)
                date_range = f"{min_date.strftime('%B %d, %Y')} - {max_date.strftime('%B %d, %Y')}"
            else:
                date_range = "No entries"
                
            self.story.append(
                Paragraph(date_range, self.styles['Subtitle'])
            )
            
            # Entry count
            self.story.append(Spacer(1, 0.5 * inch))
            entry_count_text = f"{len(entries)} Journal Entries"
            self.story.append(
                Paragraph(entry_count_text, self.styles['BodyText'])
            )
            
            # Export info
            self.story.append(Spacer(1, 2 * inch))
            export_info = f"Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
            self.story.append(
                Paragraph(export_info, self.styles['EntryMeta'])
            )
        
        def _add_table_of_contents(self) -> None:
            """Add table of contents to the document."""
            self.story.append(
                Paragraph("Table of Contents", self.styles['TOCHeading'])
            )
            self.story.append(Spacer(1, 0.5 * inch))
            
            # TOC will be populated during build
            self.story.append(self.toc)
        
        def _add_entries(self, entries: List[JournalEntry]) -> None:
            """Add all journal entries to the document.
            
            Args:
                entries: List of entries to add.
            """
            total = len(entries)
            
            for i, entry in enumerate(entries):
                # Update progress
                progress = ((i + 1) / total) * 100
                self.update_progress(progress)
                
                # Add entry
                self._add_single_entry(entry, i)
                
                # Add page break between entries (except last)
                if i < total - 1:
                    self.story.append(CondPageBreak(3 * inch))
        
        def _add_single_entry(self, entry: JournalEntry, index: int) -> None:
            """Add a single journal entry to the document.
            
            Args:
                entry: Journal entry to add.
                index: Entry index for TOC.
            """
            # Entry title with date and type
            title_text = f"{entry.entry_date.strftime('%B %d, %Y')} - {self.get_entry_type_display(entry.entry_type)}"
            entry_title = Paragraph(title_text, self.styles['EntryTitle'])
            
            # Add to TOC
            self.toc.addEntry(0, title_text, index)
            
            # Entry metadata
            meta_parts = []
            if entry.created_at:
                meta_parts.append(f"Created: {entry.created_at.strftime('%I:%M %p')}")
            if entry.updated_at and entry.updated_at != entry.created_at:
                meta_parts.append(f"Updated: {entry.updated_at.strftime('%I:%M %p')}")
            meta_parts.append(f"Words: {len(entry.content.split())}")
            
            meta_text = " | ".join(meta_parts)
            entry_meta = Paragraph(meta_text, self.styles['EntryMeta'])
            
            # Keep title and metadata together
            header = KeepTogether([entry_title, entry_meta, Spacer(1, 0.2 * inch)])
            self.story.append(header)
            
            # Process content (handle markdown if enabled)
            if self.options.extra_options.get('parse_markdown', True):
                content_paragraphs = self._parse_markdown_content(entry.content)
            else:
                content_paragraphs = self._parse_plain_content(entry.content)
            
            # Add content paragraphs
            for para in content_paragraphs:
                self.story.append(para)
        
        def _parse_plain_content(self, content: str) -> List[Flowable]:
            """Parse plain text content into paragraphs.
            
            Args:
                content: Plain text content.
                
            Returns:
                List of Flowable objects.
            """
            flowables = []
            
            # Split into paragraphs
            paragraphs = content.split('\n\n')
            
            for para_text in paragraphs:
                if para_text.strip():
                    # Handle line breaks within paragraphs
                    para_text = para_text.replace('\n', '<br/>')
                    flowables.append(
                        Paragraph(self._escape_xml(para_text), self.styles['BodyText'])
                    )
                    
            return flowables
        
        def _parse_markdown_content(self, content: str) -> List[Flowable]:
            """Parse markdown content into formatted paragraphs.
            
            Supports basic markdown formatting:
            - **bold** and *italic*
            - Headers (# ## ###)
            - Lists (- and 1.)
            - Blockquotes (>)
            
            Args:
                content: Markdown formatted content.
                
            Returns:
                List of Flowable objects.
            """
            flowables = []
            lines = content.split('\n')
            current_list = []
            in_blockquote = False
            blockquote_lines = []
            
            for line in lines:
                # Handle blockquotes
                if line.startswith('>'):
                    in_blockquote = True
                    blockquote_lines.append(line[1:].strip())
                    continue
                elif in_blockquote and line.strip() == '':
                    # End blockquote
                    if blockquote_lines:
                        quote_text = ' '.join(blockquote_lines)
                        quote_style = ParagraphStyle(
                            'Blockquote',
                            parent=self.styles['BodyText'],
                            leftIndent=20,
                            rightIndent=20,
                            textColor=self.COLORS['text_light'],
                            fontName='Helvetica-Oblique'
                        )
                        flowables.append(Paragraph(self._format_markdown_inline(quote_text), quote_style))
                        flowables.append(Spacer(1, 6))
                    blockquote_lines = []
                    in_blockquote = False
                    continue
                
                # Handle headers
                if line.startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    header_text = line.lstrip('#').strip()
                    if header_text:
                        header_style = ParagraphStyle(
                            f'Header{level}',
                            fontSize=16 - (level * 2),
                            textColor=self.COLORS['primary'],
                            spaceAfter=10,
                            spaceBefore=15,
                            fontName='Helvetica-Bold'
                        )
                        flowables.append(Paragraph(self._format_markdown_inline(header_text), header_style))
                    continue
                
                # Handle lists
                if line.strip().startswith('- ') or re.match(r'^\d+\.\s', line.strip()):
                    current_list.append(line.strip())
                    continue
                elif current_list and line.strip() == '':
                    # End list
                    self._add_list_to_story(current_list, flowables)
                    current_list = []
                    continue
                
                # Handle regular paragraphs
                if line.strip():
                    formatted_text = self._format_markdown_inline(line)
                    flowables.append(Paragraph(formatted_text, self.styles['BodyText']))
                elif flowables and not isinstance(flowables[-1], Spacer):
                    flowables.append(Spacer(1, 6))
            
            # Handle any remaining list items
            if current_list:
                self._add_list_to_story(current_list, flowables)
                
            # Handle any remaining blockquote
            if blockquote_lines:
                quote_text = ' '.join(blockquote_lines)
                quote_style = ParagraphStyle(
                    'Blockquote',
                    parent=self.styles['BodyText'],
                    leftIndent=20,
                    rightIndent=20,
                    textColor=self.COLORS['text_light'],
                    fontName='Helvetica-Oblique'
                )
                flowables.append(Paragraph(self._format_markdown_inline(quote_text), quote_style))
            
            return flowables
        
        def _format_markdown_inline(self, text: str) -> str:
            """Format inline markdown elements (bold, italic).
            
            Args:
                text: Text with markdown formatting.
                
            Returns:
                Text with ReportLab XML tags.
            """
            # Escape XML first
            text = self._escape_xml(text)
            
            # Bold: **text** -> <b>text</b>
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            
            # Italic: *text* -> <i>text</i>  
            text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
            
            # Code: `code` -> <font name="Courier">code</font>
            text = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', text)
            
            return text
        
        def _add_list_to_story(self, list_items: List[str], flowables: List[Flowable]) -> None:
            """Add a list to the story.
            
            Args:
                list_items: List item strings.
                flowables: List to append flowables to.
            """
            list_data = []
            
            for item in list_items:
                if item.startswith('- '):
                    bullet = '•'
                    text = item[2:]
                else:
                    match = re.match(r'^(\d+)\.\s(.+)', item)
                    if match:
                        bullet = f"{match.group(1)}."
                        text = match.group(2)
                    else:
                        bullet = '•'
                        text = item
                        
                formatted_text = self._format_markdown_inline(text)
                list_data.append([bullet, Paragraph(formatted_text, self.styles['BodyText'])])
            
            if list_data:
                list_table = Table(list_data, colWidths=[0.3*inch, None])
                list_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (0, -1), 0),
                    ('RIGHTPADDING', (0, 0), (0, -1), 10),
                    ('LEFTPADDING', (1, 0), (1, -1), 0),
                ]))
                flowables.append(list_table)
                flowables.append(Spacer(1, 6))
        
        def _escape_xml(self, text: str) -> str:
            """Escape XML special characters.
            
            Args:
                text: Text to escape.
                
            Returns:
                XML-safe text.
            """
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            text = text.replace('"', '&quot;')
            text = text.replace("'", '&apos;')
            return text
        
        def _estimate_page_count(self, entries: List[JournalEntry]) -> int:
            """Estimate the number of pages in the PDF.
            
            Args:
                entries: List of entries.
                
            Returns:
                Estimated page count.
            """
            # Rough estimation: 
            # Cover page: 1
            # TOC: 1-2 pages depending on entry count
            # Each entry: ~0.5-2 pages depending on length
            
            pages = 1  # Cover
            
            if self.options.extra_options.get('include_toc', True) and len(entries) > 5:
                pages += max(1, len(entries) // 30)  # TOC
                
            # Estimate based on word count
            for entry in entries:
                word_count = len(entry.content.split())
                # Roughly 250-300 words per page
                pages += max(0.5, word_count / 275)
                
            return int(pages + 0.5)  # Round up


else:
    # Fallback PDFExporter when reportlab is not available
    class PDFExporter(BaseExporter):
        """Stub PDF exporter when reportlab is not installed."""
        
        def __init__(self, options: Optional[ExportOptions] = None):
            """Initialize stub PDF exporter."""
            super().__init__(options)
            logging.warning("PDFExporter initialized without reportlab support")
            
        def export(self, entries: List[JournalEntry], output_path: str) -> ExportResult:
            """Return error result when reportlab is not available."""
            return ExportResult(
                success=False,
                error_message="PDF export is not available. Please install reportlab: pip install reportlab",
                entries_exported=0,
                file_path=output_path,
                file_size=0,
                export_duration=0.0,
                warnings=["ReportLab library not installed"]
            )