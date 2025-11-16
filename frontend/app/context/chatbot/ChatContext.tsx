import React, { createContext } from "react";

export interface ChatRecord {
  session_id: string | null;
  title: string | null;
  description: string | null;
  date: string | null;
}
export interface ChatContextType {
  hideExtraOptions: boolean;
  setHideExtraOptions: React.Dispatch<React.SetStateAction<boolean>>;
  selectedModel: string;
  setSelectedModel: React.Dispatch<React.SetStateAction<string>>;
  hideModelBox: boolean;
  setHideModelBox: React.Dispatch<React.SetStateAction<boolean>>;
  chatHistory: ChatRecord[];
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecord[]>>;
  selectedSessionID: string;
  setSelectedSessionID: React.Dispatch<React.SetStateAction<string>>;
  openChatHistoryDialogueBox: boolean;
  setOpenChatHistoryDialogueBox: React.Dispatch<React.SetStateAction<boolean>>;
}
const ChatContext = createContext<ChatContextType | any>(null);

export { ChatContext };
