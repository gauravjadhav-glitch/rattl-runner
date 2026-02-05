# AI-Driven Test Generation Architecture

## Overview
This document outlines the architecture for the "AI Auto-Generation" feature in Ratl Studio. The goal is to allow users to automatically generate Maestro YAML test steps by interacting with the device screen or providing high-level instructions.

## 1. System Components

### Frontend (Ratl Studio)
- **Capture Module**: Captures current device state (Screenshot + View Hierarchy) upon user interaction.
- **Interact Mode**: A toggleable mode (already partially implemented) where interactions trigger AI analysis.
- **Review UI**: A staging area or inline suggestion tooltip to review AI-generated code before inserting it into the editor.

### Backend (Ratl Server)
- **AI Gateway**: A new endpoint `/api/ai/generate` that proxies requests to the LLM provider.
- **Context Builder**: Formats the hierarchy and screenshot into a prompt payload.

### External LLM Service
- **Provider**: Models with Vision capabilities (e.g., GPT-4o, Gemini 1.5 Pro, Claude 3.5 Sonnet).
- **Role**: Visual analysis of UI elements and logical mapping to Maestro commands.

## 2. Data Flow

1. **User Action**: User clicks an element or region in "AI Mode".
2. **Data Collection**: Frontend gathers:
   - `screenshot`: Base64 encoded image.
   - `hierarchy`: JSON/XML tree of UI elements (DOM for Web, UIAutomator for Mobile).
   - `coordinates`: (x, y) of the click.
   - `context`: Previous steps (optional) for flow continuity.
3. **Request**: POST to `/api/ai/generate`.
4. **Processing**: Backend constructs a prompt combining visual and structural data.
5. **Generation**: LLM returns a JSON object containing:
   - `yaml`: The suggested Maestro command.
   - `explanation`: Brief reasoning (e.g., "Selected text locator for stability").
6. **Response**: Backend sends data to Frontend.
7. **Insertion**: Frontend inserts the YAML into the editor and logs the explanation.

## 3. Web vs. Mobile Implementation

The AI engine works similarly for both platforms, but data sourcing differs:

- **Mobile (Android/iOS)**:
  - **Source**: ADB / IDB (via Maestro driver).
  - **Data**: UIAutomator XML dump + ADB Screenshot.
  - **Commands**: `tapOn`, `swipe`, `inputText`.

- **Web (React/HTML)**:
  - **Source**: Chrome DevTools Protocol (CDP) or Selenium/Puppeteer bridge.
  - **Data**: Flattened DOM Tree (HTML) + Browser Screenshot.
  - **Commands**: `tapOn` (Selector), `scroll`.

The AI Prompt will adapt based on the `platform` flag, favoring `id` and `text` for both, but handling platform-specific attributes (e.g., `resource-id` vs `data-testid`).

## 4. Key Features

- **Text Preference**: AI prioritizes `tapOn: "Text"` over coordinates for stability.
- **Semantic Understanding**: AI infers intent (e.g., "Submit" button implies form submission).
- **Self-Correction**: If a step fails, AI can analyze the new screenshot to suggest a fix.

## 5. Next Steps

1. **Backend Setup**: Create the `/api/ai` endpoint structure.
2. **Frontend UI**: Add the "Ask AI" toggle/button in the Inspector.
3. **Prompt Engineering**: Develop robust system prompts for Maestro syntax.
