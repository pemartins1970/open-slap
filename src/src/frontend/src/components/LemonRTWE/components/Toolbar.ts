import { EditorConfig } from '../types/index';

export class Toolbar {
  private container: HTMLElement;
  private config: EditorConfig;
  private onCommand: (command: string, value?: string) => void;

  constructor(container: HTMLElement, config: EditorConfig, onCommand: (command: string, value?: string) => void) {
    this.container = container;
    this.config = config;
    this.onCommand = onCommand;
    this.render();
  }

  private render() {
    const toolbar = document.createElement('div');
    toolbar.className = 'lemon-toolbar';
    
    const buttons = this.createButtons();
    toolbar.appendChild(buttons);
    
    this.container.appendChild(toolbar);
  }

  private createButtons(): HTMLElement {
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'toolbar-group';
    
    // Font and size selectors
    const fontSelect = this.createFontSelector();
    const sizeSelect = this.createSizeSelector();
    buttonGroup.appendChild(fontSelect);
    buttonGroup.appendChild(sizeSelect);
    
    const separator1 = document.createElement('span');
    separator1.className = 'toolbar-separator';
    buttonGroup.appendChild(separator1);
    
    const defaultButtons = [
      { command: 'bold', icon: '<strong>B</strong>', title: 'Negrito' },
      { command: 'italic', icon: '<em>I</em>', title: 'Itálico' },
      { command: 'underline', icon: '<u>U</u>', title: 'Sublinhado' },
      { command: 'strikethrough', icon: '<s>S</s>', title: 'Riscado' }
    ];
    
    const separator2 = document.createElement('span');
    separator2.className = 'toolbar-separator';
    
    const alignmentButtons = [
      { command: 'justifyLeft', icon: '≡', title: 'Alinhar à esquerda' },
      { command: 'justifyCenter', icon: '≡', title: 'Centralizar' },
      { command: 'justifyRight', icon: '≡', title: 'Alinhar à direita' },
      { command: 'justifyFull', icon: '≡', title: 'Justificar' }
    ];
    
    const separator3 = document.createElement('span');
    separator3.className = 'toolbar-separator';
    
    const listButtons = [
      { command: 'insertUnorderedList', icon: '•', title: 'Lista não ordenada' },
      { command: 'insertOrderedList', icon: '1.', title: 'Lista ordenada' }
    ];
    
    const separator4 = document.createElement('span');
    separator4.className = 'toolbar-separator';
    
    const indentButtons = [
      { command: 'outdent', icon: '←', title: 'Diminuir recuo' },
      { command: 'indent', icon: '→', title: 'Aumentar recuo' }
    ];
    
    const separator5 = document.createElement('span');
    separator5.className = 'toolbar-separator';
    
    const mediaButtons = [
      { command: 'link', icon: '🔗', title: 'Inserir link' },
      { command: 'image', icon: '🖼️', title: 'Inserir imagem' },
      { command: 'table', icon: '⊞', title: 'Inserir tabela' },
      { command: 'video', icon: '▶', title: 'Inserir vídeo' }
    ];
    
    const separator6 = document.createElement('span');
    separator6.className = 'toolbar-separator';
    
    const actionButtons = [
      { command: 'undo', icon: '↶', title: 'Desfazer' },
      { command: 'redo', icon: '↷', title: 'Refazer' },
      { command: 'fullscreen', icon: '⛶', title: 'Tela cheia' }
    ];
    
    const allButtons = [
      ...defaultButtons,
      separator2,
      ...alignmentButtons,
      separator3,
      ...listButtons,
      separator4,
      ...indentButtons,
      separator5,
      ...mediaButtons,
      separator6,
      ...actionButtons
    ];

    const toolbarConfig = this.config.toolbar || {};
    
    allButtons.forEach(item => {
      if (item.command === 'separator') {
        buttonGroup.appendChild(item);
        return;
      }
      
      if (toolbarConfig[item.command as keyof typeof toolbarConfig] !== false) {
        const button = document.createElement('button');
        button.className = `toolbar-button toolbar-${item.command}`;
        button.innerHTML = item.icon;
        button.setAttribute('data-tooltip', item.title);
        button.type = 'button';
        
        button.addEventListener('click', () => {
          if (item.command === 'link') {
            const url = prompt('Digite a URL do link:');
            if (url) this.onCommand('createLink', url);
          } else if (item.command === 'image') {
            this.insertImage();
          } else if (item.command === 'video') {
            this.insertVideo();
          } else if (item.command === 'table') {
            this.insertTable();
          } else if (item.command === 'fullscreen') {
            this.toggleFullscreen();
          } else {
            this.onCommand(item.command);
          }
        });
        
        buttonGroup.appendChild(button);
      }
    });

    return buttonGroup;
  }

  private insertImage() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const url = e.target?.result as string;
          this.onCommand('insertImage', url);
        };
        reader.readAsDataURL(file);
      }
    };
    input.click();
  }

  private insertVideo() {
    const url = prompt('Digite a URL do vídeo do YouTube:');
    if (url) {
      this.onCommand('insertVideo', url);
    }
  }

  private insertTable() {
    const tableHtml = `
      <table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <tr><th>Cabeçalho 1</th><th>Cabeçalho 2</th></tr>
        <tr><td>Célula 1</td><td>Célula 2</td></tr>
        <tr><td>Célula 3</td><td>Célula 4</td></tr>
      </table>
    `;
    this.onCommand('insertHTML', tableHtml);
  }

  private toggleFullscreen() {
    // Procura o container .lemon-editor para adicionar a classe fullscreen
    const editor = this.container.closest('.lemon-editor') || this.container.querySelector('.lemon-editor');
    if (editor) {
      editor.classList.toggle('fullscreen');
    } else {
      console.warn('Container do editor não encontrado para fullscreen');
    }
  }

  private createFontSelector(): HTMLElement {
    const select = document.createElement('select');
    select.className = 'toolbar-select';
    select.setAttribute('data-tooltip', 'Fonte');
    
    const fonts = [
      { value: 'Arial', text: 'Arial' },
      { value: 'Times New Roman', text: 'Times' },
      { value: 'Courier New', text: 'Courier' },
      { value: 'Georgia', text: 'Georgia' },
      { value: 'Verdana', text: 'Verdana' }
    ];
    
    fonts.forEach(font => {
      const option = document.createElement('option');
      option.value = font.value;
      option.textContent = font.text;
      select.appendChild(option);
    });
    
    select.addEventListener('change', () => {
      this.onCommand('fontName', select.value);
    });
    
    return select;
  }

  private createSizeSelector(): HTMLElement {
    const select = document.createElement('select');
    select.className = 'toolbar-select';
    select.setAttribute('data-tooltip', 'Tamanho');
    
    const sizes = [
      { value: '1', text: 'Pequeno' },
      { value: '2', text: 'Menor' },
      { value: '3', text: 'Normal' },
      { value: '4', text: 'Médio' },
      { value: '5', text: 'Grande' },
      { value: '6', text: 'Maior' },
      { value: '7', text: 'Enorme' }
    ];
    
    sizes.forEach(size => {
      const option = document.createElement('option');
      option.value = size.value;
      option.textContent = size.text;
      if (size.value === '3') option.selected = true;
      select.appendChild(option);
    });
    
    select.addEventListener('change', () => {
      this.onCommand('fontSize', select.value);
    });
    
    return select;
  }
}