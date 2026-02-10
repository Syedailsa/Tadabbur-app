import { createContext } from "react";

interface PromptExtraOptionsContextType {
  messages: { role: "user" | "assistant"; content: string }[] | null;
  index: number | null;
  message_id: string | null;
  hidePromptExtraOptionsModelBox: boolean | null;
  setHidePromptExtraOptionsModelBox: any;
  sessionID: string | null;
  wsRef: any;
  ask: any;
  content: string;
}

const PromptExtraOptionsContext = createContext<
  PromptExtraOptionsContextType | any
>(null);

export { PromptExtraOptionsContext };
