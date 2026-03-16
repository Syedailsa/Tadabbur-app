import React, { useState, ReactNode } from "react";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { Dispatch, SetStateAction } from "react";
import hidePromptExtraOptionsModelBoxArray from "@/app/components/chatbot/interfaces/hidePromptExtraOptionsModelBoxArray";
import { ChatMessage, Attachment, AssistantMessage, StoryParagraph } from "@/app/components/chatbot/interfaces/ChatMessage";

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

interface ChatProviderProps {
  ask: AskFn;
  stopGeneration: () => void;
  inputRef: React.RefObject<HTMLDivElement | null>;
  wsRef: React.RefObject<WebSocket | null>;
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  children: ReactNode;
  sessionID: string | null;
  chatHistory: ChatRecord[] | null;
  hideReportContentDialogueBox: boolean | null;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  setHideReportContentDialogueBox: React.Dispatch<React.SetStateAction<boolean | null>>
  attachedFile: File | null;
  setAttachedFile: Dispatch<SetStateAction<File | null>>;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecord[] | null>>;
  currentPlayableAudio: React.RefObject<{ user_message_id: string, response_message_id: string, state: "loading" | "playing" | "paused" | "ended" | null } | null>;
  hidePromptExtraOptionsModelBoxArray: hidePromptExtraOptionsModelBoxArray[]
  setHidePromptExtraOptionsModelBoxArray: React.Dispatch<React.SetStateAction<hidePromptExtraOptionsModelBoxArray[]>>
  active: boolean[];
  setActive: React.Dispatch<React.SetStateAction<boolean[]>>;
  openChatHistoryDialogueBox: boolean;
  setOpenChatHistoryDialogueBox: React.Dispatch<React.SetStateAction<boolean>>
  currentMode: "normal" | "story" | null;
  setCurrentMode: React.Dispatch<React.SetStateAction<"normal" | "story" | null>>;
  setOpenFullStoryView: React.Dispatch<React.SetStateAction<boolean>>
  setStoryData: React.Dispatch<React.SetStateAction<StoryParagraph[]>>
  openStoryModeExtraOptions: boolean
  setOpenImageContainer: React.Dispatch<React.SetStateAction<boolean>>
  setOpenStoryModeExtraOptions: React.Dispatch<React.SetStateAction<boolean>>
  isUploading: boolean
  fileContext: string | null
  showPlaceholder: boolean | null
  isGenerating: boolean
}

const ChatProvider: React.FC<ChatProviderProps> = ({
  children,
  wsRef,
  chatHistory,
  setChatHistory,
  sessionID,
  messages,
  setMessages,
  attachedFile,
  setAttachedFile,
  audioRef,
  ask,
  stopGeneration,
  currentPlayableAudio,
  hideReportContentDialogueBox,
  setHideReportContentDialogueBox,
  hidePromptExtraOptionsModelBoxArray,
  setHidePromptExtraOptionsModelBoxArray,
  active,
  setActive,
  openChatHistoryDialogueBox,
  setOpenChatHistoryDialogueBox,
  currentMode,
  setCurrentMode,
  setOpenFullStoryView,
  setStoryData,
  openStoryModeExtraOptions,
  setOpenStoryModeExtraOptions,
  isUploading,
  fileContext,
  showPlaceholder,
  inputRef,
  isGenerating,
setOpenImageContainer
}) => {
  const [hideExtraOptions, setHideExtraOptions] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(
    "Kimi-k2-instruct-0905"
  );
  const [hideModelBox, setHideModelBox] = useState<boolean>(true);

  const [selectedSessionID, setSelectedSessionID] = useState<string | null>(
    null
  );
  const [reportedMessageID, setReportedMessageID] = useState<string | null>(null);

  return (
    <ChatContext.Provider
      value={{
        audioRef,
        ask,
        wsRef,
        hideExtraOptions,
        setHideExtraOptions,
        selectedModel,
        setSelectedModel,
        hideModelBox,
        setHideModelBox,
        active,
        setActive,
        selectedSessionID,
        setSelectedSessionID,
        chatHistory,
        setChatHistory,
        reportedMessageID,
        setReportedMessageID,
        attachedFile,
        setAttachedFile,
        sessionID,
        messages,
        setMessages,
        currentPlayableAudio,
        hideReportContentDialogueBox,
        setHideReportContentDialogueBox,
        hidePromptExtraOptionsModelBoxArray,
        setHidePromptExtraOptionsModelBoxArray,
        openChatHistoryDialogueBox,
        setOpenChatHistoryDialogueBox,
        currentMode,
        setCurrentMode,
        setOpenFullStoryView,
        setStoryData,
        openStoryModeExtraOptions,
        setOpenStoryModeExtraOptions,
        isUploading,
        fileContext,
        showPlaceholder,
        inputRef,
        isGenerating,
        stopGeneration,
        setOpenImageContainer
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export default ChatProvider;
