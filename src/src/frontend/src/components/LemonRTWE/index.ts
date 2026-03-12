import { EditorConfig } from './types/index';
import { LemonEditor } from './components/LemonEditor';
import { LemonEditorWrapper } from './LemonEditorWrapper';
import './styles/lemon-editor.css';

export class LemonRTWE {
  private editors: Map<string, LemonEditor> = new Map();

  constructor() {}

  public create(config: EditorConfig): LemonEditor {
    const editor = new LemonEditor(config);
    const id = this.generateId();
    this.editors.set(id, editor);
    return editor;
  }

  public createEditor(config: EditorConfig): LemonEditor {
    return this.create(config);
  }

  private generateId(): string {
    return `lemon-editor-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  public destroy(editor: LemonEditor): void {
    editor.destroy();
    for (const [id, ed] of this.editors.entries()) {
      if (ed === editor) {
        this.editors.delete(id);
        break;
      }
    }
  }

  public destroyAll(): void {
    for (const editor of this.editors.values()) {
      editor.destroy();
    }
    this.editors.clear();
  }
}

export { LemonEditorWrapper };
export type { EditorConfig };

// Global export
if (typeof window !== 'undefined') {
  (window as any).LemonRTWE = LemonRTWE;
}

export default LemonRTWE;