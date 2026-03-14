
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
      "Provide a concise, authentic summary of the Surah Yaseen.",
  },
  {
    title: "Ayah Explanation",
    description:
      "Explain the meaning of the verse number 10 of surah Rahman.",
  },
  {
    title: "Context of Revelation",
    description:
      "Provide the (Asbāb al-Nuzūl) of Surah Quraysh with examples.",
  },
  {
    title: "Surah Audio",
    description:
      "I want to listen to the complete recitation of surah An'faal.",
  },
  {
    title: "Surah Recitation",
    description:
      "I want to read Surah Qamar and Surah Ankaboot.",
  },
  {
    title: "Surah Summary",
    description:
      "Provide a concise, authentic summary of the Surah Yaseen.",
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
