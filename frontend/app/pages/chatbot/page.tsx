"use client";

import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { ReactNode, useEffect, useRef, useState } from "react";
import ChatProvider from "@/app/providers/chatbot/ChatProvider";
import AttachIcon from "../../../icons/attach_icon.svg";
import DisclaimerIcon from "../../../icons/disclaimer.svg";
import UndoArrow from "../../../icons/refresh.svg";
import DownArrow from ".../icons/arrow-down-head.svg";
import SimpleAudioDialog from "../../components/chatbot/UI/AudioDialogBox";
import { AssistantMessage } from "@/app/components/chatbot/interfaces/ChatMessage";
import {
  motion,
  easeInOut,
  easeIn,
  AnimatePresence,
  useAnimationControls,
} from "framer-motion";
import ProtectedRoute from "@/app/utils/ProtectedRoutes";
import RegistrationForm, {
  RegistrationData,
} from "@/app/components/chatbot/UI/ReactForm";
import { audioScheduler } from "../../utils/AudioScheduler";
import { ModelList } from "@/static/data";
import BottomOptions from "../../components/chatbot/UI/BottomOptions";
import ExtraOptions from "../../components/chatbot/UI/ExtraOptions";
import PromptSuggestion from ".../icons/prompt_suggestion.svg";
import { defaultPrompts } from "@/static/data";
import ModelBox from "../../components/chatbot/UI/ModelBox";
import Controls from "../../components/chatbot/UI/Controls";
import PromptExtraOptions from "../../components/chatbot/UI/PrompExtraOptions";
import generateUUID from "@/utils/generateShortId";
import { generateNewSessionId } from "@/app/session/session";
import { ChatHisoryDialoguseBox } from "../../components/chatbot/UI/ChatHistoryDialogueBox";
import { ChatRecord } from "@/app/context/chatbot/ChatContext";
import { PromptExtraOptionsContext } from "@/app/context/chatbot/PromptExtraOptionsContext";
import ReportContentDialogueBox from "../../components/chatbot/UI/ReportContentDialogueBox";
import { ChatMessage } from "../../components/chatbot/interfaces/ChatMessage";
import QuranAudioDialog from "../../components/chatbot/UI/AudioDialogBox";
import QuranVerseDialog from "../../components/chatbot/UI/QuranVerseDialog";
import groupChatMessages from "@/utils/groupChatMessages";
import WaveForm from "../../components/chatbot/UI/WaveForm";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const inputRef = useRef<HTMLDivElement | null>(null);
  const [showPlaceholder, setShowPlaceholder] = useState<boolean | null>(true);
  const [isRecording, setIsRecording] = useState(false);
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
  const [messageIDs, setMessageIDs] = useState<(string | null)[] | null>(null);

  const [showAudioDialog, setShowAudioDialog] = useState(false);
  const [audioRequest, setAudioRequest] = useState<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [showQuranVerseDialog, setShowQuranVerseDialog] = useState(false);
  const [verseRequest, setVerseRequest] = useState<any>(null);

  const [showQuranPlayer, setShowQuranPlayer] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatRecord[] | null>(null);
  const messageScrollFlag = useRef<boolean | null>(false);
  const committedTextRef = useRef<string>("");
  const tempSpeechRef = useRef<string>("");

  const [hideReportContentDialogueBox, setHideReportContentDialogueBox] =
    useState<boolean | null>(true);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);

  const currentMessageIDRef = useRef<string | null>(null);
  const [reportedMessageIDs, setReportedMessageIDs] = useState<string[] | null>(
    []
  );
  const [userData, setUserData] = useState<RegistrationData | null>(null);

  const oldMessagesRef = useRef<AssistantMessage[]>([]);
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
  // In your element
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
      setReportedMessageIDs([]);
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
        case "open_audio_dialog":
          // This is triggered when user asks to listen to Quran
          setAudioRequest({
            parsed_request: data.parsed_request,
            original_message: data.original_message,
            available_reciters: data.available_reciters,
            note: data.note || null,
          });
          setShowAudioDialog(true);
          break;

        case "open_verse_dialog":
          setVerseRequest({
            parsed_request: data.parsed_request,
            original_message: data.original_message,
            note: data.note || null,
          });
          setShowQuranVerseDialog(true);
          break;

        case "undo-report":
          const id = data.message_id;
          if (id) {
            setReportedMessageIDs((prev) => {
              if (!prev) return prev;
              return prev.filter((i) => i !== id);
            });
          }
          break;

        case "tts_audio_chunk":
          const audioBase64 = data.audio;
          const audio_url = data.audio_url;
          if (audio_url && audioRef.current) {
            audioRef.current.src = audio_url;
            audioRef.current?.play();
          }
          // if (audioBase64) {
          //   audioScheduler.scheduleChunk(audioBase64);
          // }
          break;

        case "session_id":
          const session_id = data.session_id;
          const isNew = session_id != sessionID;
          const session_status = data.status;
          const message_ids = data.message_ids;
          if (isNew && session_status === "acknowledged") {
            setSessionID(session_id);
            // Use functional update to ensure we're working with latest state
            setMessages((prevMessages) => {
              if (prevMessages && prevMessages.length > 0) {
                return [];
              }
              return prevMessages; // Return unchanged if no messages
            });
            setMessageIDs(message_ids);
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
          // handle chat history
          if (history_status === "acknowledged") {
            setChatHistory(chat_history);
          }
          break;

        case "get_chat":
          const status = data.status;
          if (status === "acknowledged") {
            const messageIDs = data.unique_message_ids;
            const chat_history = groupChatMessages(data.chat_history);
            setMessages(chat_history || []);
            setMessageIDs(messageIDs);
          }
          break;

        case "assistance_response":
          const reply: string = data.content ?? "No reply from server";
          const message_id: string = data.message_id;
          // assign reply to message ID with order data.reply_to_message_id >> currentMessageIDRef.current >> null
          const reply_to_message_id =
            data.reply_to_message_id || currentMessageIDRef.current || null;
          const resend_flag = data.resend_flag;

          console.log("Current old messages", oldMessagesRef.current);

          // check if oldMessages is present with resend flag
          if (resend_flag) {
            if (
              !oldMessagesRef.current ||
              oldMessagesRef.current.length === 0
            ) {
              console.log("No old messages so returning...");
              break;
            }
          }

          messageScrollFlag.current = false;
          setLoadingMessage(null);

          // Add a new assistant message
          setMessages((prev) => {
            if (!prev || prev.length == 0) {
              return prev;
            }
            const updated = [...(prev || [])];

            // although streamingMessageIndex is already set in ask function, but setting again for safety
            setStreamingMessageIndex(updated.length - 1);
            const lastUserMessage = updated.findLast((m) => m.role === "user");

            if (lastUserMessage) {
              if (!lastUserMessage.number_of_responses) {
                lastUserMessage.number_of_responses = 1;
              } else {
                lastUserMessage.number_of_responses += 1;
              }

              // initialize a new responses array if resend flag is false otherwise assign to oldMessages

              lastUserMessage.responses = resend_flag
                ? oldMessagesRef.current
                : [];

              // assign message_id and reply_to_message_id this time
              lastUserMessage.responses.push({
                role: "assistant",
                message_id: message_id,
                content: "",
                reply_to_message_id: reply_to_message_id,
                feedback: null,
              });

              // set the number of active message index
              lastUserMessage.active_message_index =
                lastUserMessage.number_of_responses - 1;
            }

            return updated;
          });

          setLoading(false);
          setLoadingMessage(null);
          const chunk_array = chunkText(reply, 4); // 4 words per chunk
          (async () => {
            for (const chunk of chunk_array) {
              // smaller delay → faster
              await new Promise((resolve) => setTimeout(resolve, 2));

              setMessages((prev) => {
                if (!prev || prev.length === 0) {
                  return prev;
                }
                const updated = [...(prev || [])];
                const streamIndex = streamingMessageIndex ?? updated.length - 1;
                if (streamIndex >= 0 && streamIndex < updated.length) {
                  let lastAssistantMessageIdx = 0;
                  if (updated[streamIndex].number_of_responses) {
                    lastAssistantMessageIdx =
                      updated[streamIndex].number_of_responses - 1;
                  }

                  updated[streamIndex].responses[
                    lastAssistantMessageIdx
                  ].content =
                    (updated[streamIndex].responses[lastAssistantMessageIdx]
                      .content || "") +
                    " " +
                    chunk;
                } else {
                  // will have to review the logic here
                  // maybe the fallback logic here is dead/unused each time
                  const lastUserMessage = updated.findLast(
                    (m) => m.role === "user"
                  );

                  if (lastUserMessage) {
                    lastUserMessage.number_of_responses = 1;
                    lastUserMessage.responses.push({
                      message_id: message_id,
                      role: "assistant",
                      reply_to_message_id: reply_to_message_id,
                      content: chunk,
                      feedback: null,
                    });
                  }
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
              setMessages([]);
              setGreeting(
                "Generate any Islamic story with the finest AI Models."
              );
              break;
            case "tafseer":
              setPlaceholder("Let's lean about the Quran");
              setMessages([]);
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
        case "report":
          const report_status = data.status;
          if (report_status !== "acknowledged") {
            break;
          }
          const reported_message_id = data.message_id;
          if (reported_message_id) {
            setReportedMessageIDs((prev) => [
              ...(prev ?? []),
              reported_message_id,
            ]);
          }

          break;
        // case "streaming_end":
        //   audioScheduler.flush();
        //   break;

        default:
          break;
      }
    };
  }, []);

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
          feedback: null,
        },
      ]);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to upload file.");
    }
  };

  const ask = async (
    input: string,
    guidelines: string | null = null,
    resend_flag: boolean = false,
    resend_message_id: string | null = null,
    old_assistant_responses = []
  ) => {
    if (streamingMessageIndex !== null || !input.trim()) return;

    if (resend_flag) {
      if (!old_assistant_responses || old_assistant_responses.length === 0) {
        console.log("No old assistant responses, continuing....");
        return;
      }
    }
    setError(null);
    messageScrollFlag.current = false;
    setLoading(true);
    let messageID: string | null = null;

    if (!resend_flag) {
      // generate a message ID for the user message if its not a resend message
      messageID = generateUUID();
      while (messageIDs?.includes(messageID)) {
        messageID = generateUUID(); // Reassign the same variable
      }
      setMessageIDs((prev) => {
        return [...(prev || []), messageID];
      });
    } else {
      messageID = resend_message_id;
    }

    if (!messageID) {
      console.log("No message ID so returning");
      return;
    }

    const userMessage: ChatMessage = {
      message_id: messageID,
      role: "user",
      content: input,
      // add a dummy response message for loading state
      responses: [
        {
          role: "assistant",
          message_id: "",
          reply_to_message_id: "",
          content: "",
          feedback: null,
        },
      ],
      number_of_responses: resend_flag ? old_assistant_responses.length : 0,
      active_message_index: 0,
    };
    oldMessagesRef.current = resend_flag ? old_assistant_responses : [];

    // lastUserMessage.responses.push({
    //   role: "assistant",
    //   message_id: message_id,
    //   content: "",
    //   reply_to_message_id: reply_to_message_id,
    //   feedback: null,
    // });

    // // set the number of active message index
    // lastUserMessage.active_message_index =
    //   lastUserMessage.number_of_responses - 1;

    setMessages((prev) => {
      // prev is already typed correctly from useState
      const updated = [...(prev || []), userMessage];
      // Set the streaming index to the upcoming new message
      setStreamingMessageIndex(updated.length - 1);
      return updated;
    });

    currentMessageIDRef.current = messageID;
    try {
      wsRef.current?.send(
        JSON.stringify({
          type: "user_message",
          message_id: messageID,
          role: "user",
          system_instructions: guidelines || "",
          content: input,
          resend_flag: resend_flag,
          resend_message_id: resend_message_id || "",
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

  const handleInput = async (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!inputRef.current) return;

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      // Handle File Upload
      if (attachedFile) {
        await uploadFile(attachedFile);
        setAttachedFile(null); // Clear the file after sending
      }

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
    parent_index: number | null;
    assistant_index: number | null;
    message_id: string | null;
    reply_to_message_id: string | null;
  }

  const PromptExtraOptionsProvider: React.FC<
    PromptExtraOptionsProviderProps
  > = ({
    children,
    message_id,
    reply_to_message_id,
    parent_index,
    assistant_index,
  }) => {
    const [hidePromptExtraOptionsModelBox, setHidePromptExtraOptionsModelBox] =
      useState<boolean | null>(true);

    const [hideResendPromptDialogue, setHideResendPromptDialogue] = useState<
      boolean | null
    >(true);
    const [activeMessageIndex, setActiveMessageIndex] = useState<number | null>(
      0
    );
    return (
      <PromptExtraOptionsContext.Provider
        value={{
          parent_index,
          assistant_index,
          messages,
          setMessages,
          message_id,
          reply_to_message_id,
          hidePromptExtraOptionsModelBox,
          setHidePromptExtraOptionsModelBox,
          hideReportContentDialogueBox,
          setHideReportContentDialogueBox,
          sessionID,
          wsRef,
          ask,
          hideResendPromptDialogue,
          setHideResendPromptDialogue,
          activeMessageIndex,
          setActiveMessageIndex,
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
              setGreeting(
                `Assalamu Alaykum ${data.username}! 🌟 I am Tadabbur, your friend!`
              );
              setPlaceholder("Tell me a about prophets...");
            } else {
              setGreeting(
                `Assalamu Alaykum ${data.username}, I am Tadabbur. How may I assist you with your Quranic studies?`
              );
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
                  {messages?.length === 0 && (
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
                                            {/* <PromptSuggestion className="w-5 h-5 fill-current text-green-700" /> */}
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
                  {/* first render user messages */}
                  {messages?.map((record, record_index) => {
                    return (
                      <div key={record_index}>
                        <div>
                          <p className="ml-auto w-max min-w-40 max-w-[20rem] bg-neutral-900 text-white switzer-500 py-2 px-3 rounded-md shadow-md border border-black/5">
                            {record.content}
                          </p>
                        </div>
                        <div>
                          <PromptExtraOptionsProvider
                            message_id={record.message_id}
                            reply_to_message_id={null}
                            parent_index={record_index}
                            assistant_index={null}
                          >
                            <PromptExtraOptions messageType={"user"} />
                          </PromptExtraOptionsProvider>
                        </div>
                        {record?.responses?.map((ai_msg, ai_msg_idx) => {
                          // loading circle logic here
                          return loading &&
                            !loadingMessage &&
                            !ai_msg.content ? (
                            <motion.div
                              key={ai_msg_idx}
                              animate={{ scale: [1, 1.2, 1] }}
                              transition={{
                                duration: 0.4,
                                ease: easeInOut,
                                repeat: Infinity,
                                repeatType: "loop",
                              }}
                              className="w-3 h-3 rounded-full bg-black"
                            ></motion.div>
                          ) : reportedMessageIDs &&
                            !reportedMessageIDs.includes(ai_msg?.message_id) &&
                            ai_msg_idx === record.active_message_index ? (
                            <div key={ai_msg_idx}>
                              <div className="w-max min-w-40 max-w-full switzer-500 mt-2 py-2 px-3 rounded-md bg-white shadow-md">
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  rehypePlugins={[rehypeRaw]}
                                  components={{
                                    // HEADERS
                                    h1: ({ node, ...props }) => (
                                      <h1
                                        className="text-3xl font-bold"
                                        {...props}
                                      />
                                    ),
                                    h2: ({ node, ...props }) => (
                                      <h2
                                        className="text-2xl font-semibold"
                                        {...props}
                                      />
                                    ),
                                    h3: ({ node, ...props }) => (
                                      <h3
                                        className="text-xl font-semibold"
                                        {...props}
                                      />
                                    ),

                                    // PARAGRAPH
                                    p: ({ node, ...props }) => (
                                      <p
                                        className="leading-7 my-2 text-gray-800"
                                        {...props}
                                      />
                                    ),

                                    // STRONG ( **bold** )
                                    strong: ({ node, ...props }) => (
                                      <strong
                                        className="font-bold text-black"
                                        {...props}
                                      />
                                    ),

                                    // EMPHASIS ( *italic* )
                                    em: ({ node, ...props }) => (
                                      <em
                                        className="italic text-gray-700"
                                        {...props}
                                      />
                                    ),

                                    // LINE BREAK
                                    br: ({ node, ...props }) => <br />,

                                    // LINKS
                                    a: ({ node, ...props }) => (
                                      <a
                                        className="text-blue-600 underline"
                                        target="_blank"
                                        rel="noreferrer"
                                        {...props}
                                      />
                                    ),

                                    // LISTS
                                    ul: ({ node, ...props }) => (
                                      <ul
                                        className="list-disc pl-6"
                                        {...props}
                                      />
                                    ),
                                    ol: ({ node, ...props }) => (
                                      <ol
                                        className="list-decimal pl-6"
                                        {...props}
                                      />
                                    ),
                                    li: ({ node, ...props }) => (
                                      <li className="my-1" {...props} />
                                    ),
                                    blockquote: ({ node, ...props }) => (
                                      <blockquote
                                        className="border-l-4 border-gray-400 pl-4 italic my-3"
                                        {...props}
                                      />
                                    ),

                                    // HORIZONTAL RULE
                                    hr: () => (
                                      <hr className="my-4 border-gray-300" />
                                    ),

                                    // IMAGES
                                    img: ({ node, ...props }) => (
                                      <img
                                        className="rounded-md my-2"
                                        alt=""
                                        {...props}
                                      />
                                    ),
                                  }}
                                >
                                  {ai_msg.content}
                                </ReactMarkdown>
                              </div>
                              {/* Place it here, inside the div */}
                              {streamingMessageIndex != record_index &&
                                reportedMessageIDs &&
                                !reportedMessageIDs.includes(
                                  ai_msg?.message_id
                                ) && (
                                  <div>
                                    <PromptExtraOptionsProvider
                                      message_id={ai_msg?.message_id}
                                      reply_to_message_id={
                                        ai_msg?.reply_to_message_id
                                      }
                                      parent_index={record_index}
                                      assistant_index={ai_msg_idx}
                                    >
                                      <PromptExtraOptions
                                        messageType={"assistant"}
                                      />
                                    </PromptExtraOptionsProvider>
                                  </div>
                                )}
                            </div>
                          ) : reportedMessageIDs &&
                            reportedMessageIDs.includes(ai_msg?.message_id) ? (
                            // reportedmessage component here
                            <div
                              key={ai_msg_idx}
                              className="flex flex-col gap-y-1.5 w-[90%] max-w-120 "
                            >
                              <div className="h-max rounded-md shadow-md min-h-25 border border-red-200/10 px-2 pt-2 pb-3">
                                <div className="mb-0.5 w-full flex justify-between">
                                  <p
                                    id="report-title"
                                    className="text-red-800 switzer-500 text-[1.1rem] tracking-[-0.04rem]"
                                  >
                                    This response is reported
                                  </p>
                                  <DisclaimerIcon className="w-5 h-5 fill-current text-red-700/90" />
                                </div>

                                <p
                                  id="report-description"
                                  className="switzer-500 text-black/60 tracking-tight"
                                >
                                  This response promotes violence or self-harm
                                  and goes against our community policies.
                                </p>
                              </div>
                              <div className="flex items-center gap-x-2 px-1">
                                <div id="learn-more-box" className="ml-auto">
                                  <p className="inter-500 text-[0.9rem] text-red-700/80 cursor-pointer hover:text-red-700 tracking-tight">
                                    Learn More about guidelines
                                  </p>
                                </div>
                                <div className="ml-1 w-[0.5px] h-3.5 bg-black/40"></div>
                                <div
                                  onClick={() => {
                                    wsRef?.current?.send(
                                      JSON.stringify({
                                        type: "undo-report",
                                        message_id: ai_msg.message_id,
                                      })
                                    );
                                  }}
                                  id="undo-report-box"
                                  className="undo-report-box flex justify-center items-center gap-x-2 flex-row-reverse px-2 py-1 hover:bg-black/5 rounded-md cursor-pointer"
                                >
                                  <p className="switzer-500 text-[0.9rem]">
                                    Undo
                                  </p>
                                  <UndoArrow className="w-3.5 h-3.5" />
                                </div>
                              </div>
                            </div>
                          ) : null;
                        })}
                      </div>
                    );
                  })}
                </AnimatePresence>

                <div ref={messagesEndRef}></div>
              </div>
            </div>
            <div className="mr-1.5 bg-gray-50 px-4 mt-4 py-4 w-full lg:w-2/3 input-box">
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

            <ReportContentDialogueBox
              hideReportContentDialogueBox={hideReportContentDialogueBox}
              setHideReportContentDialogueBox={setHideReportContentDialogueBox}
            />
            <audio controls ref={audioRef} />
          </ChatProvider>
        </div>
      )}
    </ProtectedRoute>
  );
}
