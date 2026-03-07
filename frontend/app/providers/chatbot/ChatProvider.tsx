import React, { useState, ReactNode } from "react";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { Dispatch, SetStateAction } from "react";
import hidePromptExtraOptionsModelBoxArray from "@/app/components/chatbot/interfaces/hidePromptExtraOptionsModelBoxArray";
import { ChatMessage, Attachment, AssistantMessage } from "@/app/components/chatbot/interfaces/ChatMessage";

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
  openChatHistoryDialogueBox: boolean | null;
  setOpenChatHistoryDialogueBox: React.Dispatch<React.SetStateAction<boolean | null>>;
  currentPlayableAudio: React.RefObject<{ user_message_id: string, response_message_id: string, state: "loading" | "playing" | "paused" | "ended" | null } | null>;
  hidePromptExtraOptionsModelBoxArray: hidePromptExtraOptionsModelBoxArray[]
  setHidePromptExtraOptionsModelBoxArray: React.Dispatch<React.SetStateAction<hidePromptExtraOptionsModelBoxArray[]>>
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
  currentPlayableAudio,
  hideReportContentDialogueBox,
  setHideReportContentDialogueBox,
  hidePromptExtraOptionsModelBoxArray,
  setHidePromptExtraOptionsModelBoxArray
}) => {
  const [hideExtraOptions, setHideExtraOptions] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(
    "Kimi-k2-instruct-0905"
  );
  const [active, setActive] = useState<boolean[]>([false, false, false]);
  const [hideModelBox, setHideModelBox] = useState<boolean>(true);

  const [selectedSessionID, setSelectedSessionID] = useState<string | null>(
    null
  );
  const [openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox] = useState<
    boolean | null
  >(false);
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
        openChatHistoryDialogueBox,
        setOpenChatHistoryDialogueBox,
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
        setHidePromptExtraOptionsModelBoxArray
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export default ChatProvider;
