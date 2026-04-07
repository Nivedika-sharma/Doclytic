import React, { useState } from 'react';
import { askDocumentQuestion } from '../api/ragAPI';

interface DocumentChatProps {
    documentId: string;
}

const DocumentChat: React.FC<DocumentChatProps> = ({ documentId }) => {
    const [messages, setMessages] = useState<{ sender: 'user' | 'ai', text: string }[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSend = async () => {
        if (!inputValue.trim()) return;

        const userMessage = inputValue;

        setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
        setInputValue('');
        setIsLoading(true);

        try {
            const response = await askDocumentQuestion(documentId, userMessage);

            setMessages(prev => [...prev, { sender: 'ai', text: response.answer }]);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages(prev => [...prev, { sender: 'ai', text: "Sorry, I encountered an error connecting to the AI server." }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-800 w-full">
            <div className="p-4 border-b bg-slate-50 dark:bg-gray-900/60 font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                AI Document Assistant
            </div>
            
            {/* Chat History Area */}
            <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4 bg-white dark:bg-gray-800">
                {messages.length === 0 ? (
                    <div className="text-gray-400 text-sm text-center mt-10">
                        Ask me anything about this document!
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`p-3 rounded-2xl max-w-[85%] text-sm shadow-sm ${
                                msg.sender === 'user' 
                                ? 'bg-blue-600 dark:bg-blue-700/70 text-white rounded-br-none' 
                                : 'bg-slate-100 dark:bg-gray-700 text-slate-800 dark:text-gray-300 border border-slate-200 dark:border-gray-600 rounded-bl-none'
                            }`}>
                                {msg.text}
                            </div>
                        </div>
                    ))
                )}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-100 dark:bg-gray-700 text-slate-500 dark:text-gray-300 text-sm p-3 rounded-2xl rounded-bl-none animate-pulse border dark:border-gray-600 border-slate-200 shadow-sm">
                            Thinking...
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <div className="p-4 border-t bg-white dark:bg-gray-800 flex gap-2">
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Ask a question..."
                    className="flex-1 p-2 dark:bg-gray-700 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-700 text-sm"
                    disabled={isLoading}
                />
                <button
                    onClick={handleSend}
                    disabled={isLoading || !inputValue.trim()}
                    className="bg-blue-600 dark:bg-blue-500/80  text-white px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-500  disabled:opacity-50 transition-colors text-sm font-medium"
                >
                    Send
                </button>
            </div>
        </div>
    );
};

export default DocumentChat;