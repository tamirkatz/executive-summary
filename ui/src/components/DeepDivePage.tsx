import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { ResearchCardData } from "../types";
import ResearchCard from "./ResearchCard";
import { askQuestionAboutCard } from "../utils/chatApi";
import { Loader2 } from "lucide-react";

const DeepDivePage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const card = (location.state as { card?: ResearchCardData })?.card;

  const [deepDiveContent, setDeepDiveContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Automatically fetch deep-dive analysis when the page is opened
  useEffect(() => {
    const fetchDeepDive = async () => {
      if (!card) return;
      try {
        setIsLoading(true);
        const question = `Provide a detailed deep-dive analysis describing what \"${card.title}\" is, its broader impact, and its specific relation to the company.`;
        const answer = await askQuestionAboutCard(
          card.id,
          question,
          card.content
        );
        setDeepDiveContent(answer);
      } catch (error) {
        console.error("Deep dive fetch error:", error);
        setDeepDiveContent(
          "Failed to load deep dive analysis. Please try again later."
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchDeepDive();
  }, [card]);

  if (!card) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <h2 className="text-2xl font-semibold mb-4 text-gray-800">
          No section data provided
        </h2>
        <p className="mb-6 text-gray-600">
          Please return to the main report and select a section to deep dive.
        </p>
        <button
          onClick={() => navigate("/")}
          className="px-4 py-2 rounded-lg bg-[#468BFF] text-white hover:bg-[#8FBCFA] transition-colors"
        >
          Back to Report
        </button>
      </div>
    );
  }

  const handleAskQuestion = async (
    _cardId: string,
    question: string,
    cardContent: string
  ) => {
    return askQuestionAboutCard(card.id, question, cardContent);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white p-8">
      <button
        onClick={() => navigate(-1)}
        className="mb-6 inline-flex items-center px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
      >
        ← Back
      </button>

      <div className="max-w-4xl mx-auto space-y-6">
        {/* Deep Dive Analysis Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Deep Dive Analysis
          </h2>
          {isLoading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            </div>
          ) : (
            <p className="text-gray-800 whitespace-pre-wrap">
              {deepDiveContent || "No analysis available."}
            </p>
          )}
        </div>

        {/* Original Card Content & Chat */}
        <ResearchCard
          data={card}
          onAskQuestion={handleAskQuestion}
          className="w-full bg-white"
          initialWidth={700}
          initialHeight={600}
          minWidth={500}
          minHeight={500}
        />
      </div>
    </div>
  );
};

export default DeepDivePage;
