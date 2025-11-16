// "use client";

// import type React from "react";
// import ReactMarkdown from "react-markdown";
// import remarkGfm from "remark-gfm";
// import rehypeRaw from "rehype-raw";
// import { useEffect, useRef, useState } from "react";
// import OptionsProvider from "./providers/chatbot/OptionsProvider";
// import DownArrow from "../icons/arrow-down-head.svg";
// import { motion, easeInOut, easeIn, AnimatePresence } from "framer-motion";
// import { ModelList } from "@/static/data";
// import BottomOptions from "./components/chatbot/UI/BottomOptions";
// import ExtraOptions from "./components/chatbot/UI/ExtraOptions";
// import ModelBox from "./components/chatbot/UI/ModelBox";
// import Controls from "./components/chatbot/UI/Controls";
// import { generateNewSessionId } from "./session/session";

// export default function ChatPage() {
//   const [messages, setMessages] = useState<
//     { role: "user" | "assistant"; content: string }[] | null
//   >(null);

//   const inputRef = useRef<HTMLDivElement | null>(null);
//   const [showInputButton, setShowInputButton] = useState(false);
//   const [greeting, setGreeting] = useState<string | null>(
//     "Assalam O Alaykum, I am Tadabbur, how may I help you today?"
//   );
//   const wsRef = useRef<WebSocket | null>(null);
//   const [loading, setLoading] = useState(false);
//   const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
//   const [placeholder, setPlaceholder] = useState<string | null>(
//     "Let's learn about the Quran"
//   );
//   const [error, setError] = useState<string | null>(null);
//   const viewportRef = useRef<HTMLDivElement | null>(null);
//   const messagesEndRef = useRef<HTMLDivElement | null>(null);
//   const [sessionID, setSessionID] = useState<string | null>(null);

//   useEffect(() => {
//     if (!wsRef.current) return;

//     const session_id = generateNewSessionId();
//     wsRef.current?.send(
//       JSON.stringify({ type: "new-session", session_id: session_id })
//     );
//   }, [wsRef.current]);

//   useEffect(() => {
//     const websocket = new WebSocket("ws://localhost:8000/ws/chat");
//     wsRef.current = websocket;

//     wsRef.current.onopen = () => {
//       console.log("Connected to websocket successfully!");
//     };

//     wsRef.current.onerror = (error) => {
//       console.error("An error occured in websocket", error);
//     };

//     wsRef.current.onclose = () => {
//       console.log("Websocket closed!");
//     };

//     wsRef.current.onmessage = (event) => {
//       const data = JSON.parse(event.data);
//       console.log("Data from websocket", data);

//       const type = data.type;
//       switch (type) {
//         case "session_id":
//           const session_id = data.session_id;
//           const isNew = session_id != sessionID;
//           if (isNew) {
//             setSessionID(session_id);
//             setMessages(null);
//           }
//           break;

//         case "chat-history":
//           const chat_history = data.chat_history;
//           break;
//         case "assistance_response":
//           const reply = data.content ?? "No reply from server";

//           console.log("reply from Ai", reply);
//           setMessages((prev) => {
//             const updated = [...(prev || [])];
//             const lastIdx = updated.findLastIndex(
//               (m) => m.role === "assistant" && !m.content
//             );
//             if (lastIdx !== -1) updated[lastIdx].content = reply;
//             else updated.push({ role: "assistant", content: reply });
//             return updated;
//           });
//           setLoading(false);
//           break;
//         case "agent":
//           const agent_type = data.agent;
//           switch (agent_type) {
//             case "story-telling":
//               setPlaceholder("Generate an Islamic story");
//               setMessages(null);
//               setGreeting(
//                 "Generate any Islamic story with the finest AI Models."
//               );
//               break;
//             case "tafseer":
//               setPlaceholder("Let's lean about the Quran");
//               setMessages(null);
//               setGreeting(
//                 "Assalam O Alaykum, I am Tadabbur, how may I help you today?"
//               );
//               break;
//           }
//           break;
//         case "loading_message":
//           const message = data.content ?? "Thinking to enhance response";
//           setLoadingMessage(message);
//           break;
//         default:
//           break;
//       }
//     };
//   }, []);

//   const ask = async (input: string) => {
//     setError(null);

//     setMessages((prev) => [
//       ...(prev || []),
//       { role: "user", content: input },
//       { role: "assistant", content: "" },
//     ]);
//     setLoading(true);

//     try {
//       wsRef.current?.send(
//         JSON.stringify({
//           messages: [
//             ...(messages || []),
//             { role: "user", content: input },
//           ].slice(-10),
//         })
//       );

//       if (inputRef.current) {
//         inputRef.current.innerText = "";
//         setShowInputButton(false);
//       }
//       // console.log(loading && !loadingMessage);
//     } catch (err: any) {
//       setError(err?.message ?? "Something went wrong");
//     }
//   };

//   const handleInput = (e: React.KeyboardEvent<HTMLDivElement>) => {
//     if (!inputRef.current) return;
//     if (e.key === "Enter") {
//       e.preventDefault();
//       const input = inputRef.current?.innerText;
//       if (input.trim() != "") {
//         ask(input);
//       }
//     }
//   };

//   useEffect(() => {
//     console.log(messages);
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages]);

//   return (
//     <div className="relative w-screen h-screen bg-gray-50  overflow-y-auto">
//       <div className="w-full h-full flex flex-col items-center ">
//         <div className="absolute top-0 p-2 w-full">
//           <Controls wsRef={wsRef} />
//         </div>
//         <div
//           className={`w-full h-full flex-1 px-4 mt-12 lg:w-2/3 chat-box flex flex-col gap-y-4 ${
//             !messages ? "justify-center items-center" : ""
//           }`}
//         >
//           <AnimatePresence>
//             {!messages && (
//               <motion.div
//                 key="greeting"
//                 initial={{ opacity: 0, y: -20 }}
//                 animate={{ opacity: 1, y: 0 }}
//                 exit={{ opacity: 0, y: -20 }}
//                 transition={{ duration: 0.2, ease: easeInOut }}
//               >
//                 <p className="switzer-500 text-center tracking-tight text-4xl px-6">
//                   {greeting}
//                 </p>
//               </motion.div>
//             )}
//           </AnimatePresence>
//           <AnimatePresence mode="popLayout">
//             {messages?.map((message, index) =>
//               message.role === "user" ? (
//                 <div key={index}>
//                   <p className="ml-auto w-max min-w-40 max-w-[20rem] bg-neutral-900 text-white switzer-500 py-2 px-3 rounded-md shadow-md border border-black/5">
//                     {message.content}
//                   </p>
//                 </div>
//               ) : (
//                 <div key={index}>
//                   <AnimatePresence mode="wait">
//                     {loading && !loadingMessage && !message.content ? (
//                       <motion.div
//                         animate={{ scale: [1, 1.2, 1] }}
//                         transition={{
//                           duration: 0.8,
//                           ease: easeInOut,
//                           repeat: Infinity,
//                           repeatType: "loop",
//                         }}
//                         className="w-3 h-3 rounded-full bg-black"
//                       ></motion.div>
//                     ) : loadingMessage && !message.content ? (
//                       <motion.div
//                         initial={{ opacity: 0, x: -20 }}
//                         animate={{ opacity: 1, x: 0 }}
//                         transition={{
//                           duration: 0.1,
//                           ease: easeInOut,
//                           type: "spring",
//                         }}
//                         exit={{ opacity: 0 }}
//                         className="w-max flex gap-x-1"
//                       >
//                         <motion.p
//                           className="space-grotesk-500 text-black/60 bg-linear-to-l from-black-40 via-bg-black/50 to-black/60 bg-size-[200%_100%] bg-clip-text"
//                           animate={{
//                             backgroundPosition: ["200% 0", "-200% 0"],
//                           }}
//                           transition={{
//                             duration: 3,
//                             ease: "linear",
//                             repeat: Infinity,
//                           }}
//                         >
//                           {loadingMessage}
//                         </motion.p>
//                         <motion.div
//                           animate={{ x: [-4, 6] }}
//                           transition={{
//                             duration: 1,
//                             ease: easeIn,
//                             repeat: Infinity,
//                             repeatType: "loop",
//                           }}
//                         >
//                           <DownArrow className="mt-[0.32rem] w-4 h-4 -rotate-90" />
//                         </motion.div>
//                       </motion.div>
//                     ) : (
//                       <div className="w-max min-w-40 max-w-full  switzer-500 py-2 px-3 rounded-md bg-white shadow-md">
//                         <ReactMarkdown
//                           remarkPlugins={[remarkGfm]}
//                           rehypePlugins={[rehypeRaw]}
//                         >
//                           {message.content}
//                         </ReactMarkdown>
//                       </div>
//                     )}
//                   </AnimatePresence>
//                 </div>
//               )
//             )}
//           </AnimatePresence>
//           <div ref={messagesEndRef}></div>
//         </div>
//         <div className="sticky bottom-0 bg-gray-50 px-4 pb-4 pt-2 w-full lg:w-2/3 input-box">
//           <div
//             className="flex flex-col relative border border-black/10 px-3 py-2 rounded-lg h-40 shadow-md
//         "
//           >
//             <div
//               ref={inputRef}
//               onInput={(e) => {
//                 const target = e.target as HTMLDivElement;
//                 const text = target.textContent.trim() ?? "";
//                 setShowInputButton(text !== "");
//               }}
//               onKeyDown={(e) => {
//                 handleInput(e);
//               }}
//               contentEditable
//               className="h-2/3 switzer-500 focus:outline-none overflow-y-auto"
//             ></div>
//             {!showInputButton && (
//               <span
//                 className={`absolute top-2 pointer-events-none placeholder-input-box switzer-500 text-black`}
//               >
//                 {placeholder}
//               </span>
//             )}
//             <OptionsProvider wsRef={wsRef}>
//               <BottomOptions />
//               <ExtraOptions />
//               <ModelBox modelList={ModelList} />
//             </OptionsProvider>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

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

      // STREAMING: agent-event streaming shape + token streaming
      const streamEvent = data.stream_event ?? data.type;

      switch (streamEvent) {
        case "token": {
          // STREAMING: append token delta to last assistant placeholder
          const delta = data.delta ?? "";
          setMessages((prev) => {
            const updated = [...(prev || [])];
            // Append to the last assistant placeholder (the last assistant message which may be empty or in-progress)
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
              // If placeholder exists (maybe empty), append token
              updated[lastIdx].content = (updated[lastIdx].content || "") + delta;
            } else {
              // Otherwise, push a new assistant message (stream started late)
              updated.push({ role: "assistant", content: delta });
            }
            return updated;
          });
          break;
        }

        case "message_output": {
          // Final/authoritative message from agent: replace last assistant placeholder with final text
          const text = data.text ?? "";
          setMessages((prev) => {
            const updated = [...(prev || [])];
            // find last assistant placeholder (assistant with content that likely contains partial tokens)
            const lastIdx = updated.findLastIndex((m) => m.role === "assistant");
            if (lastIdx !== -1) {
              updated[lastIdx].content = text;
            } else {
              updated.push({ role: "assistant", content: text });
            }
            return updated;
          });

          // mark loading false only when final message arrives (run_complete also does this)
          setLoading(false);
          setLoadingMessage(null);
          break;
        }

        case "tool_called": {
          // show a small assistant/system notification about tool run
          const tool = data.tool_name ?? "tool";
          const input = data.tool_input ?? "";
          setMessages((prev) => [
            ...(prev ?? []),
            {
              role: "assistant",
              content: `🔧 Tool called: ${tool}${input ? " — input: " + String(input) : ""}`,
            },
          ]);
          break;
        }

        case "tool_output": {
          const tool = data.tool_name ?? "tool";
          const output = typeof data.output === "string" ? data.output : JSON.stringify(data.output, null, 2);
          setMessages((prev) => [
            ...(prev ?? []),
            {
              role: "assistant",
              content: `🧾 Tool output (${tool}):\n\n${output}`,
            },
          ]);
          break;
        }

        case "agent_updated": {
          const name = data.new_agent_name ?? "unknown";
          // Only display handoff if it's a real change (backend already filters same-name handoffs)
          setMessages((prev) => [
            ...(prev ?? []),
            { role: "assistant", content: `➡️ Handoff to agent: ${name}` },
          ]);
          break;
        }

        case "run_item": {
          // Generic event — optionally ignore or display
          setMessages((prev) => [
            ...(prev ?? []),
            { role: "assistant", content: `[progress] ${data.item_type ?? "item"} ` },
          ]);
          break;
        }

        case "run_complete": {
          setLoading(false);
          setLoadingMessage(null);
          break;
        }

        case "loading_message": {
          const message = data.content ?? "Thinking...";

          // show the latest loading text
          setLoadingMessage(message);

          // if this chunk is marked as final → store it in chat history
          if (data.final) {
            setMessages((prev) => {
              const updated = [...(prev || [])];
              const lastIdx = updated.findLastIndex((m) => m.role === "assistant");
              if (lastIdx !== -1) {
                updated[lastIdx].content = message;   // replace placeholder
              } else {
                updated.push({ role: "assistant", content: message });
              }
              return updated;
            });
            setLoading(false);
            setLoadingMessage(null);
          }
          break;
        }

        case "agent":
          // preserve original agent switching shape (kept for backwards compatibility)
          console.log("✅ Agent switched:", data);
          alert(data.message || "Agent switched successfully!");
          break;
        
        case "final_output": {
          const text = data.content ?? "";

          setMessages((prev) => {
            const updated = [...(prev || [])];
            const lastIdx = updated.findLastIndex((m) => m.role === "assistant");

            if (lastIdx !== -1) {
              updated[lastIdx].content = text;
            } else {
              updated.push({ role: "assistant", content: text });
            }

            return updated;
          });

          setLoading(false);
          setLoadingMessage(null);
          break;
        }

        default:
          console.log("Unhandled stream event:", data);
          break;
      }
    };
  }, []);

  const ask = async (input: string) => {
    setError(null);

    // STREAMING: push a placeholder assistant message that token streaming will update
    setMessages((prev) => [
      ...(prev || []),
      { role: "user", content: input },
      { role: "assistant", content: "" }, // placeholder for streaming tokens/message_output
    ]);
    setLoading(true);
    setLoadingMessage(null);

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
      setLoading(false);
      setLoadingMessage(null);
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
