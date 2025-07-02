import { ResearchCardData } from "../types";
import ResearchCard from "./ResearchCard";

interface ResearchCardGridProps {
  cards: ResearchCardData[];
  onAskQuestion?: (
    cardId: string,
    question: string,
    cardContent: string
  ) => Promise<string>;
  onRemoveCard: (cardId: string) => void;
  className?: string;
}

const ResearchCardGrid: React.FC<ResearchCardGridProps> = ({
  cards,
  onAskQuestion,
  onRemoveCard,
  className = "",
}) => {
  // Tailwind background color palette for cards (pastel shades)
  const colorClasses = [
    "bg-rose-50",
    "bg-sky-50",
    "bg-emerald-50",
    "bg-indigo-50",
    "bg-yellow-50",
    "bg-purple-50",
  ];

  return (
    <div className={`w-full overflow-y-auto ${className}`}>
      {/* Cards container with improved spacing */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-8 p-8">
        {cards.map((card, index) => (
          <div key={card.id} className="flex justify-center">
            <ResearchCard
              data={card}
              onAskQuestion={onAskQuestion}
              onRemove={onRemoveCard}
              className={`w-full max-w-md ${
                colorClasses[index % colorClasses.length]
              }`}
              initialWidth={380}
              initialHeight={480}
              minWidth={300}
              minHeight={400}
            />
          </div>
        ))}
      </div>

      {/* Show message when no cards */}
      {cards.length === 0 && (
        <div className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg
              className="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </div>
          <p className="text-gray-500 text-lg">All cards have been removed</p>
          <p className="text-sm text-gray-400 mt-2">
            Switch to Report View to see the full content, or refresh to restore
            all cards.
          </p>
        </div>
      )}
    </div>
  );
};

export default ResearchCardGrid;
