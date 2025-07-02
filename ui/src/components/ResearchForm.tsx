import React, { useState, useRef, useEffect } from "react";
import { Building2, Globe, Loader2, Search, UserCircle2 } from "lucide-react";
import LocationInput from "./LocationInput";
import ExamplePopup, { ExampleCompany } from "./ExamplePopup";

export interface FormData {
  companyName: string;
  companyUrl: string;
  userRole: string;
}

interface ResearchFormProps {
  onSubmit: (formData: FormData) => Promise<void>;
  isResearching: boolean;
  glassStyle: {
    card: string;
    input: string;
  };
  loaderColor: string;
}

const ResearchForm: React.FC<ResearchFormProps> = ({
  onSubmit,
  isResearching,
  glassStyle,
  loaderColor,
}) => {
  const [formData, setFormData] = useState<FormData>({
    companyName: "",
    companyUrl: "",
    userRole: "",
  });

  const [activeField, setActiveField] = useState<string | null>(null);
  const [wasResearching, setWasResearching] = useState(false);
  const formRef = useRef<HTMLDivElement>(null);

  // Track research state changes
  useEffect(() => {
    if (wasResearching && !isResearching) {
      setTimeout(() => {
        setFormData({
          companyName: "",
          companyUrl: "",
          userRole: "",
        });
      }, 1000);
    }
    setWasResearching(isResearching);
  }, [isResearching, wasResearching]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSubmit(formData);
  };

  const renderInputField = (
    id: string,
    label: string,
    icon: JSX.Element,
    placeholder: string,
    required: boolean = false
  ) => (
    <div
      className={`relative transition-all duration-300 ${
        activeField === id ? "scale-[1.02]" : ""
      }`}
    >
      <div className="relative">
        <div
          className={`
          absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 
          transition-colors duration-300
          ${activeField === id ? "text-blue-600" : "text-gray-400"}
        `}
        >
          {icon}
        </div>
        <input
          required={required}
          id={id}
          type="text"
          value={formData[id as keyof FormData]}
          onChange={(e) =>
            setFormData((prev) => ({
              ...prev,
              [id]: e.target.value,
            }))
          }
          onFocus={() => setActiveField(id)}
          onBlur={() => setActiveField(null)}
          className={`
            ${glassStyle.input}
            w-full py-3 pl-12 pr-4
            text-gray-900 placeholder-gray-400
            transition-all duration-300
            ${
              activeField === id
                ? "ring-2 ring-blue-400/30 border-blue-400/50"
                : ""
            }
          `}
          placeholder={placeholder}
        />
        <label
          htmlFor={id}
          className={`
            absolute -top-6 left-0
            text-sm font-medium
            transition-colors duration-300
            ${activeField === id ? "text-blue-600" : "text-gray-600"}
          `}
        >
          {label} {required && <span className="text-blue-600">*</span>}
        </label>
      </div>
    </div>
  );

  return (
    <div className="relative" ref={formRef}>
      <div className={`${glassStyle.card} overflow-hidden`}>
        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="space-y-6">
            {renderInputField(
              "companyName",
              "Company Name",
              <Building2 strokeWidth={1.5} />,
              "Enter company name",
              true
            )}
            {renderInputField(
              "companyUrl",
              "Company Website",
              <Globe strokeWidth={1.5} />,
              "example.com"
            )}
            {renderInputField(
              "userRole",
              "Your Role",
              <UserCircle2 strokeWidth={1.5} />,
              "e.g. CEO, Product Manager, etc."
            )}
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={isResearching || !formData.companyName}
              className={`
                w-full py-4 px-6 rounded-xl
                font-medium text-white
                transition-all duration-300
                flex items-center justify-center space-x-3
                ${
                  isResearching
                    ? "bg-blue-400 cursor-not-allowed"
                    : formData.companyName
                    ? "bg-blue-600 hover:bg-blue-700 active:bg-blue-800"
                    : "bg-gray-300 cursor-not-allowed"
                }
              `}
            >
              {isResearching ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span>Analyzing...</span>
                </>
              ) : (
                <>
                  <Search size={20} />
                  <span>Start Analysis</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResearchForm;
