"use client";

import type React from "react";
import ReactMarkdown from "react-markdown";
import { ReactNode, useContext, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { div, input, p, tr } from "framer-motion/client";
import { tree } from "next/dist/build/templates/app-page";
import OptionsProvider from "./providers/chatbot/OptionsProvider";
import BottomOptions from "@/components/ui/chatbot/BottomOption";
import ImageIcon from "../icons/image_icon.svg";
import Image from "next/image";
import FullSizeIcon from "../icons/full_size_icon.svg";
import DownArrow from "../icons/arrow-down-head.svg";
import Image1 from "../images/Smiling Boy Portrait.png";
import NetworkIntelligence from "../icons/network_intelligence_icon.svg";
import { FC } from "react";
// import ArrowHead from "../icons/arrow-left-bold.svg";
// import ArrowLeft from "../icons/arrow-left.svg";
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
  const [question, setQuestion] = useState("");
  const [messages, setMessages] =
    useState<{ role: "user" | "assistant"; content: string }[]>(chatMessages);
  const inputRef = useRef<HTMLDivElement | null>(null);
  const [showInputButton, setShowInputButton] = useState(false);
  const [ws, setws] = useState<WebSocket | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState<string | null>(
    "Thinking longer for a better answer"
  );

  const [error, setError] = useState<string | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const websocket = new WebSocket("ws://localhost:8000/ws");
    wsRef.current = websocket;

    wsRef.current.onopen = () => {
      console.log("Connected to websocket successfully!");
    };

    wsRef.current.onerror = (error) => {
      console.error("An error occured in websocket", error);
    };

    wsRef.current.onclose = () => {
      console.log("Websocket closed!");
    };

    wsRef.current.onmessage = (event) => {
      const data = event.data;
      console.log("Data from websocket", data);

      const type = data.type;
      switch (type) {
        case "assistant_message":
          const reply = data.content ?? "No reply from server";
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: reply },
          ]);
        case "loading_message":
          const message = data.content ?? "Thinking to enhance response";
          setLoadingMessage(message);
          break;
        default:
          break;
      }
    };
  }, []);

  const ask = async (input: string) => {
    setError(null);

    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setQuestion("");
    setLoading(true);

    try {
      wsRef.current?.send(
        JSON.stringify({
          messages: [...messages, { role: "user", content: input }].slice(-10),
        })
      );
      if (inputRef.current) {
        inputRef.current.innerText = "";
      }
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong");
    } finally {
      setLoading(false);
    }
    // const res = await fetch("http://localhost:8000/api/chat", {
    //   method: "POST",
    //   headers: {
    //     "Content-Type": "application/json",
    //     Authorization: `Bearer ${process.env.NEXT_PUBLIC_CHAT_API_KEY}`,
    //   },
    //   body: JSON.stringify({
    //     messages: [...messages, { role: "user", content: input }].slice(-10),
    //   }),
    // });

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
                    <p className="w-[24rem] switzer-500 p-2 rounded-md bg-pink-200/70">
                      {message.content}
                    </p>
                  )}
                </AnimatePresence>
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
            <OptionsProvider wsRef={wsRef}>
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

const ModelBox: FC<ModelBoxProps> = ({
  modelList,
}): React.ReactElement | null => {
  const [filteredModels, setFilteredModels] =
    useState<ModelBoxProps["modelList"]>(modelList);
  const { hideModelBox, setHideModelBox, setSelectedModel } =
    useContext(OptionsContext);
  const overlayRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (hideModelBox) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHideModelBox(true);
        setFilteredModels(modelList);
      }
    };

    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [hideModelBox, setHideModelBox]);

  if (hideModelBox) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      ref={overlayRef}
      className="w-60 h-40 absolute left-3 bottom-14 rounded-lg bg-white/80 shadow-md backdrop-blur-md overflow-x-clip overflow-y-auto border border-black/10"
    >
      <div className="p-2 flex justify-center">
        <input
          onInput={(e) => {
            const value = e.currentTarget.value.toLowerCase();
            setFilteredModels(
              modelList.filter((m) =>
                m.model_name.toLowerCase().startsWith(value)
              )
            );
          }}
          placeholder="Search model through id, keyword or name"
          className="w-full focus:outline-none rounded-md border border-black/10 switzer-500 text-sm py-1 px-2 placeholder-black/60"
          type="text"
        />
      </div>
      <div className="flex flex-col gap-y-4 px-2 pb-4">
        {filteredModels.length > 0 ? (
          filteredModels?.map((model, index) => (
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              key={index}
              onClick={() => {
                setSelectedModel(model.model_name);
                setHideModelBox(true);
                setFilteredModels(modelList);
              }}
              className={`flex flex-col h-24 p-2 ${model.background} text-white cursor-pointer shadow-md`}
            >
              {/* Provider Qwen */}
              {/* Parameters 235B */}
              {/* Kind Base model */}
              <div className="flex gap-x-2 items-center">
                <NetworkIntelligence className="w-6 h-6 fill-current text-white" />
                <p className="switzer-500 text-xl">{model.provider}</p>
                {model.isNew && (
                  <div className="ml-auto w-8 h-4 rounded-md border border-white/50 flex justify-center items-center">
                    <span className="text-[0.5rem] switzer-500">NEW</span>
                  </div>
                )}
              </div>
              <div className="mt-auto flex">
                <p className="inter-600 text-xs">{model.model_name}</p>
                <p className="ml-auto inter-600 text-xs">{model.parameters}</p>
              </div>
            </motion.div>
          ))
        ) : (
          <div className="p-2">
            <p className="switzer-500 text-sm">No model found.</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};
