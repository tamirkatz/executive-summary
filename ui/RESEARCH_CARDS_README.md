# Research Cards UI Components

This document explains the new research cards functionality that allows users to switch between a traditional report view and an interactive cards view with embedded chat capabilities.

## Overview

The research cards feature provides:

- **Toggle View**: Switch between full report and interactive cards
- **Resizable Cards**: Each card can be manually resized by dragging the bottom-right corner
- **Responsive Layout**: Cards automatically arrange in a grid based on screen size
- **Interactive Chat**: Each card has an embedded mini ChatGPT-style interface
- **Smart Parsing**: Automatically converts research reports into individual cards

## Components

### 1. EnhancedResearchReport

The main component that wraps the existing ResearchReport and adds the toggle functionality.

```tsx
import { EnhancedResearchReport } from "./components";

<EnhancedResearchReport
  output={researchOutput}
  isResetting={false}
  glassStyle="glass-card-modern"
  fadeInAnimation={fadeInAnimation}
  loaderColor="#6366f1"
  isGeneratingPdf={false}
  isCopied={false}
  onCopyToClipboard={handleCopyToClipboard}
  onGeneratePdf={handleGeneratePdf}
  onAskQuestion={handleCardQuestion} // Optional: for chat functionality
/>;
```

### 2. ResearchCard

Individual resizable card component with embedded chat.

```tsx
import { ResearchCard } from "./components";

<ResearchCard
  data={cardData}
  onAskQuestion={handleQuestion}
  initialWidth={400}
  initialHeight={500}
  minWidth={300}
  minHeight={400}
/>;
```

### 3. ResearchCardGrid

Grid container for organizing multiple cards.

```tsx
import { ResearchCardGrid } from "./components";

<ResearchCardGrid
  cards={cardsData}
  onAskQuestion={handleQuestion}
  className="mt-6"
/>;
```

### 4. ViewToggle

Toggle component for switching between views.

```tsx
import { ViewToggle } from "./components";

<ViewToggle
  currentView={currentView}
  onViewChange={setCurrentView}
  className="ml-4"
/>;
```

## Data Structure

### ResearchCardData

```tsx
interface ResearchCardData {
  id: string;
  title: string;
  summary: string; // Brief summary for card preview
  content: string; // Full content for detailed view
  chatHistory: ChatMessage[];
}
```

### ChatMessage

```tsx
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}
```

## Usage Examples

### Basic Implementation

```tsx
import React, { useState } from "react";
import { EnhancedResearchReport } from "./components";
import { askQuestionAboutCard } from "./utils/chatApi";

function App() {
  const [researchOutput, setResearchOutput] = useState(null);

  const handleCardQuestion = async (cardId: string, question: string) => {
    const response = await askQuestionAboutCard(cardId, question, cardContent);
    return response;
  };

  return (
    <EnhancedResearchReport
      output={researchOutput}
      onAskQuestion={handleCardQuestion}
      // ... other props
    />
  );
}
```

### Custom Card Implementation

```tsx
import { ResearchCardGrid } from "./components";
import { sampleResearchData } from "./utils/sampleData";

function CustomCardsView() {
  const handleQuestion = async (cardId: string, question: string) => {
    // Your custom question handling logic
    return "Custom response";
  };

  return (
    <ResearchCardGrid
      cards={sampleResearchData}
      onAskQuestion={handleQuestion}
    />
  );
}
```

## Report Parsing

The system automatically converts research reports into cards using the `parseReportToCards` utility:

### Parsing Logic

1. **Markdown Headers**: Splits by `#`, `##`, `###` headers
2. **Bullet Points**: Creates individual cards for each bullet point
3. **Paragraphs**: Falls back to paragraph-based splitting
4. **Title Extraction**: Extracts titles from headers or first sentences

### Example Report Structure

```markdown
# Company Analysis

## Recent Product Launches

- **AI Foundation Model**: On May 7, 2025, Stripe launched an AI foundation model...
- **Enhanced Security**: New security features implemented...

## Financial Performance

Strong revenue growth of 35% year-over-year...
```

This would create separate cards for:

- "AI Foundation Model"
- "Enhanced Security"
- "Financial Performance"

## Chat Functionality

### API Integration

The chat functionality can be integrated with your backend API:

```tsx
// utils/chatApi.ts
export const askQuestionAboutCard = async (
  cardId: string,
  question: string,
  cardContent: string
): Promise<string> => {
  const response = await fetch("/api/research/ask-question", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      card_id: cardId,
      question: question,
      context: cardContent,
    }),
  });

  const data = await response.json();
  return data.answer;
};
```

### Mock Responses

For development/demo purposes, the system includes intelligent mock responses based on question keywords:

- "when/date" → Timeline information
- "why/reason" → Strategic explanations
- "how/process" → Process descriptions
- "impact/effect" → Impact analysis
- "competitor/competition" → Competitive insights

## Styling

### Resizable Handles

Cards use the `re-resizable` library with custom styling:

- Bottom-right corner resize handle
- Hover effects for better UX
- Minimum size constraints

### Responsive Design

- **Mobile**: Single column layout
- **Tablet**: 2-column layout
- **Desktop**: 3-column layout
- **Large screens**: Maintains 3 columns with larger cards

### Glass Morphism Effects

Cards inherit the app's glass morphism styling:

- Semi-transparent backgrounds
- Subtle borders and shadows
- Smooth transitions and animations

## Dependencies

### Required Packages

```json
{
  "re-resizable": "^6.9.9",
  "react": "^18.2.0",
  "react-dom": "^18.2.0"
}
```

### Installation

```bash
npm install re-resizable
```

## Best Practices

### Performance

- Use `React.memo` for card components when dealing with large datasets
- Implement virtual scrolling for 100+ cards
- Debounce resize operations

### Accessibility

- Ensure keyboard navigation works for all interactive elements
- Add ARIA labels for screen readers
- Maintain proper color contrast ratios

### UX Guidelines

- Keep card titles concise (< 50 characters)
- Limit summary text to 2-3 lines
- Provide clear visual feedback for resizing operations
- Use loading states for chat responses

## Troubleshooting

### Common Issues

1. **Cards not resizing**: Ensure `re-resizable` is properly installed
2. **Chat not working**: Check that `onAskQuestion` prop is provided
3. **Parsing issues**: Verify report content has proper markdown structure
4. **Layout problems**: Check CSS grid and responsive breakpoints

### Debug Mode

Enable debug logging by setting:

```tsx
const DEBUG_CARDS = process.env.NODE_ENV === "development";
```

This will log parsing results and card interactions to the console.
