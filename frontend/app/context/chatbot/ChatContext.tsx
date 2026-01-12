import React, { createContext, Dispatch, SetStateAction } from "react";

export interface ChatRecord {
  session_id: string | null;
  title: string | null;
  description: string | null;
  created_at: string | null;
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
  sessionID: string | null;
  messages: any;
  setMessages: Dispatch<SetStateAction<any>>;
  attachedFile: File | null;
  setAttachedFile: Dispatch<SetStateAction<File | null>>;
}
const ChatContext = createContext<ChatContextType | any>(null);

export { ChatContext };
