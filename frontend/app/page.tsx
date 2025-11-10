// "use client"

// import type React from "react"
// import ReactMarkdown from "react-markdown"
// import { useEffect, useRef, useState } from "react"
// import { Button } from "@/components/ui/button"
// import { Textarea } from "@/components/ui/textarea"
// import { Send, MessageCircle } from "lucide-react"

// export default function ChatPage() {
//   const [question, setQuestion] = useState("")
//   const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([])
//   const [loading, setLoading] = useState(false)
//   const [error, setError] = useState<string | null>(null)
//   const viewportRef = useRef<HTMLDivElement | null>(null)
//   const messagesEndRef = useRef<HTMLDivElement | null>(null)

//   useEffect(() => {
//     if (messages.length === 0) {
//       setMessages([
//         {
//           role: "assistant",
//           content:
//             "👋 Hi, I'm Tadabbur your Quran AI app! ask me what you want about quran.",
//         },
//       ])
//     }
//   }, [])

//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
//   }, [messages, loading])

//   const ask = async (e: React.FormEvent) => {
//     e.preventDefault()
//     setError(null)
//     if (!question.trim()) return
//     const q = question.trim()

//     setMessages((prev) => [...prev, { role: "user", content: q }])
//     setQuestion("")
//     setLoading(true)

//     try {
//       const res = await fetch("http://localhost:8000/api/chat", {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//           Authorization: `Bearer ${process.env.NEXT_PUBLIC_CHAT_API_KEY}`,
//         },
//         body: JSON.stringify({
//           messages: [...messages, { role: "user", content: q }].slice(-10),
//         }),
//       })

//       if (!res.ok) {
//         const txt = await res.text()
//         throw new Error(txt || "API error")
//       }

//       const data = await res.json()
//       const reply = data.reply ?? "No reply from server"
//       setMessages((prev) => [...prev, { role: "assistant", content: reply }])
//     } catch (err: any) {
//       setError(err?.message ?? "Something went wrong")
//     } finally {
//       setLoading(false)
//     }
//   }

//   return (
//     <div className="h-screen bg-gradient-to-br from-background via-background to-secondary flex flex-col">
//       <div className="bg-gradient-to-r from-primary to-accent shadow-sm border-b border-border">
//         <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
//           <div className="bg-primary-foreground p-2 rounded-lg">
//             <MessageCircle className="w-6 h-6 text-emerald-900" />
//           </div>
//           <div>
//             <h1 className="text-xl font-bold text-primary-foreground">Tadabbur AI App</h1>
//             <p className="text-sm text-primary-foreground/80">guidance on Quranic knowledge</p>
//           </div>
//         </div>
//       </div>

//       <div className="flex-1 overflow-hidden flex flex-col">
//         <div ref={viewportRef} className="flex-1 overflow-y-auto p-4 md:p-6">
//           <div className="mx-auto max-w-3xl space-y-4">
//             {messages.map((m, i) => {
//               const isUser = m.role === "user"
//               return (
//                 <div
//                   key={i}
//                   className={`flex ${isUser ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2`}
//                   role="group"
//                   aria-label={isUser ? "User message" : "Assistant message"}
//                 >
//                   <div
//                     className={`max-w-[80%] md:max-w-[65%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
//                       isUser
//                         ? "bg-primary text-primary-foreground rounded-br-none"
//                         : "bg-card text-foreground border border-border rounded-bl-none"
//                     }`}
//                   >
//                     <div className="prose prose-sm max-w-none dark:prose-invert">
//                       <ReactMarkdown
//                         components={{
//                           p: ({ node, ...props }) => <p className="mb-1 last:mb-0" {...props} />,
//                           strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
//                           ul: ({ node, ...props }) => <ul className="list-disc pl-4 my-1" {...props} />,
//                           ol: ({ node, ...props }) => <ol className="list-decimal pl-4 my-1" {...props} />,
//                           li: ({ node, ...props }) => <li className="mb-0.5" {...props} />,
//                           a: ({ node, ...props }) => <a className="text-accent underline" {...props} />,
//                         }}
//                       >
//                         {m.content}
//                       </ReactMarkdown>
//                     </div>
//                   </div>
//                 </div>
//               )
//             })}
//             {loading && (
//               <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2">
//                 <div className="bg-card text-foreground border border-border rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
//                   <div className="flex items-center gap-2">
//                     <div className="flex gap-1">
//                       <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
//                       <div
//                         className="w-2 h-2 bg-accent rounded-full animate-pulse"
//                         style={{ animationDelay: "0.2s" }}
//                       />
//                       <div
//                         className="w-2 h-2 bg-accent rounded-full animate-pulse"
//                         style={{ animationDelay: "0.4s" }}
//                       />
//                     </div>
//                     <span className="text-xs text-muted-foreground">thinking...</span>
//                   </div>
//                 </div>
//               </div>
//             )}
//             {error && (
//               <div className="flex justify-center">
//                 <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-lg text-sm border border-destructive/20">
//                   {error}
//                 </div>
//               </div>
//             )}
//             <div ref={messagesEndRef} />
//           </div>
//         </div>

//         <div className="border-t border-border bg-card shadow-lg">
//           <form onSubmit={ask} className="max-w-3xl mx-auto p-4 md:p-6 space-y-2">
//             <div className="flex gap-2 items-end">
//               <Textarea
//                 value={question}
//                 onChange={(e) => setQuestion(e.target.value)}
//                 placeholder="Ask me about quran related topics... (Shift+Enter for new line)"
//                 className="min-h-12 max-h-32 resize-none bg-background border-border text-foreground placeholder:text-muted-foreground"
//                 onKeyDown={(e) => {
//                   if (e.key === "Enter" && !e.shiftKey) {
//                     e.preventDefault()
//                     ask(e as any)
//                   }
//                 }}
//               />
//               <Button
//                 type="submit"
//                 disabled={loading || !question.trim()}
//                 className="bg-primary hover:bg-accent text-primary-foreground px-6 h-12 transition-all"
//               >
//                 {loading ? (
//                   <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
//                 ) : (
//                   <Send className="w-4 h-4" />
//                 )}
//               </Button>
//             </div>

//             <div className="text-xs text-muted-foreground text-center">
//               Helpful information for demonstration purposes only.
//             </div>
//           </form>
//         </div>
//       </div>
//     </div>
//   )
// }


"use client"

import type React from "react";
import ReactMarkdown from "react-markdown";
import { ReactNode, useContext, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, MessageCircle } from "lucide-react";
import { div, input, p, tr } from "framer-motion/client";
import { tree } from "next/dist/build/templates/app-page";
import OptionsProvider from "./providers/chatbot/OptionsProvider";
import AttachIcon from "../icons/attach_icon.svg";
import StoryIcon from "../icons/story_telling_icon.svg";
import MicIcon from "../icons/mic_icon.svg";
import ImageIcon from "../icons/image_icon.svg";
import Image from "next/image";
import FullSizeIcon from "../icons/full_size_icon.svg";
import DownArrow from "../icons/arrow-down-head.svg";
import Image1 from "../images/Smiling Boy Portrait.png";
import NetworkIntelligence from "../icons/network_intelligence_icon.svg";
import { FC } from "react";
// import ArrowHead from "../icons/arrow-left-bold.svg";
// import ArrowLeft from "../icons/arrow-left.svg";
import PlusIcon from "../icons/plus-icon.svg";
import {
  motion,
  easeInOut,
  useAnimation,
  easeIn,
  AnimatePresence,
} from "framer-motion";
import { OptionsContext } from "./context/chatbot/OptionsContext";
import { ModelList } from "@/static/data";
import { chatMessages } from "@/static/data";

export default function ChatPage() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const viewportRef = useRef<HTMLDivElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  // Initialize WebSocket on mount
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/chat")

    ws.onopen = () => {
      ws.send(JSON.stringify({
        authorization: `Bearer ${process.env.NEXT_PUBLIC_CHAT_API_KEY}`,
      }))
      console.log("✅ WebSocket connected")
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === "assistance_response") {
        setMessages((prev) => [...prev, { role: "assistant", content: data.content }])
        setLoading(false)
      } else if (data.type === "error") {
        setError(data.content)
        setLoading(false)
      } else if (data.type === "connection_ack") {
        console.log("Server acknowledged connection")
      }
    }

    ws.onerror = (err) => console.error("WebSocket error:", err)
    ws.onclose = () => console.warn("WebSocket closed")

    setSocket(ws)

    return () => ws.close()
  }, [])

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content:
            "👋 Hi, I'm Tadabbur your Quran AI app! ask me what you want about quran.",
        },
      ])
    }
  }, [])

  useEffect(() => {
    const websocket = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = websocket;

  const ask = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!question.trim() || !socket) return

    const q = question.trim()
    setMessages((prev) => [...prev, { role: "user", content: q }])
    setQuestion("")
    setLoading(true)

    // Send to backend via WebSocket
    socket.send(JSON.stringify({
      messages: [...messages, { role: "user", content: q }].slice(-10),
    }))
  }

    // moved the logic to websocket
  };

  const handleInput = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!inputRef.current) return;
    if (e.key === "Enter") {
      e.preventDefault();
      const input = inputRef.current?.innerText;
      if (input.trim() != "") {
        ask(input);
      }
    }
  };

  return (
    <div className="w-screen h-screen bg-gray-50">
      <div className="w-full h-full flex flex-col items-center ">
        <div className="p-4 mt-12 w-full lg:w-1/2 chat-section flex flex-col gap-y-4 overflow-y-auto">
          {messages?.map((message, index) =>
            message.role === "user" ? (
              <div key={index}>
                <p className="ml-auto w-[24rem] switzer-500 p-2 rounded-md bg-blue-200/70">
                  {message.content}
                </p>
              </div>
            ) : (
              <div key={index}>
                <AnimatePresence mode="wait">
                  {loading && !loadingMessage && !message.content ? (
                    <motion.div
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{
                        duration: 0.8,
                        ease: easeInOut,
                        repeat: Infinity,
                        repeatType: "loop",
                      }}
                      className="w-3 h-3 rounded-full bg-black"
                    ></motion.div>
                  ) : loadingMessage && !message.content ? (
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{
                        duration: 0.1,
                        ease: easeInOut,
                        type: "spring",
                      }}
                      exit={{ opacity: 0 }}
                      className="w-max flex gap-x-1"
                    >
                      <motion.p
                        className="space-grotesk-500 text-black/60 bg-linear-to-l from-black-40 via-bg-black/50 to-black/60 bg-size-[200%_100%] bg-clip-text"
                        animate={{ backgroundPosition: ["200% 0", "-200% 0"] }}
                        transition={{
                          duration: 3,
                          ease: "linear",
                          repeat: Infinity,
                        }}
                      >
                        {m.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )
            })}
            {loading && (
              <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2">
                <div className="bg-card text-foreground border border-border rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                      <div className="w-2 h-2 bg-accent rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
                      <div className="w-2 h-2 bg-accent rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
                    </div>
                    <span className="text-xs text-muted-foreground">thinking...</span>
                  </div>
                </div>
              </div>
            )}
            {error && (
              <div className="flex justify-center">
                <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-lg text-sm border border-destructive/20">
                  {error}
                </div>
              </div>
            )
          )}
        </div>

        <div className="mt-auto p-4 w-full lg:w-1/2">
          <div
            className="flex flex-col relative input-box border border-black/10 px-3 py-2 rounded-lg h-40 shadow-md
        "
          >
            <div
              ref={inputRef}
              onInput={(e) => {
                const target = e.target as HTMLDivElement;
                const text = target.textContent.trim() ?? "";
                setShowInputButton(text !== "");
              }}
              onKeyDown={(e) => {
                handleInput(e);
              }}
              contentEditable
              className="h-2/3 switzer-500 focus:outline-none overflow-y-auto"
            ></div>
            {!showInputButton && (
              <span
                className={`absolute top-2 pointer-events-none placeholder-input-box switzer-500 text-black`}
              >
                Let's learn about the Quran.
              </span>
            )}
            <OptionsProvider>
              <BottomOptions />
              <ExtraOptions />
              <ModelBox modelList={ModelList} />
            </OptionsProvider>
          </div>
        </div>
      </div>
    </div>
  );
}

const BottomOptions = () => {
  const {
    hideExtraOptions,
    setHideExtraOptions,
    selectedModel,
    setSelectedModel,
    hideModelBox,
    setHideModelBox,
  } = useContext(OptionsContext);

  return (
    <div
      id="bottom-options"
      className="w-full flex gap-x-1 mt-auto items-center"
    >
      <motion.div
        whileTap={{ backgroundColor: "#0000003D" }}
        whileHover={{ backgroundColor: "#0000000D" }}
        id="choose-model-box"
        onClick={(e) => {
          e.stopPropagation();
          setHideModelBox((prev) => !prev);
        }}
        className="relative flex flex-row-reverse gap-x-1 py-1 pr-3 pl-4 rounded-full cursor-pointer items-center"
      >
        <motion.div className="mt-0.2">
          <DownArrow className="w-5 h-5" />
        </motion.div>
        <p className="switzer-500 text-[0.96rem]">{selectedModel}</p>
      </motion.div>
      <motion.div className={`ml-auto flex gap-x-1`}>
        <motion.div
          onClick={(e) => {
            e.stopPropagation();
            setHideExtraOptions((prev) => !prev);
          }}
          animate={{
            backgroundColor: hideExtraOptions ? "#00000000" : "#0000000D",
          }}
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className={`w-9 h-9 rounded-full flex items-center justify-center cursor-pointer
          }`}
        >
          <PlusIcon className="fill-current w-5 h-5 text-black" />
        </motion.div>
        <motion.div
          id="story-telling-box"
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="flex gap-x-1 px-3 py-1 rounded-full cursor-pointer items-center"
        >
          <StoryIcon className="fill-current w-5 h-5 text-black" />
          <span className="w-max switzer-500 text-[0.96rem]">
            Story telling
          </span>
        </motion.div>

        <motion.div
          id="mic-icon-box"
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="w-9 h-9 rounded-full flex items-center justify-center cursor-pointer"
        >
          <MicIcon className="w-5 h-5 fill-current text-black" />
        </motion.div>

        <motion.div
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="rounded-full w-9 h-9 cursor-pointer flex justify-center items-center"
          id="attach-files-box"
        >
          <AttachIcon className="fill-current text-black w-5 h-5" />
        </motion.div>
      </motion.div>
    </div>
  );
};

const ExtraOptions = (): React.ReactElement | null => {
  const { hideExtraOptions, setHideExtraOptions } = useContext(OptionsContext);
  const scrollInterval = useRef<NodeJS.Timeout | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const [hasScrolled, setHasScrolled] = useState<boolean>(false);
  const scrollY = useRef(0);
  const controls = useAnimation();

  useEffect(() => {
    if (hideExtraOptions) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHideExtraOptions(true);
      }
    };
    document.addEventListener("click", handleOutsideClick);

    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [hideExtraOptions, setHideExtraOptions]);

  if (hideExtraOptions) return null;

  const startScrolling = (direction: "up" | "down") => {
    stopScrolling();

    scrollInterval.current = setInterval(() => {
      scrollY.current += direction === "down" ? -2 : 2;
      scrollY.current = Math.max(Math.min(scrollY.current, 0), -450);
      controls.start({ y: scrollY.current, transition: { duration: 0.1 } });
      setHasScrolled(scrollY.current < 0);
    }, 20);
  };

  const stopScrolling = () => {
    if (scrollInterval.current) {
      clearInterval(scrollInterval.current);
      scrollInterval.current = null;
    }
  };
  interface OptionProps {
    title: string;
    isNew: boolean | null;
    description: string;
    isImage: boolean | null;
    icon: React.ElementType;
  }
  const Option: FC<OptionProps> = ({
    title,
    icon: Icon,
    description,
    isNew,
    isImage,
  }) => (
    <motion.div
      onClick={() => {
        setHideExtraOptions(true);
      }}
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.2, ease: easeInOut }}
      id={`${title}-generation-box`}
      className="relative flex flex-col items-center shadow-xs h-max gap-y-1 p-2 cursor-pointer border rounded-md border-black/5"
    >
      {isImage ? (
        <Image
          className="rounded-md w-40 h-36 object-cover object-top"
          src={Image1}
          alt="smiling boy"
        ></Image>
      ) : (
        <video
          className="w-40 h-56 rounded-md object-cover object-top"
          src="/videos/ai_video.mp4"
          autoPlay
          muted
          playsInline
          loop
        ></video>
      )}
      {isNew && (
        <div className="absolute w-8 rounded-sm h-4 right-2 top-1 shadow-md bg-amber-400 flex justify-center items-center">
          <span className="poppins-semibold text-[0.6rem] text-white">NEW</span>
        </div>
      )}
      <div className="relative flex">
        <p className="switzer-500 text-sm">
          {title}
          <br />
          <span className="text-black/50">{description}</span>
        </p>
        <motion.div className="absolute border border-black/5 flex justify-center items-center w-4.5 h-4.5 rounded-sm right-0 bottom-0 hover:text-black/90 text-black/70">
          <FullSizeIcon className="w-3.5 h-3.5 fill-current " />
        </motion.div>
      </div>
    </motion.div>
  );

  return (
    <motion.div
      ref={overlayRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute right-57 backdrop-blur-md bottom-14 rounded-lg w-50 h-58 p-2 shadow-md bg-white/80 border border-black/10 overflow-x-clip overflow-y-hidden"
    >
      <motion.div
        className="flex flex-col gap-y-4 w-full justify-center"
        animate={controls}
      >
        <Option
          title="Image Generation"
          description="Powerful, high-quality image generation through our latest state of the art diffusion models."
          icon={ImageIcon}
          isNew={true}
          isImage={true}
        />
        <Option
          title="Video Generation"
          description="Seamless, realistic and and modernist ultra high quality videos through our latest Generative AI models."
          isImage={false}
          icon={ImageIcon}
          isNew={true}
        />
      </motion.div>
      <div className="relative sticky -bottom-3 w-full h-10 pointer-events-none flex justify-center items-center">
        {/* Blurred background layer */}
        <div className="absolute inset-0 bg-white blur-xs" />

        {/* Arrow layer (not blurred) */}
        <div className={`flex w-full mb-2`}>
          <div
            className="w-6 h-6 ml-19 shadow-sm relative flex justify-center items-center rounded-full hover:bg-black/10 border hover:inset-shadow-black/10 border-black/5 pointer-events-auto cursor-pointer"
            onMouseEnter={() => {
              startScrolling("down");
            }}
            onMouseLeave={stopScrolling}
          >
            <DownArrow className="w-4 h-4" />
          </div>
          {hasScrolled && (
            <div
              className="w-6 h-6 ml-auto shadow-sm relative flex justify-center items-center rounded-full hover:bg-black/10 border hover:inset-shadow-black/10 border-black/5 pointer-events-auto cursor-pointer"
              onMouseEnter={() => {
                startScrolling("up");
              }}
              onMouseLeave={stopScrolling}
            >
              <DownArrow className="rotate-180 w-4 h-4" />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

interface ModelBoxProps {
  modelList: {
    model_name: string;
    provider: string;
    parameters: string;
    isNew: boolean;
    background: string;
  }[];
}

