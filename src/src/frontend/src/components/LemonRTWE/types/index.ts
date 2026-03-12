export interface EditorConfig {
  container: HTMLElement | string;
  content?: string;
  theme?: 'light' | 'dark';
  toolbar?: {
    bold?: boolean;
    italic?: boolean;
    underline?: boolean;
    strikethrough?: boolean;
    heading?: boolean;
    list?: boolean;
    link?: boolean;
    image?: boolean;
    video?: boolean;
    markdown?: boolean;
    undo?: boolean;
    redo?: boolean;
  };
  markdown?: boolean;
  dragDrop?: boolean;
  textWrap?: boolean;
}

export interface Position {
  x: number;
  y: number;
}

export interface DraggableElement {
  id: string;
  element: HTMLElement;
  position: Position;
  type: 'image' | 'video' | 'iframe';
}

export interface MarkdownConfig {
  enablePreview?: boolean;
  liveSync?: boolean;
  shortcuts?: boolean;
}