interface ChatMessage {
  message_id: string | null;
  role: "user";
  content: string;
  responses: AssistantMessage[];
  number_of_responses: number | null;
  active_message_index: number | null;
  attached_files?: any[];
}

interface AssistantMessage {
  message_id: string;
  role: "assistant";
  content: string;
  reply_to_message_id: string | null;
  feedback: "liked" | "disliked" | "reported" | null;
}

export type { ChatMessage, AssistantMessage };
