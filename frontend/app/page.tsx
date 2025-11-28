"use client";

import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { ReactNode, useContext, useEffect, useRef, useState } from "react";
import ChatProvider from "./providers/chatbot/ChatProvider";
import DownArrow from "../icons/arrow-down-head.svg";
import {
  motion,
  easeInOut,
  easeIn,
  AnimatePresence,
  useAnimationControls,
} from "framer-motion";
import { ModelList } from "@/static/data";
import BottomOptions from "./components/chatbot/UI/BottomOptions";
import ExtraOptions from "./components/chatbot/UI/ExtraOptions";
import PromptSuggestion from "../icons/prompt_suggestion.svg";
import { defaultPrompts } from "@/static/data";
import ModelBox from "./components/chatbot/UI/ModelBox";
import Controls from "./components/chatbot/UI/Controls";
import PromptExtraOptions from "./components/chatbot/UI/PrompExtraOptions";

import { generateNewSessionId } from "./session/session";
import { ChatHisoryDialoguseBox } from "./components/chatbot/UI/ChatHistoryDialogueBox";
import { ChatRecord } from "./context/chatbot/ChatContext";
import { PromptExtraOptionsContext } from "./context/chatbot/PromptExtraOptionsContext";

export default function ChatPage() {
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string }[] | null
  >(null);

  const inputRef = useRef<HTMLDivElement | null>(null);
  const [showPlaceholder, setShowPlaceholder] = useState<boolean | null>(true);
  const [greeting, setGreeting] = useState<string | null>(
    "Assalam O Alaykum, I am Tadabbur, how may I help you today?"
  );
  const wsRef = useRef<WebSocket | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
  const [placeholder, setPlaceholder] = useState<string | null>(
    "Let's learn about the Quran"
  );
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [sessionID, setSessionID] = useState<string | null>(null);
  const [streamingMessageIndex, setStreamingMessageIndex] = useState<
    number | null
  >(null);
  const [chatHistory, setChatHistory] = useState<ChatRecord[] | null>(null);
  const messageScrollFlag = useRef<boolean | null>(false);
  const controls = useAnimationControls();

  function chunkText(text: string, size = 4) {
    const words = text.split(/\s+/);
    const chunks = [];

    for (let i = 0; i < words.length; i += size) {
      chunks.push(words.slice(i, i + size).join(" "));
    }
    return chunks;
  }

  useEffect(() => {
    const websocket = new WebSocket("ws://localhost:8000/ws/chat");
    wsRef.current = websocket;

    wsRef.current.onopen = () => {
      console.log("Connected to websocket successfully!");
      const session_id = generateNewSessionId();
      wsRef.current?.send(
        JSON.stringify({
          type: "session-init",
          session_id: session_id,
          model: "kimi-k2-instruct-0905",
        })
      );
    };

    wsRef.current.onerror = (error) => {
      console.error("An error occured in websocket", error);
    };

    wsRef.current.onclose = () => {
      console.log("Websocket closed!");
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      console.log("Data from websocket", event.data);

      const type = data.type;
      switch (type) {
        case "session_id":
          const session_id = data.session_id;
          const isNew = session_id != sessionID;
          if (isNew) {
            setSessionID(session_id);
            setMessages(null);
          }
          break;

        case "model-selection":
          const model_status = data.status;
          const model_name = data.display_name;
          if (model_status === "acknowledged") {
            alert(`Model is changed to ${model_name}`);
          }

          break;
        case "chat_history":
          const chat_history = data.chat_history;
          console.log(chat_history);
          const history_status = data.status;
          console.log(history_status);
          // handle chat history
          if (history_status === "acknowledged") {
            setChatHistory(chat_history);
          }
          break;

        case "get_chat":
          const status = data.status;
          if (status === "acknowledged") {
            setMessages(null);
            const chat_history = data.chat_history;
            setMessages(chat_history);
          }
          break;

        case "assistance_response":
          const reply: string = data.content ?? "No reply from server";
          setLoadingMessage(null);

          const chunk_array = chunkText(reply, 4); // 4 words per chunk

          setLoading(false);
          messageScrollFlag.current = false;

          (async () => {
            for (const chunk of chunk_array) {
              // smaller delay → faster
              await new Promise((resolve) => setTimeout(resolve, 2));

              setMessages((prev) => {
                const updated = [...(prev || [])];
                const lastIdx = updated.findLastIndex(
                  (m) => m.role === "assistant"
                );

                if (lastIdx !== -1) {
                  updated[lastIdx].content =
                    (updated[lastIdx].content || "") + " " + chunk;
                } else {
                  updated.push({ role: "assistant", content: chunk });
                }
                return updated;
              });
            }
          })().then(() => {
            setStreamingMessageIndex(null);
          });

          break;

        case "agent":
          const agent_type = data.agent;
          switch (agent_type) {
            case "story-telling":
              setPlaceholder("Generate an Islamic story");
              setMessages(null);
              setGreeting(
                "Generate any Islamic story with the finest AI Models."
              );
              break;
            case "tafseer":
              setPlaceholder("Let's lean about the Quran");
              setMessages(null);
              setGreeting(
                "Assalam O Alaykum, I am Tadabbur, how may I help you today?"
              );
              break;
          }
          break;
        case "loading_message":
          const message = data.content ?? "Thinking to enhance response";
          // setLoadingMessage(message);
          break;
        default:
          break;
      }
    };
  }, []);

  const ask = async (input: string) => {
    if (streamingMessageIndex !== null) return;
    setError(null);
    messageScrollFlag.current = false;
    setMessages((prev): { role: "user" | "assistant"; content: string }[] => {
      const updated: { role: "user" | "assistant"; content: string }[] = [
        ...(prev || []),
        { role: "user", content: input },
        { role: "assistant", content: "" }, // placeholder for assistant reply
      ];

      // Track the index of the new assistant message
      setStreamingMessageIndex(updated.length - 1);

      return updated;
    });
    setLoading(true);

    try {
      wsRef.current?.send(
        JSON.stringify({
          messages: [
            ...(messages || []),
            { role: "user", content: input },
          ].slice(-10),
        })
      );
      if (inputRef.current) {
        inputRef.current.innerText = "";
        setShowPlaceholder(true);
      }
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong");
    }
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

  useEffect(() => {
    if (messageScrollFlag.current) return;
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    messageScrollFlag.current = true;
  }, [messages]);

  useEffect(() => {
    controls?.start({
      x: "-60%",
    });
  }, []);

  interface PromptExtraOptionsProviderProps {
    children: ReactNode;
    index: number | null;
  }
  const PromptExtraOptionsProvider: React.FC<
    PromptExtraOptionsProviderProps
  > = ({ children, index }) => {
    const [hidePromptExtraOptionsModelBox, setHidePromptExtraOptionsModelBox] =
      useState<boolean | null>(true);

    return (
      <PromptExtraOptionsContext.Provider
        value={{
          messages,
          index,
          hidePromptExtraOptionsModelBox,
          setHidePromptExtraOptionsModelBox,
          sessionID,
          wsRef,
          ask,
        }}
      >
        {children}
      </PromptExtraOptionsContext.Provider>
    );
  };

  return (
    <div className="relative w-screen h-screen bg-gray-50 flex flex-col items-center">
      <ChatProvider
        chatHistory={chatHistory}
        setChatHistory={setChatHistory}
        wsRef={wsRef}
      >
        <ChatHisoryDialoguseBox />
        <div className="w-full h-full flex flex-col items-center overflow-y-auto">
          <div className="absolute top-0 p-2 w-full">
            <Controls wsRef={wsRef} />
          </div>
          <div
            className={`w-full ${
              messages && messages?.length > 0 ? "h-max" : "h-full"
            }
             px-4 mt-12 lg:w-2/3 chat-box flex flex-col gap-y-4 ${
               !messages ? "justify-center items-center" : ""
             }`}
          >
            <AnimatePresence>
              {!messages && (
                <motion.div
                  // initial={{ opacity: 0, y: -20 }}
                  // animate={{ opacity: 1, y: 110 }}
                  // exit={{ opacity: 0, y: -20 }}
                  className="flex flex-col gap-y-4 items-center self-center"
                >
                  <motion.div
                    key="greeting"
                    transition={{ duration: 0.4, ease: easeInOut }}
                  >
                    <p className="switzer-500 text-center tracking-tight text-4xl px-6 text-black/90">
                      {greeting}
                    </p>
                  </motion.div>
                  <div className="default-prompts-box w-full relative overflow-x-clip">
                    <motion.div
                      animate={controls}
                      transition={{
                        duration: 25,
                        ease: easeInOut,
                        repeat: Infinity,
                        repeatType: "loop",
                      }}
                      className="w-[1200%] md:w-[600%] flex gap-x-2"
                    >
                      {Array.from({ length: 2 }).map((_, i) => (
                        <motion.div key={i} className="carousel w-1/2">
                          <div className="carousel-controls-slider flex">
                            <div className="h-max grid grid-cols-6 grid-rows-1 rounded-md gap-4 w-full">
                              {defaultPrompts.map((prompt, index) => (
                                <motion.div
                                  key={index}
                                  whileHover={{ scale: 1.01 }}
                                  transition={{
                                    duration: 0.5,
                                    ease: easeInOut,
                                  }}
                                  onMouseOver={() => {
                                    controls.stop();
                                  }}
                                  onMouseLeave={() => {
                                    controls.start({ x: "-60%" });
                                  }}
                                  onClick={() => {
                                    ask(
                                      `${prompt.title} ${prompt.description}`
                                    );
                                  }}
                                  className="bg-white rounded-md shadow-sm backdrop-blur-md cursor-pointer"
                                >
                                  <div className="w-full flex flex-col px-3 pt-3 pb-6 gap-y-1">
                                    <div className="flex gap-x-3">
                                      <div className="p-1 h-max border border-black/5 rounded-md">
                                        <PromptSuggestion className="w-5 h-5 fill-current text-green-700" />
                                      </div>
                                      <div className="default-prompt-text-box">
                                        <div className="heading-text">
                                          <p className="switzer-600 tracking-tight text-black/80">
                                            {prompt.title}
                                          </p>
                                        </div>
                                        <div className="system-instructions text-[0.9rem] switzer-500 text-black/80 ">
                                          <p className="">
                                            {prompt.description}
                                          </p>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                </motion.div>
                              ))}
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </motion.div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <AnimatePresence mode="popLayout">
              {messages?.map((message, index) =>
                message.role === "user" ? (
                  <div key={index}>
                    <p className="ml-auto w-max min-w-40 max-w-[20rem] bg-neutral-900 text-white switzer-500 py-2 px-3 rounded-md shadow-md border border-black/5">
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
                            animate={{
                              backgroundPosition: ["200% 0", "-200% 0"],
                            }}
                            transition={{
                              duration: 3,
                              ease: "linear",
                              repeat: Infinity,
                            }}
                          >
                            {loadingMessage}
                          </motion.p>
                          <motion.div
                            animate={{ x: [-4, 6] }}
                            transition={{
                              duration: 1,
                              ease: easeIn,
                              repeat: Infinity,
                              repeatType: "loop",
                            }}
                          >
                            <DownArrow className="mt-[0.32rem] w-4 h-4 -rotate-90" />
                          </motion.div>
                        </motion.div>
                      ) : (
                        <div>
                          <div className="w-max min-w-40 max-w-full switzer-500 py-2 px-3 rounded-md bg-white shadow-md">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              rehypePlugins={[rehypeRaw]}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>
                          {streamingMessageIndex != index && (
                            <div>
                              <PromptExtraOptionsProvider index={index}>
                                <PromptExtraOptions />
                              </PromptExtraOptionsProvider>
                            </div>
                          )}
                        </div>
                      )}
                    </AnimatePresence>
                  </div>
                )
              )}
            </AnimatePresence>
            <div ref={messagesEndRef}></div>
          </div>
        </div>
        <div className="mr-1.5 bg-gray-50 px-4 mt-4 py-4 w-full lg:w-2/3 input-box">
          <div
            className="flex flex-col relative border border-black/10 px-3 py-2 rounded-lg h-40 shadow-md
        "
          >
            <div
              ref={inputRef}
              onInput={(e) => {
                const target = e.target as HTMLDivElement;
                const text = target.textContent.trim() ?? "";
                setShowPlaceholder(text === "");
              }}
              onKeyDown={(e) => {
                handleInput(e);
              }}
              contentEditable
              className="h-2/3 switzer-500 focus:outline-none overflow-y-auto"
            ></div>

            {showPlaceholder && (
              <span
                className={`absolute top-2 pointer-events-none placeholder-input-box switzer-500 text-black`}
              >
                {placeholder}
              </span>
            )}
            <BottomOptions />
            <ExtraOptions />
            <ModelBox modelList={ModelList} />
          </div>
        </div>
      </ChatProvider>
    </div>
  );
}
