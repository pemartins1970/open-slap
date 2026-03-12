export class DraggableManager {
  private draggables: Map<string, HTMLElement> = new Map();
  private isDragging = false;
  private currentElement: HTMLElement | null = null;
  private offset: { x: number; y: number } = { x: 0, y: 0 };
  private container: HTMLElement;
  private boundMouseMove: (e: MouseEvent) => void;
  private boundMouseUp: (e: MouseEvent) => void;
  private boundTouchMove: (e: TouchEvent) => void;
  private boundTouchEnd: (e: TouchEvent) => void;

  constructor(container: HTMLElement) {
    this.container = container;
    
    // Bind methods once
    this.boundMouseMove = this.handleMouseMove.bind(this);
    this.boundMouseUp = this.handleMouseUp.bind(this);
    this.boundTouchMove = this.handleTouchMove.bind(this);
    this.boundTouchEnd = this.handleTouchEnd.bind(this);
    
    this.setupEventListeners();
  }

  private setupEventListeners() {
    this.container.addEventListener('mousedown', this.handleMouseDown.bind(this));
    document.addEventListener('mousemove', this.boundMouseMove);
    document.addEventListener('mouseup', this.boundMouseUp);
    
    // Touch events for mobile
    this.container.addEventListener('touchstart', this.handleTouchStart.bind(this));
    document.addEventListener('touchmove', this.boundTouchMove);
    document.addEventListener('touchend', this.boundTouchEnd);
  }

  private handleMouseDown(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (target.dataset.draggable === 'true') {
      e.preventDefault();
      this.startDragging(target, e.clientX, e.clientY);
    }
  }

  private handleMouseMove(e: MouseEvent) {
    if (this.isDragging && this.currentElement) {
      e.preventDefault();
      this.updatePosition(e.clientX, e.clientY);
    }
  }

  private handleMouseUp() {
    this.stopDragging();
  }

  private handleTouchStart(e: TouchEvent) {
    const target = e.target as HTMLElement;
    if (target.dataset.draggable === 'true') {
      e.preventDefault();
      const touch = e.touches[0];
      this.startDragging(target, touch.clientX, touch.clientY);
    }
  }

  private handleTouchMove(e: TouchEvent) {
    if (this.isDragging && this.currentElement) {
      e.preventDefault();
      const touch = e.touches[0];
      this.updatePosition(touch.clientX, touch.clientY);
    }
  }

  private handleTouchEnd() {
    this.stopDragging();
  }

  private startDragging(element: HTMLElement, clientX: number, clientY: number) {
    this.isDragging = true;
    this.currentElement = element;
    
    const rect = element.getBoundingClientRect();
    this.offset.x = clientX - rect.left;
    this.offset.y = clientY - rect.top;
    
    element.style.position = 'absolute';
    element.style.cursor = 'grabbing';
    element.style.zIndex = '1000';
  }

  private updatePosition(clientX: number, clientY: number) {
    if (!this.currentElement) return;
    
    const containerRect = this.container.getBoundingClientRect();
    const x = clientX - containerRect.left - this.offset.x;
    const y = clientY - containerRect.top - this.offset.y;
    
    this.currentElement.style.left = `${x}px`;
    this.currentElement.style.top = `${y}px`;
  }

  private stopDragging() {
    if (this.currentElement) {
      this.currentElement.style.cursor = 'grab';
    }
    this.isDragging = false;
    this.currentElement = null;
  }

  public makeDraggable(element: HTMLElement) {
    element.dataset.draggable = 'true';
    element.style.cursor = 'grab';
    this.draggables.set(element.id || Date.now().toString(), element);
  }

  public destroy() {
    document.removeEventListener('mousemove', this.boundMouseMove);
    document.removeEventListener('mouseup', this.boundMouseUp);
    document.removeEventListener('touchmove', this.boundTouchMove);
    document.removeEventListener('touchend', this.boundTouchEnd);
  }
}