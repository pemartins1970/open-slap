import { EditorConfig } from '../types/index';
import { MarkdownParser } from '../utils/markdown';
import { DraggableManager } from '../utils/draggable';
import { TextWrapManager } from '../utils/textwrap';
import TurndownService from 'turndown';

export class LemonEditor {
  private container: HTMLElement;
  private editor: HTMLElement;
  private toolbar: HTMLElement;
  private config: EditorConfig;
  private markdownParser: MarkdownParser;
  private draggableManager: DraggableManager;
  private textWrapManager: TextWrapManager;
  private turndownService: TurndownService;
  private isMarkdownMode = false;

  constructor(config: EditorConfig) {
    this.config = { ...config };
    this.markdownParser = new MarkdownParser();
    this.turndownService = new TurndownService({
      headingStyle: 'atx',
      codeBlockStyle: 'fenced'
    });
    
    if (typeof config.container === 'string') {
      this.container = document.querySelector(config.container) as HTMLElement;
    } else {
      this.container = config.container;
    }
    
    if (!this.container) {
      throw new Error('Container element not found');
    }

    this.init();
  }

  private init() {
    this.setupContainer();
    this.createEditor();
    this.setupDragAndDrop();
    this.setupMarkdown();
    this.loadContent();
  }

  private setupContainer() {
    this.container.className = `lemon-editor lemon-${this.config.theme || 'light'}`;
    this.container.innerHTML = '';
  }

  private createEditor() {
    // Create toolbar
    this.toolbar = document.createElement('div');
    this.toolbar.className = 'lemon-toolbar-container';
    
    // Create editor area
    this.editor = document.createElement('div');
    this.editor.className = 'lemon-editor-content';
    this.editor.contentEditable = 'true';
    this.editor.innerHTML = this.config.content || '<p>Start typing...</p>';
    
    this.container.appendChild(this.toolbar);
    this.container.appendChild(this.editor);
    
    // Initialize toolbar component
    this.setupToolbar();
    
    // Setup editor events
    this.setupEditorEvents();
  }

  private setupToolbar() {
    import('./Toolbar').then(({ Toolbar }) => {
      new Toolbar(this.toolbar, this.config, this.handleCommand.bind(this));
    });
  }

  private handleCommand(command: string, value?: string) {
    if (command === 'markdown') {
      this.toggleMarkdown();
      return;
    }
    
    this.editor.focus();
    if (value) {
      document.execCommand(command, false, value);
    } else {
      document.execCommand(command, false);
    }
    
    this.setupDraggableElements();
    this.setupTextWrapping();
  }

  private setupEditorEvents() {
    this.editor.addEventListener('paste', this.handlePaste.bind(this));
    this.editor.addEventListener('input', this.handleInput.bind(this));
    this.editor.addEventListener('keydown', this.handleKeydown.bind(this));
  }

  private handlePaste(e: ClipboardEvent) {
    e.preventDefault();
    const text = e.clipboardData?.getData('text/plain') || '';
    const html = e.clipboardData?.getData('text/html') || '';
    
    if (this.isMarkdownMode && text) {
      const markdownHtml = this.markdownParser.parse(text);
      document.execCommand('insertHTML', false, markdownHtml);
    } else if (html) {
      document.execCommand('insertHTML', false, html);
    } else {
      document.execCommand('insertText', false, text);
    }
  }

  private handleInput() {
    this.setupDraggableElements();
    this.setupTextWrapping();
  }

  private handleKeydown(e: KeyboardEvent) {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 'b':
          e.preventDefault();
          this.handleCommand('bold');
          break;
        case 'i':
          e.preventDefault();
          this.handleCommand('italic');
          break;
        case 'u':
          e.preventDefault();
          this.handleCommand('underline');
          break;
        case 'm':
          e.preventDefault();
          this.toggleMarkdown();
          break;
      }
    }
  }

  private setupDragAndDrop() {
    if (this.config.dragDrop !== false) {
      this.draggableManager = new DraggableManager(this.editor);
      this.setupDraggableElements();
    }
  }

  private setupDraggableElements() {
    const images = this.editor.querySelectorAll('img[data-draggable="true"]');
    images.forEach(img => {
      if (!img.dataset.draggableInitialized) {
        this.draggableManager?.makeDraggable(img as HTMLElement);
        img.dataset.draggableInitialized = 'true';
      }
    });
  }

  private setupTextWrapping() {
    if (this.config.textWrap !== false) {
      this.textWrapManager = new TextWrapManager(this.editor);
      this.setupTextWrapControls();
    }
  }

  private setupTextWrapControls() {
    const images = this.editor.querySelectorAll('img:not(.text-wrapped-control)');
    images.forEach(img => {
      if (img.dataset.wrapControlInitialized) return;
      
      this.textWrapManager?.createWrapControl(img as HTMLElement);
      this.textWrapManager?.enableTextWrap(img as HTMLElement, 'both');
      img.dataset.wrapControlInitialized = 'true';
    });
  }

  private setupMarkdown() {
    if (this.config.markdown !== false) {
      this.setupMarkdownShortcuts();
    }
  }

  private setupMarkdownShortcuts() {
    // Markdown shortcuts will be handled here
  }

  private toggleMarkdown() {
    this.isMarkdownMode = !this.isMarkdownMode;
    
    if (this.isMarkdownMode) {
      const content = this.editor.innerHTML;
      const markdown = this.htmlToMarkdown(content);
      
      // Hide WYSIWYG editor
      this.editor.style.display = 'none';
      
      // Create or show Markdown textarea
      let textarea = this.container.querySelector('.lemon-markdown-editor') as HTMLTextAreaElement;
      if (!textarea) {
        textarea = document.createElement('textarea');
        textarea.className = 'lemon-markdown-editor markdown-editor';
        this.container.appendChild(textarea);
      }
      
      textarea.value = markdown;
      textarea.style.display = 'block';
      textarea.focus();
      
      // Update toolbar state if needed
    } else {
      const textarea = this.container.querySelector('.lemon-markdown-editor') as HTMLTextAreaElement;
      if (textarea) {
        const markdown = textarea.value;
        const html = this.markdownParser.parse(markdown);
        
        textarea.style.display = 'none';
        this.editor.innerHTML = html;
        this.editor.style.display = 'block';
        this.editor.focus();
      }
    }
  }

  private htmlToMarkdown(html: string): string {
    return this.turndownService.turndown(html);
  }

  private loadContent() {
    if (this.config.content) {
      if (this.isMarkdownMode) {
        const html = this.markdownParser.parse(this.config.content);
        this.editor.innerHTML = html;
      } else {
        this.editor.innerHTML = this.config.content;
      }
    }
  }

  public getContent(): string {
    if (this.isMarkdownMode) {
      const textarea = this.container.querySelector('.lemon-markdown-editor') as HTMLTextAreaElement;
      return textarea ? textarea.value : '';
    }
    return this.editor.innerHTML;
  }

  public setContent(content: string) {
    if (this.isMarkdownMode) {
      const textarea = this.container.querySelector('.lemon-markdown-editor') as HTMLTextAreaElement;
      if (textarea) {
        textarea.value = content;
      }
    } else {
      this.editor.innerHTML = content;
    }
    this.setupDraggableElements();
    this.setupTextWrapControls();
  }

  public destroy() {
    this.draggableManager?.destroy();
    this.container.innerHTML = '';
  }
}