import { useEffect, useRef } from "react";
import { ChatHistoryProps, ChatMessage } from "../types";

const ChatHistory: React.FC<ChatHistoryProps> = ({
  messages,
  className = "",
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.role === "user";
    return (
      <div
        key={`${message.timestamp}-${message.content}`}
        className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
      >
        <div
          className={`max-w-[80%] rounded-lg px-4 py-2 ${
            isUser
              ? "bg-blue-600 text-white rounded-br-none"
              : "bg-gray-100 text-gray-900 rounded-bl-none"
          }`}
        >
          <div className="text-sm">{message.content}</div>
          <div
            className={`text-xs mt-1 ${
              isUser ? "text-blue-100" : "text-gray-500"
            }`}
          >
            {formatTimestamp(message.timestamp)}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`flex-1 overflow-y-auto p-4 ${className}`}>
      {messages.map(renderMessage)}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default ChatHistory;
