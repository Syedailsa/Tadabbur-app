"use client";

import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { ReactNode, useContext, useEffect, useRef, useState } from "react";
import ChatProvider from "../../providers/chatbot/ChatProvider";
import { useRouter } from "next/navigation";
import DownArrow from "../../../icons/arrow-down-head.svg";
import RegistrationForm, { RegistrationData } from "./../../components/chatbot/UI/ReactForm"; 
import ProtectedRoute from "@/app/utils/ProtectedRoutes";
import AttachIcon from "@/icons/attach_icon.svg";
import {
  motion,
  easeInOut,
  easeIn,
  AnimatePresence,
  useAnimationControls,
} from "framer-motion";
import { ModelList } from "@/static/data";
import BottomOptions from "./../../components/chatbot/UI/BottomOptions";
import ExtraOptions from "./../../components/chatbot/UI/ExtraOptions";
import PromptSuggestion from "../../../icons/prompt_suggestion.svg";
import { defaultPrompts } from "@/static/data";
import ModelBox from "./../../components/chatbot/UI/ModelBox";
import Controls from "./../../components/chatbot/UI/Controls";
import PromptExtraOptions from "./../../components/chatbot/UI/PrompExtraOptions";
import { audioScheduler } from "./../../utils/AudioScheduler";

import { generateNewSessionId } from "./../../session/session";
import { ChatHisoryDialoguseBox } from "./../../components/chatbot/UI/ChatHistoryDialogueBox";
import QuranAudioDialog from "./../../components/chatbot/UI/AudioDialogBox";
import QuranVerseDialog from "@/app/components/chatbot/UI/QuranVerseDialog";
import { ChatRecord } from "./../../context/chatbot/ChatContext";
import { PromptExtraOptionsContext } from "./../../context/chatbot/PromptExtraOptionsContext";
import WaveForm from "@/app/components/chatbot/UI/WaveForm";

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<
    | {
        message_id: string;
        role: "user" | "assistant";
        content: string;
        feedback: "liked" | "disliked" | "reported" | null;
      }[]
    | null
  >(null);
  const committedTextRef = useRef<string>(""); 
  const tempSpeechRef = useRef<string>(""); 

  const [userData, setUserData] = useState<RegistrationData | null>(null);
  const [isRecording, setIsRecording] = useState(false);
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

  const [messageIDs, setMessageIDs] = useState<string[] | null>(null);
  const [showAudioDialog, setShowAudioDialog] = useState(false);
  const [audioRequest, setAudioRequest] = useState<any>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);

  const [showQuranVerseDialog, setShowQuranVerseDialog] = useState(false);
  const [verseRequest, setVerseRequest] = useState<any>(null);

  const [showQuranPlayer, setShowQuranPlayer] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatRecord[] | null>(null);
  const messageScrollFlag = useRef<boolean | null>(false);
  const controls = useAnimationControls();

  interface TableData {
    headers: string[];
    rows: string[][];
  }

  interface ContentSection {
    heading: string;
    body: string;
    bullet_points?: string[];
    table?: TableData;
  }

  interface QuranResponse {
    title: string;
    intro: string;
    sections: ContentSection[];
    references?: string[];
  }

//   useEffect(() => {
//     const storedUser = localStorage.getItem('user');
//     if (storedUser && !userData) {
//         try {
//             const parsed = JSON.parse(storedUser);
//             setUserData({
//                 username: parsed.name || "User",
//                 age: 20, 
//             } as RegistrationData);
//         } catch (e) {
//             console.error("Failed to parse stored user", e);
//         }
//     }
//   }, []);

  useEffect(() => {
    const handleMicStart = () => {
        setIsRecording(true);
        tempSpeechRef.current = ""; 
    };

    const handleMicStop = () => {
        setIsRecording(false);
    };

    const handleSTTResult = (e: Event) => {
        const customEvent = e as CustomEvent;
        const text = customEvent.detail;
        
        if (inputRef.current && text) {
            const currentText = inputRef.current.innerText.trim();
            const newText = currentText ? `${currentText} ${text}` : text;
            
            inputRef.current.innerText = newText;
            committedTextRef.current = newText;

            const range = document.createRange();
            const sel = window.getSelection();
            if(inputRef.current.lastChild) {
                 range.selectNodeContents(inputRef.current);
                 range.collapse(false);
                 sel?.removeAllRanges();
                 sel?.addRange(range);
            }
            setShowPlaceholder(false);
        }
    };

    window.addEventListener("tadabbur-mic-start", handleMicStart);
    window.addEventListener("tadabbur-mic-stop", handleMicStop);
    window.addEventListener("tadabbur-stt-result", handleSTTResult);

    return () => {
        window.removeEventListener("tadabbur-mic-start", handleMicStart);
        window.removeEventListener("tadabbur-mic-stop", handleMicStop);
        window.removeEventListener("tadabbur-stt-result", handleSTTResult);
    };
  }, []);

  const StructuredResponse = ({ data }: { data: QuranResponse }) => {
    return (
      <div className="space-y-6 text-black/90 switzer-500 w-full">
        <div className="border-b pb-4 mb-4">
          <h1 className="text-3xl font-bold text-black/90 mb-3">{data.title}</h1>
          <p className="text-lg leading-relaxed">{data.intro}</p>
        </div>

        {data.sections.map((section, idx) => (
          <div key={idx} className="bg-white/50 rounded-lg p-1">
            <h3 className="text-xl font-bold text-black/90 mb-2">{section.heading}</h3>
            
            <p className="mb-4 whitespace-pre-wrap leading-relaxed">{section.body}</p>

            {section.bullet_points && section.bullet_points.length > 0 && (
              <ul className="list-disc list-inside mb-4 p-3 ">
                {section.bullet_points.map((point, i) => (
                  <li key={i} className="mb-1">{point}</li>
                ))}
              </ul>
            )}

            {section.table && (
              <div className="overflow-x-auto my-4 border rounded-lg shadow-sm">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="text-white">
                    <tr>
                      {section.table.headers.map((header, hIdx) => (
                        <th key={hIdx} className="px-4 py-3 text-left text-sm font-semibold uppercase tracking-wider">
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {section.table.rows.map((row, rIdx) => (
                      <tr key={rIdx} className={rIdx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-4 py-3 text-sm text-gray-700 whitespace-pre-wrap">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}

        {data.references && (
          <div className="mt-8 pt-4 border-t border-gray-300 text-sm text-gray-500">
            <span className="font-bold">References:</span> {data.references.join(", ")}
          </div>
        )}
      </div>
    );
  };

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");

    router.push("/pages/auth");
  };


  function preprocessContent(content: string) {
    if (!content) return "";

    let processed = content;

    processed = processed.replace(/\\n/g, '\n');

    return processed;
  }


  function chunkText(text: string, size = 4) {
    const words = text.split(/\s+/);
    const chunks = [];

    for (let i = 0; i < words.length; i += size) {
      chunks.push(words.slice(i, i + size).join(" "));
    }
    return chunks;
  }

  const generateShortId = (): string =>
    Math.random().toString(36).substring(2, 8);

  useEffect(() => {
    // Only connect if we have user data
    if (!userData) return;

    const socket = new WebSocket("ws://localhost:8000/ws/chat");
    wsRef.current = socket;

    socket.onopen = () => {
      console.log("Connected to websocket successfully!");
      const session_id = generateNewSessionId();
      
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(
          JSON.stringify({
            type: "session-init",
            session_id: session_id,
            model: "kimi-k2-instruct-0905",
            user_data: {
              username: userData.username,
              age: userData.age 
            }
          })
        );
      }
    };

    socket.onerror = (error) => {
      console.error("An error occured in websocket", error);
    };

    socket.onclose = () => {
      console.log("Websocket closed!");
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Data from websocket", event.data);

      const type = data.type;
      switch (type) {
        case "open_audio_dialog":
          setAudioRequest({
            parsed_request: data.parsed_request,
            original_message: data.original_message,
            available_reciters: data.available_reciters,
            note: data.note || null,
          });
          setShowAudioDialog(true);
          break;

        case "tts_audio_chunk":
          const audioBase64 = data.audio;
          if (audioBase64) {
             audioScheduler.scheduleChunk(audioBase64);
          }
          break;

        case "open_verse_dialog":
          setVerseRequest({
            parsed_request: data.parsed_request,
            original_message: data.original_message,
            note: data.note || null,
          });
          setShowQuranVerseDialog(true);
          break;

        case "audio_response":
          break;

        case "session_id":
          const session_id = data.session_id;
          const isNew = session_id != sessionID;
          if (isNew) {
            setSessionID(session_id);
            setMessages((prevMessages) => {
              if (prevMessages && prevMessages.length > 0) {
                return null;
              }
              return prevMessages; 
            });
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
          const history_status = data.status;
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
          const message_id: string = data.message_id;
          setLoadingMessage(null);

          messageScrollFlag.current = false;
          setMessages((prev) => {
            const updated = [...(prev || [])];

            updated.push({
              message_id: message_id,
              role: "assistant",
              content: "", 
              feedback: null,
            });

            setStreamingMessageIndex(updated.length - 1);
            return updated;
          });

          setLoading(false);

          const chunk_array = chunkText(reply, 4); 
          (async () => {
            for (const chunk of chunk_array) {
              await new Promise((resolve) => setTimeout(resolve, 2));

              setMessages((prev) => {
                const updated = [...(prev || [])];
                const streamIndex = streamingMessageIndex ?? updated.length - 1;
                if (streamIndex >= 0 && streamIndex < updated.length) {
                  updated[streamIndex].content =
                    (updated[streamIndex].content || "") + " " + chunk;
                } else {
                  updated.push({
                    message_id: message_id,
                    role: "assistant",
                    content: chunk,
                    feedback: null,
                  });
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

        case "streaming_end":
             audioScheduler.flush(); 
             break;

        default:
          break;
      }
    };

    return () => {
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close();
      }
    }
  }, [userData]);

  const ask = async (input: string) => {
    if (streamingMessageIndex !== null) return;
    committedTextRef.current = "";
    tempSpeechRef.current = "";
    if (inputRef.current) inputRef.current.innerText = ""; 
    setError(null);
    messageScrollFlag.current = false;
    setLoading(true);
    // generate a message ID for the user message
    let messageID = generateShortId();
    while (messageIDs?.includes(messageID)) {
      messageID = generateShortId();
    }
    setMessageIDs((prev) => {
      return [...(prev || []), messageID];
    });

    setMessages((prev: any) => {
      const updated = [
        ...(prev || []),
        { message_id: messageID, role: "user", content: input, feedback: null },
      ];
      return updated;
    });

    try {
      wsRef.current?.send(
        JSON.stringify({
          type: "user_message",
          message_id: messageID,
          role: "user",
          content: input,
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

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionID || "default_session"); 

    try {
        const response = await fetch("http://localhost:8000/api/upload", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json();
          alert(`Upload failed: ${err.detail}`);
          return;
        }

        const data = await response.json();
        
        // Add the file message to the chat UI immediately
        setMessages((prev: any) => [
          ...(prev || []),
          {
            message_id: data.message_id, 
            role: "user",
            content: `📂 Attached file: ${file.name}`,
            feedback: null
          }
        ]);
        
    } catch (error) {
        console.error("Upload error:", error);
        alert("Failed to upload file.");
    }
  };

  const handleInput = async (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!inputRef.current) return;
    
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      
      // Handle File Upload
      if (attachedFile) {
        await uploadFile(attachedFile);
        setAttachedFile(null); // Clear the file after sending
      }

      // Handle Text Message
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
    message_id: string | null;
  }
  const PromptExtraOptionsProvider: React.FC<
    PromptExtraOptionsProviderProps
  > = ({ children, index, message_id }) => {
    const [hidePromptExtraOptionsModelBox, setHidePromptExtraOptionsModelBox] =
      useState<boolean | null>(true);

    const content = (messages && index !== null && messages[index]) 
      ? messages[index].content 
      : "";

    return (
      <PromptExtraOptionsContext.Provider
        value={{
          messages,
          setMessages,
          index,
          message_id,
          hidePromptExtraOptionsModelBox,
          setHidePromptExtraOptionsModelBox,
          sessionID,
          wsRef,
          ask,
          content,
        }}
      >
        {children}
      </PromptExtraOptionsContext.Provider>
    );
  };

  return (
    <ProtectedRoute>
    {!userData ? (
      <RegistrationForm 
          onComplete={(data) => {
              setUserData(data); 
              if (data.age <= 12) {
                  setGreeting(`Assalamu Alaykum ${data.username}! 🌟 I am Tadabbur, your friend!`);
                  setPlaceholder("Tell me about prophets...");
              } else {
                  setGreeting(`Assalamu Alaykum ${data.username}, I am Tadabbur. How may I assist you with your Quranic studies?`);
              }
          }} 
      />
    ) : (
        <div className="relative w-screen h-screen bg-gray-50 flex flex-col items-center">
            <ChatProvider
                chatHistory={chatHistory}
                setChatHistory={setChatHistory}
                wsRef={wsRef}
                sessionID={sessionID}
                attachedFile={attachedFile}
                setAttachedFile={setAttachedFile}
                messages={messages}
                setMessages={setMessages}
            >
                <ChatHisoryDialoguseBox /> 
                {showAudioDialog && audioRequest && (
                  <QuranAudioDialog
                    isOpen={showAudioDialog}
                    onClose={() => setShowAudioDialog(false)}
                    parsedRequest={audioRequest.parsed_request}
                    originalMessage={audioRequest.original_message}
                    availableReciters={audioRequest.available_reciters}
                    wsRef={wsRef}
                  />
                )}
                {showQuranVerseDialog && verseRequest && (
                  <QuranVerseDialog
                    isOpen={showQuranVerseDialog}
                    onClose={() => setShowQuranVerseDialog(false)}
                    parsedRequest={verseRequest.parsed_request}
                    originalMessage={verseRequest.original_message}
                    note={verseRequest.note}
                    wsRef={wsRef}
                  />
                )}
                <div className="w-full h-full flex flex-col items-center overflow-y-auto">
                <div className="absolute top-0 p-2 w-full">
                    <div className="pointer-events-auto">
                      <Controls wsRef={wsRef} />
                    </div>
                    <button 
                      onClick={handleLogout}
                      className="pointer-events-auto mr-2 mt-2 px-4 py-2 bg-black hover:bg-gray-800 text-white text-sm font-medium rounded-md shadow-md transition-colors"
                    >
                      Logout
                    </button>
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
                            <div>
                            <p className="ml-auto w-max min-w-40 max-w-[20rem] bg-neutral-900 text-white switzer-500 py-2 px-3 rounded-md shadow-md border border-black/5">
                                {message.content}
                            </p>
                            </div>
                            <div>
                            <PromptExtraOptionsProvider
                                message_id={message.message_id}
                                index={index}
                            >
                                <PromptExtraOptions messageType={"user"} />
                            </PromptExtraOptionsProvider>
                            </div>
                        </div>
                        ) : (
                        <div key={index} className="w-full"> 
                            {(() => {
                            let parsedData: QuranResponse | null = null;
                            try {
                                // Clean up markdown code blocks 
                                const cleanContent = message.content
                                .replace(/^```json\s*/, "") // Remove start
                                .replace(/^```\s*/, "")     // Remove start generic
                                .replace(/\s*```$/, "");    // Remove end

                                parsedData = JSON.parse(cleanContent);
                            } catch (e) {
                                parsedData = null;
                            }

                            if (parsedData && parsedData.title) {
                                return (
                                <div className="w-full max-w-[90%] bg-white shadow-md rounded-md p-4">
                                    <StructuredResponse data={parsedData} />
                                </div>
                                );
                            }

                            return (
                                <div className="w-fit min-w-40 max-w-[90%] switzer-500 py-2 px-3 rounded-md bg-white shadow-md overflow-hidden">
                                <ReactMarkdown
                                    remarkPlugins={[remarkGfm]} 
                                    rehypePlugins={[rehypeRaw]}
                                    components={{
                                    h1: ({ node, ...props }) => (
                                        <h1 className="text-2xl font-bold mt-4 mb-2 text-black" {...props} />
                                    ),
                                    h2: ({ node, ...props }) => (
                                        <h2 className="text-xl font-semibold mt-3 mb-2 text-black" {...props} />
                                    ),
                                    h3: ({ node, ...props }) => (
                                        <h3 className="text-lg font-medium mt-3 mb-1 text-black" {...props} />
                                    ),
                                    p: ({ node, ...props }) => (
                                        <p className="mb-2 leading-relaxed text-black/90 whitespace-pre-wrap" {...props} />
                                    ),
                                    ul: ({ node, ...props }) => (
                                        <ul className="list-disc list-inside mb-2 pl-2 text-black" {...props} />
                                    ),
                                    ol: ({ node, ...props }) => (
                                        <ol className="list-decimal list-inside mb-2 pl-2 text-black" {...props} />
                                    ),
                                    li: ({ node, ...props }) => (
                                        <li className="mb-1 marker:font-bold" {...props} />
                                    ),
                                    blockquote: ({ node, ...props }) => (
                                        <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...props} />
                                    ),
                                    code: ({ node, inline, className, children, ...props }: any) => {
                                        return inline ? (
                                        <code className="bg-gray-100 text-pink-600 rounded px-1 py-0.5 text-sm font-mono" {...props}>
                                            {children}
                                        </code>
                                        ) : (
                                        <div className="overflow-x-auto my-2 rounded-md bg-gray-900 p-3">
                                            <code className="block text-white text-sm font-mono" {...props}>
                                            {children}
                                            </code>
                                        </div>
                                        );
                                    },

                                    table: ({ node, ...props }) => (
                                        <div className="overflow-x-auto my-4 rounded-lg border border-gray-200">
                                        <table className="min-w-full divide-y divide-gray-200" {...props} />
                                        </div>
                                    ),
                                    thead: ({ node, ...props }) => (
                                        <thead className="bg-gray-50" {...props} />
                                    ),
                                    tbody: ({ node, ...props }) => (
                                        <tbody className="bg-white divide-y divide-gray-200" {...props} />
                                    ),
                                    tr: ({ node, ...props }) => (
                                        <tr className="even:bg-gray-50/50" {...props} />
                                    ),
                                    th: ({ node, ...props }) => (
                                        <th className="px-4 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200" {...props} />
                                    ),
                                    td: ({ node, ...props }) => (
                                        <td className="px-4 py-3 text-sm text-gray-700 whitespace-pre-wrap align-top border-b border-gray-100" {...props} />
                                    ),
                                    }}
                                >
                                    {preprocessContent(message.content)}
                                </ReactMarkdown>
                                </div>
                            );
                            })()}                    
                            {streamingMessageIndex != index && (
                            <div>
                                <PromptExtraOptionsProvider
                                message_id={message.message_id}
                                index={index}
                                >
                                <PromptExtraOptions messageType={"assistant"} />
                                </PromptExtraOptionsProvider>
                            </div>
                            )}
                        </div>
                        )
                    )}

                    {/* Loading indicators - separate from messages array */}
                    <AnimatePresence mode="wait">
                        {loading && !loadingMessage && (
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
                        )}
                        {loadingMessage && (
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
                        )}
                    </AnimatePresence>
                    </AnimatePresence>
                    <div ref={messagesEndRef}></div>
                </div>
                </div>
                <div className="mr-1.5 bg-gray-50 px-2 mt-4 py-2 w-full lg:w-2/3 input-box">

                <AnimatePresence>
                    {isRecording && (
                        <div className="absolute bottom-20 left-0 w-full px-4 z-20">
                            <WaveForm />
                        </div>
                    )}
                </AnimatePresence>

                <div
                    className="flex flex-col relative border border-black/10 px-3 py-2 rounded-lg h-40 shadow-md bg-white
                "
                >
                    {attachedFile && (
                        <div className="absolute top-2 right-2 bg-gray-100 border border-gray-200 px-3 py-3 rounded-full text-xs flex items-center gap-x-2 z-10">
                            <span className="flex font-bold text-gray-700"> 
                              <AttachIcon className="fill-current text-black w-4 h-4" /> 
                              {attachedFile.name}
                            </span>
                            <button 
                                onClick={() => setAttachedFile(null)}
                                className="text-gray-400 hover:text-red-500 font-bold px-1"
                            >
                                ✕
                            </button>
                        </div>
                    )}
                    <div
                    ref={inputRef}
                    onInput={(e) => {
                        const target = e.target as HTMLDivElement;
                        const text = target.textContent.trim() ?? "";
                        setShowPlaceholder(text === "");
                        committedTextRef.current = target.innerText;
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
    )} 
    </ProtectedRoute>  
  );
}
