import React, { useEffect, useRef } from 'react';

interface PreviewProps {
  code: string;
}

export const Preview: React.FC<PreviewProps> = ({ code }) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (!iframeRef.current || !code) return;

    const html = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
          <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
          <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
          <script src="https://unpkg.com/lucide-react"></script>
          <script src="https://unpkg.com/motion@12.0.0/dist/motion.js"></script>
          <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
          <style>
            body { margin: 0; font-family: sans-serif; }
            #root { min-height: 100vh; }
          </style>
        </head>
        <body>
          <div id="root"></div>
          <script type="text/babel">
            const { useState, useEffect, useMemo, useCallback, useRef } = React;
            
            // Mocking motion/react for the browser preview
            const motion = window.motion || { div: (props) => <div {...props} /> };

            ${code.replace(/export default function/, 'function GeneratedComponent').replace(/import.*from.*/g, '')}

            const App = () => {
              try {
                return <GeneratedComponent />;
              } catch (err) {
                return (
                  <div className="p-4 text-red-500 bg-red-50 border border-red-200 rounded">
                    <h2 className="font-bold">Runtime Error</h2>
                    <pre className="text-xs mt-2 whitespace-pre-wrap">{err.message}</pre>
                  </div>
                );
              }
            };

            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<App />);
          </script>
        </body>
      </html>
    `;

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    iframeRef.current.src = url;

    return () => URL.revokeObjectURL(url);
  }, [code]);

  return (
    <div className="w-full h-full bg-white rounded-lg shadow-inner overflow-hidden border border-zinc-200">
      <iframe
        ref={iframeRef}
        className="w-full h-full border-none"
        title="Preview"
        sandbox="allow-scripts"
      />
    </div>
  );
};
