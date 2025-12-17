import React, { useState } from 'react';
import { generateDesignAdvice } from '../services/gemini';
import { ChatMessage } from '../types';

export const DesignAdvisor: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'model', text: 'Hello. I am your Luxury Merchandising Advisor. Ask me how to arrange this display or what jewelry pieces would best suit these velvet boxes.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: ChatMessage = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const prompt = `Context: A high-end jewelry store glass display case (wide) with 5 velvet boxes arranged in a row. 
    User Question: ${input}`;

    const responseText = await generateDesignAdvice(prompt);
    
    setMessages(prev => [...prev, { role: 'model', text: responseText }]);
    setLoading(false);
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 bg-gold-500 text-neutral-900 px-6 py-3 rounded-full shadow-lg font-serif font-bold hover:bg-gold-300 transition-all flex items-center gap-2"
      >
        <span className="text-xl">✨</span> Ask Design Advisor
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 h-[500px] bg-neutral-900/95 backdrop-blur-md border border-gold-700/30 rounded-lg shadow-2xl flex flex-col font-sans">
      {/* Header */}
      <div className="p-4 border-b border-gold-900 flex justify-between items-center bg-gold-900/20 rounded-t-lg">
        <h3 className="text-gold-300 font-serif font-bold text-lg">Luxe Advisor AI</h3>
        <button onClick={() => setIsOpen(false)} className="text-gold-500 hover:text-white transition-colors">
          ✕
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-gold-900">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-lg text-sm leading-relaxed ${
              msg.role === 'user' 
                ? 'bg-gold-700 text-white' 
                : 'bg-neutral-800 text-gold-100 border border-gold-900/50'
            }`}>
              {msg.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-neutral-800 p-3 rounded-lg border border-gold-900/50">
              <span className="animate-pulse text-gold-500 text-xs">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gold-900 bg-black/20">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="E.g., What stones match red velvet?"
            className="flex-1 bg-neutral-800 border border-gold-900 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:border-gold-500"
          />
          <button 
            onClick={handleSend}
            disabled={loading}
            className="bg-gold-600 hover:bg-gold-500 text-black px-4 py-2 rounded-md font-bold text-sm transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
