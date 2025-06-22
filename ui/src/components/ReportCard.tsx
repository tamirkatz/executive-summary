import React, { useState } from "react";
import { ChevronDown, ChevronUp, Search, ExternalLink } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ReportCardProps {
  title: string;
  content: string;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
  showDeepDive?: boolean;
  onDeepDive?: () => void;
  priority?: "high" | "medium" | "low";
  cardType?: "summary" | "analysis" | "recommendations" | "data";
}

const ReportCard: React.FC<ReportCardProps> = ({
  title,
  content,
  isExpanded = true,
  onToggleExpand,
  showDeepDive = true,
  onDeepDive,
  priority = "medium",
  cardType = "analysis",
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const getPriorityColor = () => {
    switch (priority) {
      case "high":
        return "border-red-200 bg-red-50/50";
      case "medium":
        return "border-yellow-200 bg-yellow-50/50";
      case "low":
        return "border-green-200 bg-green-50/50";
      default:
        return "border-gray-200 bg-white/50";
    }
  };

  const getCardIcon = () => {
    switch (cardType) {
      case "summary":
        return "📋";
      case "analysis":
        return "📊";
      case "recommendations":
        return "💡";
      case "data":
        return "📈";
      default:
        return "📄";
    }
  };

  return (
    <div
      className={`
        relative rounded-xl border-2 transition-all duration-300 ease-in-out
        ${getPriorityColor()}
        ${isHovered ? "shadow-lg transform scale-[1.02]" : "shadow-md"}
        backdrop-blur-sm
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{getCardIcon()}</span>
          <h3 className="text-xl font-bold text-gray-900">{title}</h3>
          {priority === "high" && (
            <span className="px-2 py-1 text-xs font-semibold text-red-600 bg-red-100 rounded-full">
              HIGH PRIORITY
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {showDeepDive && (
            <button
              onClick={onDeepDive}
              className="flex items-center space-x-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors duration-200"
            >
              <Search className="h-4 w-4" />
              <span>Deep Dive</span>
              <ExternalLink className="h-3 w-3" />
            </button>
          )}

          {onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md transition-colors duration-200"
            >
              {isExpanded ? (
                <ChevronUp className="h-5 w-5" />
              ) : (
                <ChevronDown className="h-5 w-5" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div
        className={`
          transition-all duration-300 ease-in-out overflow-hidden
          ${isExpanded ? "max-h-none opacity-100" : "max-h-0 opacity-0"}
        `}
      >
        <div className="p-6">
          <div className="prose prose-gray max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children, ...props }) => (
                  <h1
                    className="text-2xl font-bold text-gray-900 mb-4"
                    {...props}
                  >
                    {children}
                  </h1>
                ),
                h2: ({ children, ...props }) => (
                  <h2
                    className="text-xl font-semibold text-gray-800 mb-3"
                    {...props}
                  >
                    {children}
                  </h2>
                ),
                h3: ({ children, ...props }) => (
                  <h3
                    className="text-lg font-medium text-gray-800 mb-2"
                    {...props}
                  >
                    {children}
                  </h3>
                ),
                p: ({ children, ...props }) => (
                  <p className="text-gray-700 mb-3 leading-relaxed" {...props}>
                    {children}
                  </p>
                ),
                ul: ({ children, ...props }) => (
                  <ul
                    className="list-disc list-inside text-gray-700 space-y-1 mb-3"
                    {...props}
                  >
                    {children}
                  </ul>
                ),
                li: ({ children, ...props }) => (
                  <li className="text-gray-700" {...props}>
                    {children}
                  </li>
                ),
                strong: ({ children, ...props }) => (
                  <strong className="font-semibold text-gray-900" {...props}>
                    {children}
                  </strong>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>
      </div>

      {/* Resize handle (visual indicator) */}
      <div className="absolute bottom-2 right-2 w-4 h-4 opacity-20 hover:opacity-40 transition-opacity">
        <div
          className="w-full h-full bg-gray-400 rounded-br-xl"
          style={{
            clipPath: "polygon(100% 0%, 0% 100%, 100% 100%)",
          }}
        />
      </div>
    </div>
  );
};

export default ReportCard;
