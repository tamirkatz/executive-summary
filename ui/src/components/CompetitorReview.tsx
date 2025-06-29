import React, { useState } from "react";
import {
  Trash2,
  Plus,
  Check,
  X,
  Building2,
  Globe,
  AlertCircle,
} from "lucide-react";

export interface Competitor {
  name: string;
  description?: string;
  category?: string;
  confidence?: number;
  evidence?: string;
  website?: string;
}

interface CompetitorReviewProps {
  competitors: Competitor[];
  onConfirm: (modifiedCompetitors: Competitor[]) => void;
  onCancel: () => void;
  isVisible: boolean;
  glassStyle: {
    card: string;
    input: string;
  };
}

const CompetitorReview: React.FC<CompetitorReviewProps> = ({
  competitors = [],
  onConfirm,
  onCancel,
  isVisible,
  glassStyle,
}) => {
  const [modifiedCompetitors, setModifiedCompetitors] =
    useState<Competitor[]>(competitors);
  const [newCompetitorName, setNewCompetitorName] = useState("");
  const [newCompetitorWebsite, setNewCompetitorWebsite] = useState("");
  const [isAddingNew, setIsAddingNew] = useState(false);

  // Update when competitors prop changes
  React.useEffect(() => {
    setModifiedCompetitors(competitors);
  }, [competitors]);

  const removeCompetitor = (index: number) => {
    setModifiedCompetitors((prev) => prev.filter((_, i) => i !== index));
  };

  const addNewCompetitor = () => {
    if (newCompetitorName.trim()) {
      const newCompetitor: Competitor = {
        name: newCompetitorName.trim(),
        website: newCompetitorWebsite.trim() || undefined,
        category: "manual",
        confidence: 1.0,
        description: "Manually added by user",
        evidence: "User input",
      };

      setModifiedCompetitors((prev) => [...prev, newCompetitor]);
      setNewCompetitorName("");
      setNewCompetitorWebsite("");
      setIsAddingNew(false);
    }
  };

  const handleConfirm = () => {
    onConfirm(modifiedCompetitors);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div
        className={`${glassStyle.card} backdrop-blur-2xl bg-white/95 border-gray-200/50 shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden`}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 font-['DM_Sans']">
                Review Competitors
              </h2>
              <p className="text-gray-600 mt-1 font-['DM_Sans']">
                Review the discovered competitors and add or remove as needed
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1 text-sm text-gray-500">
                <AlertCircle className="h-4 w-4" />
                <span>{modifiedCompetitors.length} competitors</span>
              </div>
            </div>
          </div>

          {/* Competitors List */}
          <div className="space-y-3 max-h-96 overflow-y-auto mb-6">
            {modifiedCompetitors.map((competitor, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-4 bg-white/60 rounded-lg border border-gray-200/50 hover:bg-white/80 transition-all duration-200"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <Building2 className="h-5 w-5 text-blue-500" />
                    <div>
                      <h3 className="font-semibold text-gray-900 font-['DM_Sans']">
                        {competitor.name}
                      </h3>
                      {competitor.website && (
                        <div className="flex items-center space-x-1 text-sm text-gray-500 mt-1">
                          <Globe className="h-3 w-3" />
                          <span>{competitor.website}</span>
                        </div>
                      )}
                      {competitor.description && (
                        <p className="text-sm text-gray-600 mt-1">
                          {competitor.description}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {competitor.category && (
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        competitor.category === "direct"
                          ? "bg-red-100 text-red-700"
                          : competitor.category === "indirect"
                          ? "bg-yellow-100 text-yellow-700"
                          : competitor.category === "emerging"
                          ? "bg-green-100 text-green-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {competitor.category}
                    </span>
                  )}
                  {competitor.confidence && (
                    <span className="text-xs text-gray-500">
                      {Math.round(competitor.confidence * 100)}%
                    </span>
                  )}
                  <button
                    onClick={() => removeCompetitor(index)}
                    className="p-2 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-all duration-200"
                    title="Remove competitor"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Add New Competitor */}
          <div className="border-t border-gray-200/50 pt-4 mb-6">
            {!isAddingNew ? (
              <button
                onClick={() => setIsAddingNew(true)}
                className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 transition-colors duration-200"
              >
                <Plus className="h-4 w-4" />
                <span className="font-['DM_Sans']">Add Competitor</span>
              </button>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      value={newCompetitorName}
                      onChange={(e) => setNewCompetitorName(e.target.value)}
                      placeholder="Competitor name *"
                      className={`${glassStyle.input} pl-10 font-['DM_Sans']`}
                      onKeyPress={(e) =>
                        e.key === "Enter" && addNewCompetitor()
                      }
                    />
                  </div>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <input
                      type="text"
                      value={newCompetitorWebsite}
                      onChange={(e) => setNewCompetitorWebsite(e.target.value)}
                      placeholder="Website URL (optional)"
                      className={`${glassStyle.input} pl-10 font-['DM_Sans']`}
                      onKeyPress={(e) =>
                        e.key === "Enter" && addNewCompetitor()
                      }
                    />
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={addNewCompetitor}
                    disabled={!newCompetitorName.trim()}
                    className="flex items-center space-x-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    <Check className="h-4 w-4" />
                    <span className="font-['DM_Sans']">Add</span>
                  </button>
                  <button
                    onClick={() => {
                      setIsAddingNew(false);
                      setNewCompetitorName("");
                      setNewCompetitorWebsite("");
                    }}
                    className="flex items-center space-x-1 px-3 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-all duration-200"
                  >
                    <X className="h-4 w-4" />
                    <span className="font-['DM_Sans']">Cancel</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3">
            <button
              onClick={onCancel}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-all duration-200 font-['DM_Sans'] font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 font-['DM_Sans'] font-medium flex items-center space-x-2"
            >
              <Check className="h-4 w-4" />
              <span>Continue Research</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompetitorReview;
