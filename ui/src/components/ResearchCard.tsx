import { useState } from "react";
import { Resizable } from "re-resizable";
import { ResearchCardProps } from "../types";
import ChatHistory from "./ChatHistory";
import ChatInput from "./ChatInput";

const ResearchCard: React.FC<ResearchCardProps> = ({
  data,
  onAskQuestion,
  onRemove,
  className = "",
  initialWidth = 400,
  initialHeight = 500,
  minWidth = 300,
  minHeight = 400,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [dimensions, setDimensions] = useState({
    width: initialWidth,
    height: initialHeight,
  });

  const handleResize = (e: any, direction: any, ref: any, d: any) => {
    setDimensions({
      width: dimensions.width + d.width,
      height: dimensions.height + d.height,
    });
  };

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const handleQuestionSubmit = async (question: string) => {
    if (onAskQuestion) {
      await onAskQuestion(data.id, question, data.content);
    }
  };

  const handleRemove = () => {
    if (onRemove) {
      onRemove(data.id);
    }
  };

  return (
    <Resizable
      size={{ width: dimensions.width, height: dimensions.height }}
      minWidth={minWidth}
      minHeight={minHeight}
      onResizeStop={handleResize}
      className={`relative rounded-xl shadow-lg overflow-hidden ${className}`}
      enable={{
        top: false,
        right: true,
        bottom: true,
        left: false,
        topRight: false,
        bottomRight: true,
        bottomLeft: false,
        topLeft: false,
      }}
      handleStyles={{
        bottomRight: {
          right: "4px",
          bottom: "4px",
          cursor: "se-resize",
        },
      }}
      handleClasses={{
        bottomRight:
          "w-4 h-4 bg-gray-200 rounded-sm hover:bg-gray-300 transition-colors",
      }}
    >
      <div className="flex flex-col h-full">
        {/* Card Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex-1 pr-4">
            {data.title}
          </h3>
          <div className="flex items-center space-x-2">
            {/* Remove button */}
            {onRemove && (
              <button
                onClick={handleRemove}
                className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded-full hover:bg-red-50"
                title="Remove this card"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
            {/* Expand/collapse button */}
            <button
              onClick={toggleExpand}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg
                className={`w-6 h-6 transform transition-transform ${
                  isExpanded ? "rotate-180" : ""
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Card Content */}
        <div
          className={`flex-1 overflow-hidden ${isExpanded ? "" : "max-h-32"}`}
        >
          <div className="p-6">
            <p className="text-sm text-gray-600 font-medium mb-2">Summary:</p>
            <p className="text-gray-800 mb-4">{data.summary}</p>

            <div className="border-t border-gray-200 pt-4">
              <p className="text-sm text-gray-600 font-medium mb-2">Details:</p>
              <p className="text-gray-800">{data.content}</p>
            </div>
          </div>
        </div>

        {/* Chat Section */}
        <div className="border-t border-gray-200">
          <div className="h-64 flex flex-col">
            <ChatHistory messages={data.chatHistory} className="flex-1" />
            <ChatInput onSubmit={handleQuestionSubmit} />
          </div>
        </div>
      </div>
    </Resizable>
  );
};

export default ResearchCard;
