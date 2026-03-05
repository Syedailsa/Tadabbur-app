import { SurahForAudios, SurahForVerseImages } from "./Surah";
interface ChatMessage {
  message_id: string;
  role: "user";
  content: string;
  attachments: Attachment[];
  responses: AssistantMessage[];
  number_of_responses: number;
  active_message_index: number;
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
  story_data: StoryParagraph[]
}

type StoryParagraph = {
  story_paragraph: string;
  paragraph_title: string
  image: string;
}

export type { ChatMessage, AssistantMessage, Attachment, StoryParagraph };
