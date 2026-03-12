import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Bot, User } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  expert?: string;
  confidence?: number;
}

interface ChatProps {
  messages: Message[];
  inputMessage: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  isLoading: boolean;
  isDarkMode: boolean;
}

const Chat: React.FC<ChatProps> = ({
  messages,
  inputMessage,
  onInputChange,
  onSendMessage,
  isLoading,
  isDarkMode
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when component mounts
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
    <div className={`flex flex-col h-full ${isDarkMode ? 'bg-gray-900' : 'bg-white'}`}>
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Bot className={`w-16 h-16 mb-4 ${isDarkMode ? 'text-blue-400' : 'text-blue-500'}`} />
            <h3 className={`text-xl font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              Bem-vindo ao Agentic System
            </h3>
            <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
              Envie uma mensagem para começar a interagir com nossos especialistas.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} fade-in`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl ${
                  message.type === 'user'
                    ? isDarkMode ? 'bg-blue-600 text-white' : 'bg-blue-500 text-white'
                    : isDarkMode ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-900'
                }`}
              >
                {/* Message Header */}
                {message.type === 'assistant' && message.expert && (
                  <div className={`text-xs font-medium mb-1 ${isDarkMode ? 'text-blue-400' : 'text-blue-600'}`}>
                    {message.expert}
                    {message.confidence && (
                      <span className={`ml-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                        ({Math.round(message.confidence * 100)}% confiança)
                      </span>
                    )}
                  </div>
                )}

                {/* Message Content */}
                <div className={`text-sm whitespace-pre-wrap break-words ${
                  message.type === 'system' ? 'italic' : ''
                }`}>
                  {message.content}
                </div>

                {/* Message Timestamp */}
                <div className={`text-xs mt-1 ${isDarkMode ? 'text-gray-500' : 'text-gray-400'}`}>
                  {formatTime(message.timestamp)}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className={`border-t ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'} p-4`}>
        <div className="flex items-end space-x-2">
          {/* Input Field */}
          <div className="flex-1 relative">
            <input
              id="chat-input"
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Digite sua mensagem..."
              disabled={isLoading}
              className={`w-full px-4 py-3 rounded-lg border resize-none focus:outline-none focus:ring-2 ${
                isDarkMode
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:ring-blue-500'
                  : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500 focus:ring-blue-500'
              }`}
              style={{
                minHeight: '48px',
                maxHeight: '120px',
              }}
            />
          </div>

          {/* Send Button */}
          <button
            onClick={onSendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className={`px-4 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2 ${
              isLoading || !inputMessage.trim()
                ? isDarkMode
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : isDarkMode
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Status Indicator */}
        {isLoading && (
          <div className={`mt-2 text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Processando mensagem...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;
