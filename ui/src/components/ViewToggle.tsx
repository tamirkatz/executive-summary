import { ViewToggleProps } from "../types";

const ViewToggle: React.FC<ViewToggleProps> = ({
  currentView,
  onViewChange,
  className = "",
}) => {
  return (
    <div
      className={`flex items-center space-x-1 bg-gray-100 rounded-lg p-1 ${className}`}
    >
      <button
        onClick={() => onViewChange("report")}
        className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
          currentView === "report"
            ? "bg-white text-blue-600 shadow-sm"
            : "text-gray-600 hover:text-gray-900"
        }`}
      >
        <svg
          className="w-4 h-4 mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        Report View
      </button>
      <button
        onClick={() => onViewChange("cards")}
        className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
          currentView === "cards"
            ? "bg-white text-blue-600 shadow-sm"
            : "text-gray-600 hover:text-gray-900"
        }`}
      >
        <svg
          className="w-4 h-4 mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
        Cards View
      </button>
    </div>
  );
};

export default ViewToggle;
