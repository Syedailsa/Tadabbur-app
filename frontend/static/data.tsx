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

export { ModelList, chatMessages };
