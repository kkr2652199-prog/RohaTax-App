import { GoogleGenAI, GenerateContentResponse } from "@google/genai";

// Initialize the client assuming the API key is pre-configured and valid
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const generateDesignAdvice = async (prompt: string): Promise<string> => {
  try {
    const response: GenerateContentResponse = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
      config: {
        systemInstruction: "You are an expert luxury jewelry display designer and visual merchandiser. You provide sophisticated, aesthetic advice on how to arrange jewelry in a glass case. Keep answers concise, elegant, and professional.",
      }
    });
    
    return response.text || "I could not generate advice at this moment.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Sorry, I encountered an error while consulting the design models.";
  }
};