import { SurahForAudios, SurahForVerseImages } from "./Surah";
interface ChatMessage {
  message_id: string;
  role: "user";
  content: string;
  attachments: Attachment[];
  responses: AssistantMessage[];
  number_of_responses: number | null;
  active_message_index: number | null;
  attached_files?: any[];
}

interface Attachment {
  attachmentType: string
  attachmentName: string
}

interface AssistantMessage {
  message_id: string;
  role: "assistant";
  content: string;
  reply_to_message_id: string | null;
  feedback: "liked" | "disliked" | "reported" | null;
  audio_link: string | null
  audio_state: "loading" | "playing" | "paused" | "ended" | null
  has_verse_audio: boolean;
  verse_audio_data: SurahForAudios[]
  has_verse_image: boolean;
  verse_images: SurahForVerseImages[]
}


export type { ChatMessage, AssistantMessage, Attachment };
