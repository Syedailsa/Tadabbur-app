import React, { createContext, useContext, Dispatch, SetStateAction } from "react";
import { ChatMessage, AssistantMessage, Attachment, StoryParagraph } from "@/app/components/chatbot/interfaces/ChatMessage";
import hidePromptExtraOptionsModelBoxArray from "@/app/components/chatbot/interfaces/hidePromptExtraOptionsModelBoxArray";
import { ActionType, ResponseBasedActions } from "@/app/utils/types";


export interface ChatRecord {
  session_id: string | null;
  title: string | null;
  description: string | null;
  created_at: string | null;
}


type AskFn = (
  input: string,
  guidelines?: string | null,
  resend_flag?: boolean,
  resend_message_id?: string | null,
  old_responses_attachments?: {
    responses: AssistantMessage[];
    attachments: Attachment[];
  } | null
) => Promise<void>;

export interface ChatContextType {
  ask: AskFn;
  requestExists: (action: ActionType) => boolean
  stopGeneration: () => void;
  wsRef: React.RefObject<WebSocket | null>;
  inputRef: React.RefObject<HTMLDivElement | null>
  audioRef: React.RefObject<HTMLAudioElement | null>;
  hideExtraOptions: boolean;
  setHideExtraOptions: React.Dispatch<React.SetStateAction<boolean>>;
  selectedModel: string | null;
  active: boolean[];
  setActive: React.Dispatch<React.SetStateAction<boolean[]>>
  reportedMessageID: string | null
  setReportedMessageID: React.Dispatch<React.SetStateAction<string | null>>
  currentPlayableAudio: React.RefObject<{ user_message_id: string | null, response_message_id: string | null, state: "loading" | "playing" | "paused" | "ended" | null } | null>;
  setSelectedModel: React.Dispatch<React.SetStateAction<string | null>>;
  hideModelBox: boolean;
  hideReportContentDialogueBox: boolean | null;
  setHideReportContentDialogueBox: React.Dispatch<React.SetStateAction<boolean | null>>
  hidePromptExtraOptionsModelBoxArray: hidePromptExtraOptionsModelBoxArray[]
  setHidePromptExtraOptionsModelBoxArray: React.Dispatch<React.SetStateAction<hidePromptExtraOptionsModelBoxArray[]>>
  setHideModelBox: React.Dispatch<React.SetStateAction<boolean>>;
  chatHistory: ChatRecord[] | null;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecord[] | null>>;
  selectedSessionID: string | null;
  setSelectedSessionID: React.Dispatch<React.SetStateAction<string | null>>;
  openChatHistoryDialogueBox: boolean;
  setOpenChatHistoryDialogueBox: React.Dispatch<React.SetStateAction<boolean>>;
  sessionID: string | null;
  messages: ChatMessage[];
  setMessages: Dispatch<SetStateAction<ChatMessage[]>>;
  attachedFile: File | null;
  setAttachedFile: Dispatch<SetStateAction<File | null>>;
  currentMode: "normal" | "story" | null;
  setCurrentMode: React.Dispatch<React.SetStateAction<"normal" | "story" | null>>;
  setOpenFullStoryView: React.Dispatch<React.SetStateAction<boolean>>
  setStoryData: React.Dispatch<React.SetStateAction<StoryParagraph[]>>
  openStoryModeExtraOptions: boolean
  setOpenStoryModeExtraOptions: React.Dispatch<React.SetStateAction<boolean>>
  isUploading: boolean
  fileContext: string | null
  showPlaceholder: boolean | null
  isGenerating: boolean
  setOpenImageContainer: React.Dispatch<React.SetStateAction<boolean>>
  responseBasedActions: ResponseBasedActions
  setResponseBasedActions: React.Dispatch<React.SetStateAction<ResponseBasedActions>>
  showFriendlyError: (error: string) => void
}
export const ChatContext = createContext<ChatContextType | null>(null);
