
import QuranPic from "../images/Quran.jpg"
import QuranReading from "../images/QuranReading.jpg"
import DesertPic from "../images/Desert.jpg"
import ArkPic from "../images/OldArk.png"
import { StaticImageData } from "next/image";

const ModelList = [
  {
    model_name: "Llama 3.1 8B",
    provider: "Meta",
    parameters: "235B",
    isNew: true,
    background:
      "bg-linear-to-br rounded-lg from-[#FFB347] via-[#FFCC33] to-[#FFB347]", // Warm Amber (light gold)
  },
  {
    model_name: "Llama 3.3 70B",
    provider: "Meta",
    parameters: "120B",
    isNew: false,
    background:
      "bg-linear-to-br rounded-lg from-[#6DD5FA] via-[#2980B9] to-[#6DD5FA]", // Sky Blue
  },
  {
    model_name: "GPT OSS 120B",
    provider: "OpenAI",
    parameters: "120B",
    isNew: false,
    background:
      "bg-linear-to-br rounded-lg from-[#B993D6] via-[#8CA6DB] to-[#B993D6]", // Soft Lavender Blue
  },
  {
    model_name: "GPT OSS 20B",
    provider: "OpenAI",
    parameters: "20B",
    isNew: false,
    background:
      "bg-linear-to-br rounded-lg from-[#A8EDEA] via-[#FED6E3] to-[#A8EDEA]", // Mint Rose
  },

];

const defaultPromptsNormalMode: { title: string, description: string }[] = [
  {
    title: "Surah Summary",
    description:
      "Provide a concise, neutral summary of the selected Surah based only on well-known, non-sectarian scholarly understandings. Do not offer personal opinions, rulings, or new interpretations.",
  },
  {
    title: "Ayah Explanation",
    description:
      "Explain the meaning of the selected ayah using widely accepted tafsir principles. Stay neutral across schools of thought, avoid issuing religious rulings, and cite sources when possible.",
  },
  {
    title: "Context of Revelation",
    description:
      "Describe the historical context (Asbāb al-Nuzūl) of the selected verse using reliable, established sources. Only share information documented in classical works and avoid speculation.",
  },
  {
    title: "Key Themes",
    description:
      "Identify the major themes present in the selected Surah or ayah based on recognized scholarly commentary. Present themes clearly and objectively without independent interpretation.",
  },
  {
    title: "Arabic Vocabulary Help",
    description:
      "Explain the meaning of specific Qur’anic Arabic words using standard lexical definitions. Provide root meanings where relevant and avoid theological interpretations or rulings.",
  },
  {
    title: "Reflection Prompt",
    description:
      "Offer a gentle, non-prescriptive reflection based on the verse. Keep the reflection general, avoid giving personal religious advice or rulings, and encourage the user to explore established tafsir.",
  },
];

const defaultPromptsStoryMode: { prompt: string, imageSrc: StaticImageData }[] = [
  {
    prompt: "Generate the story of the people of the Cave.",
    imageSrc: QuranReading
  },
  {
    prompt: "Narrate the occasion of first revelation.",
    imageSrc: QuranPic
  },
  {
    prompt: "Generate the story of Prophet Yusuf عليه السلام.",
    imageSrc: DesertPic
  },
  {
    prompt: "Generate the story of Prophet Noah عليه السلام and his people.",
    imageSrc: ArkPic
  }
]

// Option 1: With TypeScript interfaces and mapped options
interface RadioOption {
  id: string;
  value: string;
  label: string;
}

const reportOptions: RadioOption[] = [
  {
    id: "offensive",
    value: "the response is offensive",
    label: "The response is offensive",
  },
  {
    id: "ethical",
    value: "the response violates ethical standards",
    label: "The response violates ethical standards",
  },
  {
    id: "inaccurate",
    value: "the response is inaccurate",
    label: "The response is inaccurate",
  },
  {
    id: "harmful",
    value: "the response is harmful",
    label: "The response is harmful",
  },
  {
    id: "violence",
    value: "the response promotes violence or self-harm",
    label: "The response promotes violence or self-harm",
  },
  {
    id: "spam",
    value: "the response is spam or advertising",
    label: "This appears to be spam or advertising",
  },
  {
    id: "copyright",
    value: "the response infringes on copyright or intellectual property",
    label: "This infringes on copyright or intellectual property",
  },
  {
    id: "privacy",
    value: "the response violates privacy or contains personal information",
    label: "This violates someone's privacy or contains personal information",
  },
  {
    id: "harassment",
    value: "the response is harassment or bullying",
    label: "This is harassment, bullying, or targeted abuse",
  },
  {
    id: "misinformation",
    value: "the response contains misinformation",
    label: "This contains misinformation or fake news",
  },
  {
    id: "other",
    value: "other",
    label: "Other",
  },
];

export {
  ModelList,
  defaultPromptsNormalMode,
  reportOptions,
  defaultPromptsStoryMode
};
