import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Sparkles, 
  Send, 
  Code, 
  Eye, 
  History, 
  Terminal, 
  Layers,
  ChevronRight,
  RotateCcw,
  Download,
  Copy,
  Check,
  Paperclip,
  X,
  FileText,
  Image as ImageIcon,
  Film,
  Music
} from 'lucide-react';
import { generateUI, type Attachment } from './lib/gemini';
import { Preview } from './components/Preview';
import ReactMarkdown from 'react-markdown';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  code?: string;
  explanation?: string;
}

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'code' | 'video'>('preview');
  const [mode, setMode] = useState<'ui' | 'video'>('ui');
  const [details, setDetails] = useState('');
  const [currentCode, setCurrentCode] = useState<string>('');
  const [videoUrl, setVideoUrl] = useState<string>('');
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const [copied, setCopied] = useState(false);

  const copyCode = () => {
    navigator.clipboard.writeText(currentCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newAttachments: Attachment[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const reader = new FileReader();
      
      const promise = new Promise<Attachment>((resolve) => {
        reader.onload = () => {
          const result = reader.result as string;
          if (file.type.startsWith('text/') || file.type === 'application/json' || file.name.endsWith('.html') || file.name.endsWith('.tsx') || file.name.endsWith('.ts')) {
            resolve({
              mimeType: file.type || 'text/plain',
              data: result,
              name: file.name
            });
          } else {
            const base64 = result.split(',')[1];
            resolve({
              mimeType: file.type,
              data: base64,
              name: file.name
            });
          }
        };
      });

      if (file.type.startsWith('text/') || file.type === 'application/json' || file.name.endsWith('.html') || file.name.endsWith('.tsx') || file.name.endsWith('.ts')) {
        reader.readAsText(file);
      } else {
        reader.readAsDataURL(file);
      }
      
      newAttachments.push(await promise);
    }

    setAttachments(prev => [...prev, ...newAttachments]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const generateVideo = async (videoPrompt: string) => {
    setIsLoading(true);
    setIsGeneratingVideo(true);
    setActiveTab('video');
    try {
      const { GoogleGenAI } = await import("@google/genai");
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });
      
      const firstImage = attachments.find(a => a.mimeType.startsWith('image/'));

      let operation = await ai.models.generateVideos({
        model: 'veo-3.1-fast-generate-preview',
        prompt: videoPrompt,
        image: firstImage ? {
          imageBytes: firstImage.data,
          mimeType: firstImage.mimeType
        } : undefined,
        config: {
          numberOfVideos: 1,
          resolution: '720p',
          aspectRatio: '16:9'
        }
      });

      while (!operation.done) {
        await new Promise(resolve => setTimeout(resolve, 5000));
        operation = await ai.operations.getVideosOperation({ operation: operation });
      }

      const downloadLink = operation.response?.generatedVideos?.[0]?.video?.uri;
      if (downloadLink) {
        const response = await fetch(downloadLink, {
          method: 'GET',
          headers: {
            'x-goog-api-key': process.env.GEMINI_API_KEY || '',
          },
        });
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setVideoUrl(url);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'Vídeo gerado com sucesso! Você pode visualizá-lo na aba de vídeo.' 
        }]);
      }
    } catch (error) {
      console.error('Error generating video:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Erro ao gerar vídeo. Certifique-se de que sua chave de API suporta o modelo Veo.' 
      }]);
    } finally {
      setIsLoading(false);
      setIsGeneratingVideo(false);
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!prompt.trim() || isLoading) return;

    const fullPrompt = details.trim() 
      ? `${prompt}\n\nDetalhes adicionais:\n${details}`
      : prompt;

    const currentAttachments = [...attachments];
    setPrompt('');
    setDetails('');
    setAttachments([]);
    setIsLoading(true);

    const newMessages: Message[] = [...messages, { role: 'user', content: fullPrompt }];
    setMessages(newMessages);

    if (mode === 'video') {
      await generateVideo(fullPrompt);
      return;
    }

    try {
      const history = messages.map(m => ({ 
        role: m.role === 'assistant' ? 'model' : 'user', 
        content: m.content 
      }));
      
      const result = await generateUI(fullPrompt, history, currentAttachments);
      
      if (result.code) {
        setCurrentCode(result.code);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: result.explanation || 'Aqui está o seu componente.',
          code: result.code,
          explanation: result.explanation
        }]);
        setActiveTab('preview');
      }
    } catch (error) {
      console.error('Error generating UI:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Desculpe, ocorreu um erro ao gerar a interface.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadCode = () => {
    const blob = new Blob([currentCode], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'GeneratedComponent.tsx';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#F8F9FA] text-zinc-900 font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Header */}
      <header className="h-16 border-b border-zinc-200 bg-white/80 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-200 rotate-3">
            <Sparkles className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">Banana Agent</h1>
            <p className="text-[10px] uppercase tracking-widest text-zinc-400 font-semibold">Frontend UI Generator</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex bg-zinc-100 p-1 rounded-xl border border-zinc-200">
            <button 
              onClick={() => setMode('ui')}
              className={cn(
                "px-3 py-1 rounded-lg text-[10px] font-bold transition-all",
                mode === 'ui' ? "bg-white text-emerald-600 shadow-sm" : "text-zinc-500"
              )}
            >UI</button>
            <button 
              onClick={() => setMode('video')}
              className={cn(
                "px-3 py-1 rounded-lg text-[10px] font-bold transition-all",
                mode === 'video' ? "bg-white text-emerald-600 shadow-sm" : "text-zinc-500"
              )}
            >VÍDEO</button>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="p-2 hover:bg-zinc-100 rounded-lg transition-colors text-zinc-500"
            title="Reset Session"
          >
            <RotateCcw size={18} />
          </button>
        </div>
      </header>

      <main className="flex flex-col lg:flex-row h-[calc(100vh-64px)] overflow-hidden">
        {/* Sidebar / Chat */}
        <div className="w-full lg:w-[400px] border-r border-zinc-200 bg-white flex flex-col shrink-0">
          <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-zinc-200">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center space-y-4 px-6">
                <div className="w-16 h-16 bg-zinc-50 rounded-2xl flex items-center justify-center border border-zinc-100 mb-2">
                  <Layers className="text-zinc-300 w-8 h-8" />
                </div>
                <h2 className="font-semibold text-zinc-800">Crie sua Interface ou Vídeo</h2>
                <p className="text-xs text-zinc-500 leading-relaxed">
                  Descreva o que você precisa. Use sugestões rápidas abaixo:
                </p>
                <div className="flex flex-wrap gap-2 justify-center w-full pt-2">
                  {['Login Form', 'Product Card', 'Hero Section', 'Video Banner'].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setPrompt(suggestion)}
                      className="px-3 py-1.5 text-[10px] font-bold bg-zinc-50 hover:bg-zinc-100 border border-zinc-200 rounded-full transition-all text-zinc-600 uppercase tracking-wider"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <AnimatePresence initial={false}>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "flex flex-col gap-2",
                    msg.role === 'user' ? "items-end" : "items-start"
                  )}
                >
                  <div className={cn(
                    "max-w-[90%] px-4 py-3 rounded-2xl text-sm shadow-sm",
                    msg.role === 'user' 
                      ? "bg-emerald-600 text-white rounded-tr-none" 
                      : "bg-zinc-100 text-zinc-800 rounded-tl-none border border-zinc-200"
                  )}>
                    {msg.role === 'assistant' ? (
                      <div className="prose prose-sm prose-zinc">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      msg.content
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {isLoading && (
              <div className="flex flex-col gap-2 items-start">
                <div className="bg-zinc-100 px-4 py-3 rounded-2xl rounded-tl-none border border-zinc-200 flex items-center gap-3">
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" />
                  </div>
                  <span className="text-xs text-zinc-500 font-medium">
                    {isGeneratingVideo ? 'Gerando Vídeo (pode levar 1-2 min)...' : 'Pensando...'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-zinc-200 bg-white space-y-3">
            {attachments.length > 0 && (
              <div className="flex flex-wrap gap-2 pb-2">
                {attachments.map((att, i) => (
                  <div key={i} className="flex items-center gap-2 px-2 py-1 bg-zinc-100 rounded-lg border border-zinc-200 group">
                    {att.mimeType.startsWith('image/') ? <ImageIcon size={12} className="text-emerald-600" /> :
                     att.mimeType.startsWith('video/') ? <Film size={12} className="text-emerald-600" /> :
                     att.mimeType.startsWith('audio/') ? <Music size={12} className="text-emerald-600" /> :
                     <FileText size={12} className="text-emerald-600" />}
                    <span className="text-[10px] font-medium text-zinc-600 max-w-[80px] truncate">{att.name}</span>
                    <button onClick={() => removeAttachment(i)} className="text-zinc-400 hover:text-red-500">
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="relative flex gap-2">
              <div className="relative flex-1">
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder={mode === 'ui' ? "O que vamos construir?" : "Descreva o vídeo..."}
                  className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all shadow-sm"
                />
              </div>
              <label className="flex items-center justify-center p-2.5 bg-zinc-100 text-zinc-600 rounded-xl hover:bg-zinc-200 cursor-pointer transition-all border border-zinc-200 shadow-sm">
                <Paperclip size={18} />
                <input
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
            </div>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="Detalhes adicionais (opcional)..."
              className="w-full bg-zinc-50 border border-zinc-200 rounded-xl px-4 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-none min-h-[60px]"
            />
            <button
              onClick={handleSubmit}
              disabled={!prompt.trim() || isLoading}
              className="w-full py-2.5 bg-emerald-600 text-white rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-lg shadow-emerald-200 flex items-center justify-center gap-2"
            >
              <Send size={14} />
              {mode === 'ui' ? 'GERAR INTERFACE' : 'GERAR VÍDEO'}
            </button>
            <p className="text-[9px] text-zinc-400 text-center font-medium uppercase tracking-tighter">
              Gemini 3 Flash • Veo Video Engine
            </p>
          </div>
        </div>

        {/* Workspace */}
        <div className="flex-1 bg-[#F1F3F5] p-4 lg:p-6 flex flex-col gap-4 overflow-hidden">
          {/* Tabs */}
          <div className="flex items-center justify-between">
            <div className="flex bg-white p-1 rounded-xl border border-zinc-200 shadow-sm">
              <button
                onClick={() => setActiveTab('preview')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all",
                  activeTab === 'preview' ? "bg-emerald-50 text-emerald-700 shadow-sm" : "text-zinc-500 hover:bg-zinc-50"
                )}
              >
                <Eye size={14} />
                PREVIEW
              </button>
              <button
                onClick={() => setActiveTab('code')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all",
                  activeTab === 'code' ? "bg-emerald-50 text-emerald-700 shadow-sm" : "text-zinc-500 hover:bg-zinc-50"
                )}
              >
                <Code size={14} />
                CÓDIGO
              </button>
              {videoUrl && (
                <button
                  onClick={() => setActiveTab('video')}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all",
                    activeTab === 'video' ? "bg-emerald-50 text-emerald-700 shadow-sm" : "text-zinc-500 hover:bg-zinc-50"
                  )}
                >
                  <Terminal size={14} />
                  VÍDEO
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              {currentCode && (
                <>
                  <button
                    onClick={copyCode}
                    className="flex items-center gap-2 px-4 py-2 bg-white border border-zinc-200 rounded-xl text-xs font-bold text-zinc-600 hover:bg-zinc-50 transition-all shadow-sm"
                  >
                    {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                    {copied ? 'COPIADO' : 'COPIAR'}
                  </button>
                  <button
                    onClick={downloadCode}
                    className="flex items-center gap-2 px-4 py-2 bg-zinc-900 text-white rounded-xl text-xs font-bold hover:bg-zinc-800 transition-all shadow-lg shadow-zinc-200"
                  >
                    <Download size={14} />
                    EXPORTAR
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 relative min-h-0">
            {activeTab === 'preview' && currentCode && <Preview code={currentCode} />}
            {activeTab === 'code' && currentCode && (
              <div className="h-full bg-[#1e1e1e] rounded-2xl overflow-hidden border border-zinc-800 shadow-2xl">
                <div className="flex items-center justify-between px-4 py-2 bg-zinc-800/50 border-b border-zinc-700">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/40" />
                    <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500/40" />
                    <div className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500/40" />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">App.tsx</span>
                </div>
                <pre className="p-6 text-sm font-mono text-zinc-300 overflow-auto h-[calc(100%-40px)] scrollbar-thin scrollbar-thumb-zinc-700">
                  <code>{currentCode}</code>
                </pre>
              </div>
            )}
            {activeTab === 'video' && videoUrl && (
              <div className="h-full bg-black rounded-2xl overflow-hidden shadow-2xl flex items-center justify-center">
                <video src={videoUrl} controls className="max-w-full max-h-full" />
              </div>
            )}
            {!currentCode && !videoUrl && (
              <div className="h-full flex flex-col items-center justify-center text-center p-12 bg-white/50 rounded-3xl border-2 border-dashed border-zinc-300">
                <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center shadow-xl mb-6">
                  <Sparkles className="text-zinc-300 w-10 h-10" />
                </div>
                <h3 className="text-xl font-bold text-zinc-800 mb-2">Pronto para criar</h3>
                <p className="text-zinc-500 max-w-sm">
                  Escolha entre gerar uma interface UI ou um vídeo curto usando os modelos de IA.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
