const ModelList = [
  {
    model_name: "kimi-k2-instruct-0905",
    provider: "Qwen",
    parameters: "235B",
    isNew: true,
    background:
      "bg-linear-to-br rounded-lg from-[#FFB347] via-[#FFCC33] to-[#FFB347]", // Warm Amber (light gold)
  },
  {
    model_name: "deepseek-v3p1-terminus",
    provider: "DeepSeek",
    parameters: "120B",
    isNew: false,
    background:
      "bg-linear-to-br rounded-lg from-[#6DD5FA] via-[#2980B9] to-[#6DD5FA]", // Sky Blue
  },
  {
    model_name: "gpt-oss-120b",
    provider: "OpenAI",
    parameters: "120B",
    isNew: false,
    background:
      "bg-linear-to-br rounded-lg from-[#B993D6] via-[#8CA6DB] to-[#B993D6]", // Soft Lavender Blue
  },
  {
    model_name: "gpt-oss-20b",
    provider: "OpenAI",
    parameters: "20B",
    isNew: false,
    background:
      "bg-linear-to-br rounded-lg from-[#A8EDEA] via-[#FED6E3] to-[#A8EDEA]", // Mint Rose
  },
  {
    model_name: "qwen3-235b-a22b-instruct",
    provider: "Qwen",
    parameters: "235B",
    isNew: true,
    background:
      "bg-linear-to-br rounded-lg from-[#FBD786] via-[#C6FFDD] to-[#FBD786]", // Soft Sunrise
  },
];

const chatMessages: { role: "user" | "assistant"; content: string }[] = [
  { role: "user", content: "Hi, can you explain what generative AI is?" },
  {
    role: "assistant",
    content:
      "Generative AI refers to artificial intelligence systems capable of creating new content such as text, images, audio, or video by learning patterns from existing data.",
  },
  { role: "user", content: "That’s interesting! Can you give an example?" },
  {
    role: "assistant",
    content:
      "Sure! ChatGPT, DALL·E, and Midjourney are examples of generative AI tools — they can generate text and images from user prompts.",
  },
  {
    role: "user",
    content: "How is generative AI different from traditional AI?",
  },
  {
    role: "assistant",
    content:
      "Traditional AI focuses on classification or prediction based on input data, while generative AI creates new, original outputs that didn’t exist before.",
  },
  { role: "user", content: "Can it be used in video generation too?" },
  {
    role: "assistant",
    content:
      "Yes! Modern generative models like Runway or Pika Labs can generate realistic videos from text prompts using diffusion or transformer-based architectures.",
  },
  {
    role: "user",
    content: "Is there any risk in using generative AI tools?",
  },
  {
    role: "assistant",
    content: "",
  },
];

const dummyChatHistory = [
  {
    session_id: "a162542",
    title: "Surah Baqarah Tafseer",
    description:
      "Overview of major themes and lessons. Focus on guidance and faith.",
    date: "Sep, 2002",
  },
  {
    session_id: "k282383",
    title: "Asbāb al-Nuzūl of Key Verses",
    description:
      "Context behind selected revelations. Explains historical background.",
    date: "Oct, 2002",
  },
  {
    session_id: "u918233",
    title: "Surah Yaseen Summary",
    description:
      "Central message of Surah Yaseen. Covers warnings and glad tidings.",
    date: "Nov, 2002",
  },
  {
    session_id: "x552781",
    title: "Stories of the Prophets in the Quran",
    description:
      "Short summaries of prophetic stories. Focus on moral lessons.",
    date: "Dec, 2002",
  },
  {
    session_id: "p712034",
    title: "Surah Mulk Explanation",
    description:
      "Meaning of verses and key reflections. Emphasis on accountability.",
    date: "Jan, 2003",
  },
  {
    session_id: "m553910",
    title: "Names & Attributes of Allah",
    description:
      "Explanation of selected names from the Quran. Focus on meaning and impact.",
    date: "Feb, 2003",
  },
  {
    session_id: "z831002",
    title: "Surah Rahman Tafseer",
    description:
      "Theme of divine mercy. Structure and repeated verse significance.",
    date: "Mar, 2003",
  },
  {
    session_id: "q482299",
    title: "Makki vs Madani Surahs",
    description:
      "Differences in style and themes. How revelation evolved over time.",
    date: "Apr, 2003",
  },
];

export { ModelList, chatMessages, dummyChatHistory };
