---
task_id: T07_S06
sprint_sequence_id: S06
status: open
complexity: High
last_updated: 2025-01-28T00:00:00Z
dependencies: ["T01_S06", "T05_S06"]
---

# Task: Journal Export Functionality (JSON/PDF)

## Description
Implement export functionality to allow users to export their journal entries in JSON and PDF formats. This includes single entry export, date range export, and full journal export with proper formatting and metadata.

## Goal / Objectives
- Export journal entries to JSON with full metadata
- Generate well-formatted PDF documents
- Support single, range, and full exports
- Include health metrics context in exports
- Ensure exports are readable and professional

## Acceptance Criteria
- [ ] JSON export includes all entry metadata
- [ ] PDF export has professional formatting
- [ ] Date range selection works for exports
- [ ] Export progress shown for large datasets
- [ ] PDF includes table of contents for multiple entries
- [ ] Exported files have meaningful names
- [ ] Export templates customizable
- [ ] Character encoding handled correctly
- [ ] Large exports don't freeze UI

## Implementation Analysis

### PDF Library Choice
**Options:**
1. **ReportLab** - Comprehensive PDF generation
   - Pros: Full control, professional output, charts support
   - Cons: Complex API, large dependency
2. **PyPDF2/pypdf** - Simple PDF manipulation
   - Pros: Lightweight, easy to use
   - Cons: Limited formatting, no HTML support
3. **WeasyPrint** - HTML/CSS to PDF
   - Pros: Web standards, easy styling, responsive
   - Cons: External dependencies, slower

**Recommendation:** ReportLab (#1) - Best for professional documents

### Export Architecture
**Options:**
1. **Synchronous Export** - Block UI during export
   - Pros: Simple implementation, predictable
   - Cons: UI freezes, poor UX for large exports
2. **Thread-based Export** - Background thread
   - Pros: UI responsive, progress updates
   - Cons: Thread management complexity
3. **Process-based Export** - Separate process
   - Pros: True parallelism, crash isolation
   - Cons: IPC complexity, memory overhead

**Recommendation:** Thread-based Export (#2) - Best balance

### Template Engine
**Options:**
1. **Jinja2** - Full template engine
   - Pros: Powerful, familiar syntax, reusable
   - Cons: Extra dependency
2. **Python f-strings** - Built-in formatting
   - Pros: No dependencies, fast
   - Cons: Limited features, less maintainable
3. **Custom Template System** - Purpose-built
   - Pros: Exact features needed
   - Cons: Reinventing wheel

**Recommendation:** Jinja2 (#1) - Flexibility for future needs

## Detailed Subtasks

### 1. Exporter Base Architecture
- [ ] Create src/exporters/base_exporter.py:
  ```python
  class BaseExporter(ABC):
      def __init__(self, journal_db: JournalDatabase):
          self.journal_db = journal_db
          self.progress = 0
          
      @abstractmethod
      def export(self, entries: List[JournalEntry], 
                output_path: str) -> None:
          pass
  ```
- [ ] Define common interfaces:
  - [ ] ExportOptions dataclass
  - [ ] ExportProgress callback
  - [ ] ExportResult with statistics
- [ ] Implement shared utilities:
  - [ ] File naming conventions
  - [ ] Progress calculation
  - [ ] Error handling base

### 2. JSON Exporter Implementation
- [ ] Create src/exporters/json_exporter.py:
  ```python
  class JSONExporter(BaseExporter):
      def export(self, entries, output_path):
          data = {
              "export_date": datetime.now().isoformat(),
              "version": "1.0",
              "entry_count": len(entries),
              "entries": [self.entry_to_dict(e) for e in entries]
          }
  ```
- [ ] Design JSON schema:
  ```json
  {
    "export_date": "2025-01-28T10:00:00",
    "version": "1.0",
    "metadata": {
      "app_version": "2.0.0",
      "export_range": "2024-01-01 to 2025-01-28"
    },
    "entries": [{
      "id": 123,
      "date": "2025-01-28",
      "type": "daily",
      "content": "...",
      "word_count": 250,
      "created_at": "...",
      "updated_at": "..."
    }]
  }
  ```
- [ ] Add export options:
  - [ ] Pretty print vs compact
  - [ ] Include/exclude metadata
  - [ ] Custom date format
- [ ] Implement streaming for large exports:
  ```python
  def export_streaming(self, query, output_path):
      with open(output_path, 'w') as f:
          f.write('{"entries": [')
          for i, entry in enumerate(self.stream_entries(query)):
              if i > 0: f.write(',')
              json.dump(entry, f)
          f.write(']}')
  ```

### 3. PDF Template Design
- [ ] Create template structure:
  ```python
  PDF_TEMPLATE = {
      "cover_page": {
          "title": "My Health Journal",
          "subtitle": "Personal Health Reflections",
          "date_range": "{start} - {end}",
          "logo": "assets/logo.png"
      },
      "entry_page": {
          "header": "{date} - {type}",
          "footer": "Page {page}",
          "margins": (72, 72, 72, 72)
      }
  }
  ```
- [ ] Design color scheme:
  - [ ] Primary: #FF8C42 (headers)
  - [ ] Secondary: #8B7355 (text)
  - [ ] Accent: #FFD166 (highlights)
  - [ ] Background: #FFF8F0 (subtle)
- [ ] Create page layouts:
  - [ ] Cover page with summary
  - [ ] Table of contents
  - [ ] Entry pages with metadata
  - [ ] Index/appendix

### 4. PDF Exporter Implementation
- [ ] Create src/exporters/pdf_exporter.py:
  ```python
  class PDFExporter(BaseExporter):
      def __init__(self, journal_db):
          super().__init__(journal_db)
          self.styles = self.create_styles()
          
      def create_styles(self):
          return {
              'title': ParagraphStyle(
                  fontSize=24,
                  textColor=colors.HexColor('#FF8C42'),
                  spaceAfter=30
              )
          }
  ```
- [ ] Implement document structure:
  - [ ] Cover page generation
  - [ ] TOC with page numbers
  - [ ] Entry formatting
  - [ ] Page headers/footers
- [ ] Add rich text support:
  - [ ] Parse markdown to PDF
  - [ ] Handle bold/italic
  - [ ] Support lists
  - [ ] Include blockquotes
- [ ] Implement pagination:
  ```python
  class PageNumberCanvas(canvas.Canvas):
      def __init__(self, *args, **kwargs):
          canvas.Canvas.__init__(self, *args, **kwargs)
          self.pages = []
  ```

### 5. Export Dialog UI
- [ ] Create ExportDialog(QDialog):
  ```python
  class ExportDialog(QDialog):
      def __init__(self, parent=None):
          self.format_selector = QComboBox()
          self.date_range_widget = DateRangeSelector()
          self.options_stack = QStackedWidget()
  ```
- [ ] Design dialog layout:
  - [ ] Format selection (JSON/PDF)
  - [ ] Date range picker
  - [ ] Format-specific options
  - [ ] Preview area
  - [ ] Export button
- [ ] Add validation:
  - [ ] Check date range validity
  - [ ] Verify output path
  - [ ] Estimate export size
- [ ] Style with warm theme:
  ```css
  QDialog {
      background-color: #FFF8F0;
  }
  QPushButton {
      background-color: #FF8C42;
      color: white;
  }
  ```

### 6. Date Range Selection
- [ ] Create DateRangeSelector widget:
  ```python
  class DateRangeSelector(QWidget):
      def __init__(self):
          self.from_date = EnhancedDateEdit()
          self.to_date = EnhancedDateEdit()
          self.preset_combo = QComboBox()
  ```
- [ ] Add preset ranges:
  - [ ] "All entries"
  - [ ] "This year"
  - [ ] "Last 3 months"
  - [ ] "Last 30 days"
  - [ ] "Custom range"
- [ ] Implement validation:
  - [ ] To date >= From date
  - [ ] Not future dates
  - [ ] Show entry count
- [ ] Add calendar popup

### 7. Export Progress System
- [ ] Create ExportProgressDialog:
  ```python
  class ExportProgressDialog(QDialog):
      def __init__(self, total_entries):
          self.progress_bar = QProgressBar()
          self.status_label = QLabel()
          self.cancel_button = QPushButton("Cancel")
  ```
- [ ] Implement progress tracking:
  - [ ] Entry-level progress
  - [ ] Time estimation
  - [ ] Current entry display
  - [ ] Bytes written
- [ ] Add cancellation:
  - [ ] Thread interruption
  - [ ] Cleanup partial files
  - [ ] Restore UI state
- [ ] Show completion:
  - [ ] Success message
  - [ ] Open file location
  - [ ] Export statistics

### 8. Export Worker Thread
- [ ] Create ExportWorker(QThread):
  ```python
  class ExportWorker(QThread):
      progress = pyqtSignal(int, str)
      finished = pyqtSignal(bool, str)
      error = pyqtSignal(str)
      
      def run(self):
          try:
              self.exporter.export(self.entries, self.output_path)
          except Exception as e:
              self.error.emit(str(e))
  ```
- [ ] Implement thread safety:
  - [ ] Lock database access
  - [ ] Queue progress updates
  - [ ] Handle interruption
- [ ] Add performance optimizations:
  - [ ] Batch processing
  - [ ] Memory management
  - [ ] I/O buffering

### 9. Table of Contents Generation
- [ ] Create TOCGenerator:
  ```python
  class TOCGenerator:
      def generate(self, entries):
          toc = []
          for entry in entries:
              toc.append({
                  'title': self.format_title(entry),
                  'page': self.calculate_page(entry),
                  'level': self.determine_level(entry)
              })
  ```
- [ ] Implement TOC features:
  - [ ] Hierarchical structure
  - [ ] Page number alignment
  - [ ] Clickable links (PDF)
  - [ ] Section summaries
- [ ] Add TOC styling:
  - [ ] Indentation levels
  - [ ] Leader dots
  - [ ] Font variations

### 10. Markdown Support
- [ ] Integrate markdown parser:
  ```python
  import markdown
  
  class MarkdownProcessor:
      def to_pdf_elements(self, md_text):
          html = markdown.markdown(md_text)
          return self.html_to_reportlab(html)
  ```
- [ ] Support markdown features:
  - [ ] Headers (h1-h6)
  - [ ] Bold/italic
  - [ ] Lists (ordered/unordered)
  - [ ] Links
  - [ ] Code blocks
  - [ ] Blockquotes
- [ ] Add syntax highlighting:
  - [ ] Code language detection
  - [ ] Color schemes
  - [ ] Preserve formatting

### 11. Export Settings
- [ ] Create ExportSettings dialog:
  ```python
  class ExportSettings(QDialog):
      def __init__(self):
          self.pdf_settings = PDFSettingsWidget()
          self.json_settings = JSONSettingsWidget()
  ```
- [ ] PDF settings options:
  - [ ] Font family/size
  - [ ] Page margins
  - [ ] Include images
  - [ ] Color/grayscale
  - [ ] Page size (A4/Letter)
- [ ] JSON settings options:
  - [ ] Indentation
  - [ ] Date format
  - [ ] Include metadata
  - [ ] Compression
- [ ] Save user preferences

### 12. Batch Processing
- [ ] Implement chunked processing:
  ```python
  def export_in_chunks(self, entries, chunk_size=100):
      for i in range(0, len(entries), chunk_size):
          chunk = entries[i:i + chunk_size]
          self.process_chunk(chunk)
          self.update_progress(i + len(chunk))
  ```
- [ ] Add memory management:
  - [ ] Stream large content
  - [ ] Release processed entries
  - [ ] Monitor memory usage
- [ ] Optimize performance:
  - [ ] Parallel processing options
  - [ ] Caching repeated elements
  - [ ] Efficient I/O

### 13. Error Handling
- [ ] Implement comprehensive error handling:
  - [ ] File permission errors
  - [ ] Disk space checks
  - [ ] Invalid characters
  - [ ] Export interruption
- [ ] Create error recovery:
  ```python
  class ExportErrorHandler:
      def handle_error(self, error, context):
          if isinstance(error, PermissionError):
              return self.handle_permission_error(context)
  ```
- [ ] Add error reporting:
  - [ ] Detailed error messages
  - [ ] Recovery suggestions
  - [ ] Error log export

### 14. Testing
- [ ] Create tests/unit/test_exporters.py:
  - [ ] Test JSON structure
  - [ ] Test PDF generation
  - [ ] Test progress tracking
  - [ ] Test error handling
  - [ ] Test cancellation
  
- [ ] Create tests/integration/test_export_integration.py:
  - [ ] Test large exports (1000+ entries)
  - [ ] Test special characters
  - [ ] Test memory usage
  - [ ] Test UI responsiveness
  
- [ ] Create performance benchmarks:
  - [ ] Export speed metrics
  - [ ] Memory profiling
  - [ ] File size optimization

### 15. Documentation
- [ ] Create export user guide:
  - [ ] Step-by-step instructions
  - [ ] Format comparisons
  - [ ] Settings explanations
  - [ ] Troubleshooting
- [ ] Add developer documentation:
  - [ ] Exporter API
  - [ ] Template customization
  - [ ] Extension guide
- [ ] Create examples:
  - [ ] Sample exports
  - [ ] Custom templates
  - [ ] Integration code

## Output Log
[2025-01-28 00:00:00] Task created - Export functionality preserves journal entries externally