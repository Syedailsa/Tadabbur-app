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

// class StoryParagraph(BaseModel):
// story_paragraph: str = Field(..., description = "An extract representing a paragraph of story")
// image: str = Field(..., description = "Base 64 string of the generated image")

// class StoryOutputSchema(BaseModel):
// complete_story: str = Field(..., description = "The complete story")
// story_segments: List[StoryParagraph] = Field(default_factory = list, description = "The list of story paragraphs")


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
  is_error: boolean
  story_data: StoryParagraph[]
  clicked_feedback: [boolean, boolean]
}

type StoryParagraph = {
  story_paragraph: string;
  paragraph_title: string
  image: string;
}

export type { ChatMessage, AssistantMessage, Attachment, StoryParagraph };
