import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "" });

export interface Attachment {
  mimeType: string;
  data: string; // base64 for binary, text for text files
  name: string;
}

export const generateUI = async (
  prompt: string, 
  history: { role: string; content: string }[] = [],
  attachments: Attachment[] = []
) => {
  const model = "gemini-3-flash-preview";
  
  const systemInstruction = `You are an expert React and Tailwind CSS developer. 
Your task is to generate a single-file React component based on the user's request.
Rules:
1. Use ONLY Tailwind CSS for styling.
2. Use Lucide React for icons (assume 'lucide-react' is available).
3. The response must be a valid React component that can be rendered.
4. Return the code in a JSON object with 'code' and 'explanation' fields.
5. Do not use external libraries other than 'lucide-react', 'motion/react', and standard React hooks.
6. Ensure the component is self-contained and exported as default.
7. Use 'motion/react' for animations.
8. The code should be clean, responsive, and modern.
9. If the user provides attachments (images, code, etc.), use them as reference for the design or logic.`;

  const parts: any[] = [{ text: prompt }];
  
  attachments.forEach(att => {
    if (att.mimeType.startsWith('text/') || att.mimeType === 'application/json' || att.name.endsWith('.html') || att.name.endsWith('.tsx') || att.name.endsWith('.ts')) {
      parts.push({ text: `\n\nFile Content (${att.name}):\n${att.data}` });
    } else {
      parts.push({
        inlineData: {
          mimeType: att.mimeType,
          data: att.data
        }
      });
    }
  });

  const contents = [
    ...history.map(h => ({
      role: h.role === "user" ? "user" : "model",
      parts: [{ text: h.content }]
    })),
    {
      role: "user",
      parts: parts
    }
  ];

  const response = await ai.models.generateContent({
    model,
    contents,
    config: {
      systemInstruction,
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          code: {
            type: Type.STRING,
            description: "The complete React component code.",
          },
          explanation: {
            type: Type.STRING,
            description: "A brief explanation of what was built.",
          },
        },
        required: ["code", "explanation"],
      },
    },
  });

  return JSON.parse(response.text || "{}");
};
