import React, { useEffect, useRef } from 'react';
import { LemonEditor } from './components/LemonEditor';
import './styles/lemon-editor.css';

interface LemonEditorWrapperProps {
  content?: string;
  onChange?: (content: string) => void;
  className?: string;
  theme?: 'light' | 'dark';
}

export const LemonEditorWrapper: React.FC<LemonEditorWrapperProps> = ({
  content = '',
  onChange,
  className = '',
  theme = 'light'
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<LemonEditor | null>(null);

  useEffect(() => {
    if (containerRef.current && !editorRef.current) {
      editorRef.current = new LemonEditor({
        container: containerRef.current,
        content,
        theme,
        markdown: true,
        dragDrop: true,
        textWrap: true,
        toolbar: {
          bold: true,
          italic: true,
          underline: true,
          strikethrough: true,
          heading: true,
          list: true,
          link: true,
          image: true,
          quote: true,
          code: true,
          markdown: true
        }
      });

      // Add input listener to propagate changes from WYSIWYG
      const editorElement = containerRef.current.querySelector('.lemon-editor-content');
      if (editorElement) {
        editorElement.addEventListener('input', () => {
          if (onChange && editorRef.current) {
            onChange(editorRef.current.getContent());
          }
        });
      }
      
      // Listen for markdown textarea changes
      // Since the textarea is created dynamically, we listen on the container
      containerRef.current.addEventListener('input', (e) => {
         const target = e.target as HTMLElement;
         if (target.classList.contains('lemon-markdown-editor')) {
             if (onChange && editorRef.current) {
                onChange(editorRef.current.getContent());
             }
         }
      });
    }

    return () => {
      if (editorRef.current) {
        editorRef.current.destroy();
        editorRef.current = null;
      }
    };
  }, []); // Run once on mount

  // Handle external content updates
  useEffect(() => {
    if (editorRef.current && content !== editorRef.current.getContent()) {
       // Only update if content is significantly different to avoid cursor jumps
       // This is a naive implementation; for production, use a more robust comparison
       // or only update on specific conditions.
       // For now, we'll skip auto-update from props to avoid overwriting user input
       // unless it's the initial load or explicit reset.
    }
  }, [content]);

  return <div ref={containerRef} className={`lemon-editor-wrapper ${className}`} />;
};
