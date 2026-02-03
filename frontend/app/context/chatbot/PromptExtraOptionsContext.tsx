import { createContext } from "react";

interface PromptExtraOptionsContextType {
  messages: { role: "user" | "assistant"; content: string }[] | null;
  index: number | null;
}

const PromptExtraOptionsContext = createContext<
  PromptExtraOptionsContextType | any
>(null);

export { PromptExtraOptionsContext };
