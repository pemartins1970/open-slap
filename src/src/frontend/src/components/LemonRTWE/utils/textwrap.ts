export class TextWrapManager {
  private container: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
  }

  public enableTextWrap(image: HTMLElement, wrapStyle: 'none' | 'left' | 'right' | 'both' = 'both') {
    image.style.float = wrapStyle === 'left' ? 'left' : wrapStyle === 'right' ? 'right' : 'none';
    
    const margin = '20px';
    image.style.marginLeft = wrapStyle === 'right' ? margin : '10px';
    image.style.marginRight = wrapStyle === 'left' ? margin : '10px';
    image.style.marginBottom = '10px';
    image.style.marginTop = '10px';

    this.container.style.overflow = 'hidden';
    
    // Clear any existing text wrapping styles
    this.clearTextWrap(image);
    
    // Apply the new wrapping style
    if (wrapStyle !== 'none') {
      image.classList.add('text-wrapped');
      image.dataset.wrapStyle = wrapStyle;
    }
  }

  public clearTextWrap(image: HTMLElement) {
    image.style.float = '';
    image.style.marginLeft = '';
    image.style.marginRight = '';
    image.style.marginBottom = '';
    image.style.marginTop = '';
    image.classList.remove('text-wrapped');
    delete image.dataset.wrapStyle;
  }

  public toggleTextWrap(image: HTMLElement) {
    const currentStyle = image.dataset.wrapStyle || 'none';
    let newStyle: 'none' | 'left' | 'right' | 'both';
    
    switch (currentStyle) {
      case 'none':
        newStyle = 'left';
        break;
      case 'left':
        newStyle = 'right';
        break;
      case 'right':
        newStyle = 'both';
        break;
      default:
        newStyle = 'none';
    }
    
    this.enableTextWrap(image, newStyle);
    return newStyle;
  }

  public createWrapControl(image: HTMLElement): HTMLElement {
    const control = document.createElement('div');
    control.className = 'text-wrap-control';
    control.innerHTML = `
      <button data-wrap="none" title="No wrap">⊡</button>
      <button data-wrap="left" title="Wrap left">⬅</button>
      <button data-wrap="right" title="Wrap right">➡</button>
      <button data-wrap="both" title="Wrap both">⬌</button>
    `;
    
    control.style.position = 'absolute';
    control.style.top = '-40px';
    control.style.left = '0';
    control.style.background = '#fff';
    control.style.border = '1px solid #ddd';
    control.style.borderRadius = '4px';
    control.style.padding = '4px';
    control.style.display = 'none';
    control.style.zIndex = '1001';
    control.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
    
    image.style.position = 'relative';
    image.appendChild(control);
    
    // Show/hide control on hover
    image.addEventListener('mouseenter', () => {
      control.style.display = 'block';
    });
    
    image.addEventListener('mouseleave', () => {
      control.style.display = 'none';
    });
    
    // Handle wrap button clicks
    control.querySelectorAll('button').forEach(button => {
      button.addEventListener('click', (e) => {
        e.stopPropagation();
        const wrapStyle = button.dataset.wrap as 'none' | 'left' | 'right' | 'both';
        this.enableTextWrap(image, wrapStyle);
      });
    });
    
    return control;
  }
}