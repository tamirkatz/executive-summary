# Debugging Guide for Research UI Issues

## Console Logging Added

I've added comprehensive console logging to help debug the issue. The logs use emojis for easy identification:

### 🔍 WebSocket Messages

- `🔍 WebSocket message received:` - Raw message received
- `📊 Status update received:` - Parsed status update details
- `🔄 Phase transition:` - When research phases change
- `✅ Research completed successfully` - When research finishes

### 🔗 Connection Events

- `🔗 WebSocket connection established` - Connection opened
- `🔌 WebSocket disconnected` - Connection closed with details
- `❌ WebSocket error:` - Connection errors

### 🚀 Research Flow

- `🚀 Starting research for:` - Research initiation
- `📤 Sending research request:` - Request details
- `📥 Response received:` - Server response
- `✅ Response data:` - Job ID and other data

### 📊 State Updates

- `🔄 Research state updated:` - State changes
- `📄 Output updated:` - Report content updates
- `📊 Status updated:` - Status message changes

### 🎨 Component Rendering

- `🎨 Rendering progress components:` - Component rendering decisions
- `📄 Rendering ResearchReport component` - Report component
- `📝 Rendering ResearchBriefings component` - Briefing component
- `📚 Rendering CurationExtraction component` - Enrichment component
- `🔍 Rendering ResearchQueries component` - Queries component

### 📚 Specific Phase Logs

- `📚 Enrichment update:` - Enrichment progress
- `📋 Curation update:` - Curation progress
- `🔍 Query generating:` - Query generation
- `✅ Query generated:` - Query completion
- `📝 Briefing started:` - Briefing initiation
- `✅ Briefing completed:` - Briefing completion

## How to Debug

1. **Open Browser Console** (F12 → Console tab)
2. **Start a Research Job** with a company name
3. **Watch the Console Logs** as the research progresses
4. **Look for Patterns** when the issue occurs:
   - Does the WebSocket disconnect?
   - Are there any error messages?
   - Does the state stop updating?
   - Are components not rendering?

## Key Areas to Monitor

### After Initial Query Generation

Look for these logs after "successfully extracted content":

- `📚 Enrichment update:` - Should show enrichment starting
- `📋 Curation update:` - Should show curation progress
- `📝 Briefing started:` - Should show briefing initiation

### Potential Issue Points

1. **WebSocket Disconnection**: Look for `🔌 WebSocket disconnected`
2. **State Update Failures**: Look for missing `🔄 Research state updated` logs
3. **Component Rendering Issues**: Look for missing component rendering logs
4. **Error Messages**: Look for any `❌` prefixed logs

## What to Report

When the issue occurs, please provide:

1. **Console Logs**: Copy all console output from the research start to the issue
2. **Last Successful Log**: What was the last successful operation?
3. **Error Messages**: Any error messages or warnings
4. **Timing**: How long after starting did the issue occur?
5. **Company Name**: What company were you researching?

## Expected Flow

1. `🚀 Starting research for: [Company]`
2. `📤 Sending research request:`
3. `📥 Response received:`
4. `✅ Response data:`
5. `🔗 WebSocket connection established`
6. `🔍 WebSocket message received:` (multiple times)
7. `🔍 Query generating:` (multiple times)
8. `✅ Query generated:` (multiple times)
9. `📚 Enrichment update:` (multiple times)
10. `📋 Curation update:` (multiple times)
11. `📝 Briefing started:`
12. `✅ Briefing completed:` (multiple times)
13. `✅ Research completed successfully`

If the flow stops or breaks at any point, that's where the issue is occurring.
