"use client";

import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { useEffect, useRef, useState } from "react";
import OptionsProvider from "./providers/chatbot/OptionsProvider";
import DownArrow from "../icons/arrow-down-head.svg";
import { motion, easeInOut, easeIn, AnimatePresence } from "framer-motion";
import { ModelList } from "@/static/data";
import BottomOptions from "./components/chatbot/UI/BottomOptions";
import ExtraOptions from "./components/chatbot/UI/ExtraOptions";
import ModelBox from "./components/chatbot/UI/ModelBox";

declare global {
  interface Window {
    wsRef?: React.RefObject<WebSocket>;
  }
}

export default function ChatPage() {
  const [messages, setMessages] =
    useState<{ role: "user" | "assistant"; content: string }[]>();

  const inputRef = useRef<HTMLDivElement | null>(null);
  const [showInputButton, setShowInputButton] = useState(false);
  const [ws, setws] = useState<WebSocket | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const websocket = new WebSocket("ws://localhost:8000/ws/chat");
    wsRef.current = websocket;

    // make it globally accessible
    window.wsRef = wsRef as React.RefObject<WebSocket>;

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
      const data = JSON.parse(event.data);
      console.log("Data from websocket", data);

      const type = data.type;
      switch (type) {
        case "assistance_response":
          const reply = data.content ?? "No reply from server";

          console.log("reply from Ai", reply);
          setMessages((prev) => {
            const updated = [...(prev || [])];
            const lastIdx = updated.findLastIndex(
              (m) => m.role === "assistant" && !m.content
            );
            if (lastIdx !== -1) updated[lastIdx].content = reply;
            else updated.push({ role: "assistant", content: reply });
            return updated;
          });

          setLoading(false);
          break;
        case "agent":
          console.log("✅ Agent switched:", data);
          alert(data.message || "Agent switched successfully!");
          break;
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

    setMessages((prev) => [
      ...(prev || []),
      { role: "user", content: input },
      { role: "assistant", content: "" },
    ]);
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
        setShowInputButton(false);
      }
      // console.log(loading && !loadingMessage);
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
    console.log(messages);
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Define a placeholder text for the input box
  const placeholder = "Type your message...";

  return (
    <div className="relative w-screen h-screen bg-gray-50  overflow-y-auto">
      <div className="w-full h-full flex flex-col items-center ">
        <div className="w-full px-4 mt-12 lg:w-2/3 chat-box flex flex-col gap-y-4">
          <>
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
                          {loadingMessage}
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
                        <div className="w-max min-w-40 max-w-full  switzer-500 py-2 px-3 rounded-md bg-white shadow-md">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </AnimatePresence>
                  </div>
                )
              )}
            </AnimatePresence>
            <div ref={messagesEndRef}></div>
          </>
        </div>
        <div className="sticky bottom-0 px-4 pb-4 pt-2 w-full lg:w-2/3 bg-gray-50">
          <div
            className="flex flex-col relative border border-black/10 px-3 py-2 rounded-lg h-40 shadow-md
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
                {placeholder}
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


