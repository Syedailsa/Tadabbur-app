"use client";

import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { ReactNode, useEffect, useRef, useState, CSSProperties, HTMLAttributes, Suspense } from "react";
import Image from "next/image"
import QuranPic from "../../../images/Quran.jpg"
import QuranReading from "../../../images/QuranReading.jpg"
import DesertPic from "../../../images/Desert.jpg"
import ArkPic from "../../../images/OldArk.png"
import ChatProvider from "@/app/providers/chatbot/ChatProvider";

import DisclaimerIcon from "../../../icons/disclaimer.svg";
import CrossIcon from "../../../icons/cross_icon.svg"
import TextFileIcon from "../../../icons/text-file-icon.svg"
import PdfFileIcon from "../../../icons/pdf-file-icon.svg"
import PlusIcon from "../../../icons/plus-icon-white.svg"
import TadabburFontWhite from "../../../images/tadabbur-font-white.png"
import TadabburFontBlack from "../../../images/tadabbur-font-black.jpeg"
import SendIcon from "../../../icons/send_icon.svg"
import EngagingIcon from "../../../icons/engage_icon.svg"
import ArrowLeft from "../../../icons/arrow-left-bold.svg"
import UndoArrow from "../../../icons/refresh.svg";
import { AssistantMessage, Attachment, StoryParagraph } from "@/app/components/chatbot/interfaces/ChatMessage";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  motion,
  easeInOut,
  AnimatePresence,
  useAnimationControls,
  animate,
  useMotionValue
} from "framer-motion";
import ProtectedRoute from "@/app/utils/ProtectedRoutes";
import RegistrationForm from "@/app/components/chatbot/UI/ReactForm";
import { ModelList } from "@/static/data";
import BottomOptions from "../../components/chatbot/UI/BottomOptions";
import ExtraOptions from "../../components/chatbot/UI/ExtraOptions";
import MicStoryMode from "@/app/components/chatbot/UI/MicStoryMode";
// import PromptSuggestion from ".../icons/prompt_suggestion.svg";
import { defaultPrompts } from "@/static/data";
import ModelBox from "../../components/chatbot/UI/ModelBox";
import Controls from "../../components/chatbot/UI/Controls";
import PromptExtraOptions from "../../components/chatbot/UI/PrompExtraOptions";
import generateUUID from "@/utils/generateShortId";
import { ChatHisoryDialogueBox } from "../../components/chatbot/UI/ChatHistoryDialogueBox";
import { SurahForAudios, SurahForVerseImages } from "@/app/components/chatbot/interfaces/Surah";
import ReportContentDialogueBox from "../../components/chatbot/UI/ReportContentDialogueBox";
import { ChatMessage } from "../../components/chatbot/interfaces/ChatMessage";
import QuranDialogBox from "@/app/components/chatbot/UI/QuranDialogBox";
import StoryContainer from "@/app/components/chatbot/UI/StoryContainer";
import groupChatMessages from "@/utils/groupChatMessages";
import WaveForm from "../../components/chatbot/UI/WaveForm";
import hidePromptExtraOptionsModelBoxArray from "@/app/components/chatbot/interfaces/hidePromptExtraOptionsModelBoxArray";
import { useRouter, useSearchParams } from "next/navigation";
import {
  SessionInitMessage,
  ChatRecordType,
} from "../../utils/types";
import { retryOperation, wsSendAsync } from "@/app/utils/retryOpernation";
import HamBurger from "@/app/components/chatbot/UI/HamBurger";
import ChatHistoryCupboard from "@/app/components/chatbot/UI/ChatHistoryCupboard";
import FullStoryViewContainer from "@/app/components/chatbot/UI/FullStoryViewContainer";
import StoryModeExtraOptions from "@/app/components/chatbot/UI/StoryModeExtraOptions";


function ChatContent() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const inputRef = useRef<HTMLDivElement | null>(null);
  const [showPlaceholder, setShowPlaceholder] = useState<boolean | null>(true);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [greeting, setGreeting] = useState<string | null>(
    "Assalam O Alaykum, I am Tadabbur, how may I help you today?",
  );

  const wsRef = useRef<WebSocket | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
  const [placeholder, setPlaceholder] = useState<string | null>(
    "Ask me a Quranic Story",
  );
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [sessionID, setSessionID] = useState<string | null>(null);
  const [streamingMessageIndex, setStreamingMessageIndex] = useState<
    number | null
  >(null);

  const currentPlayableAudio = useRef<{ user_message_id: string, response_message_id: string, state: "loading" | "playing" | "paused" | "ended" | null } | null>(null);
  const [messageIDs, setMessageIDs] = useState<(string | null)[] | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatRecordType[] | null>(null);
  const messageScrollFlag = useRef<boolean | null>(false);
  const [active, setActive] = useState<boolean[]>([false, false, false]);
  const committedTextRef = useRef<string>("");
  const tempSpeechRef = useRef<string>("");
  const [showPersonalizationForm, setShowPersonalizationForm] = useState<boolean>(false)
  const [isCheckingPersonalization, setIsCheckingPersonalization] = useState<boolean>(true)
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [hideReportContentDialogueBox, setHideReportContentDialogueBox] =
    useState<boolean | null>(true);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [fileContext, setFileContext] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false);
  const currentMessageIDRef = useRef<string | null>(null);
  const [reportedMessageIDs, setReportedMessageIDs] = useState<string[] | null>(
    [],
  );
  const [currentMode, setCurrentMode] = useState<"normal" | "story" | null>("story");
  const [isGenerating, setIsGenerating] = useState(false);
  const [openStoryModeExtraOptions, setOpenStoryModeExtraOptions] = useState<boolean>(false)
  const currentStreamingMsgRef = useRef<{
    message_id: string;
    reply_to_message_id: string;
  } | null>(null);
  const streamingContentRef = useRef<string>("");
  const stopStreamRef = useRef<(() => void) | null>(null);

  const searchParams = useSearchParams()
  const oldMessagesRef = useRef<AssistantMessage[]>([]);
  const controls = useAnimationControls();
  const [hidePromptExtraOptionsModelBoxArray, setHidePromptExtraOptionsModelBoxArray] =
    useState<hidePromptExtraOptionsModelBoxArray[]>([]);
  const [openFullStoryView, setOpenFullStoryView] = useState<boolean>(false)
  const [storyData, setStoryData] = useState<StoryParagraph[]>([])
  const router = useRouter()
  const [openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox] = useState<
    boolean
  >(false);

  const x = useMotionValue(0)
  const animationRef = useRef<any>(null)

  const startAnimation = () => {
    animationRef.current = animate(x, -1000, {
      duration: 15,
      ease: "linear",
      repeat: Infinity,
      repeatType: "loop"
    })
  }

  const isStoryMode = active[1]

  useEffect(() => {
    if (!isStoryMode || !wsRef.current) return

    const initializeStoryMode = async () => {
      const user = localStorage.getItem("user");
      let user_id = null;
      if (user) {
        try {
          const userData = JSON.parse(user);
          user_id = userData.id;
        } catch (e) {
          console.error("Error parsing user data:", e);
        }
      }
      const sessionInit: SessionInitMessage = {
        type: "session-init",
        session_id: "",
        user_id: "",
        model: "",
        mode: "story"
      };

      try {
        await wsSendAsync(
          wsRef.current,
          sessionInit,
          8,
          500
        );
      }
      catch (error) {
        console.error("❌ Failed to initialize WebSocket session:", error);
      }
    }
    initializeStoryMode()

  }, [isStoryMode])

  function preprocessContent(content: string) {
    if (!content) return "";
    let processed = content;

    processed = processed.replace(/\\n/g, "\n");
    processed = processed.replace(/([^\n])\s*(#{1,6}\s)/g, "$1\n\n$2");
    processed = processed.replace(/(\|[ -]*\|)\s*(?=\|)/g, "$1\n");
    processed = processed.replace(/([^\n])\s*(-\s)/g, "$1\n$2");
    processed = processed.replace(/([^\n])\s*(\d+\.\s)/g, "$1\n$2");

    return processed;
  }

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push('/pages/auth');
  };


  useEffect(() => {
    const audioEl = audioRef.current;
    if (!audioEl) return;

    const handlePlay = () => {
      // update ref for centralized audio management
      if (currentPlayableAudio.current) {
        currentPlayableAudio.current.state = "playing"
      }
      setMessages(prev =>
        prev.map(m =>
          m.message_id === currentPlayableAudio.current?.user_message_id
            ? {
              ...m,
              responses: m.responses.map(n =>
                n.message_id === currentPlayableAudio.current?.response_message_id
                  ? { ...n, audio_state: "playing" }
                  // nullify the rest
                  : { ...n, audio_state: null }
              ),
            }
            : { ...m, responses: m.responses.map(b => ({ ...b, audio_state: null })) }
        )
      );
    };

    const handlePause = () => {

      // update ref for centralized audio management
      if (currentPlayableAudio.current) {
        currentPlayableAudio.current.state = "paused"
      }
      setMessages(prev =>
        prev.map(m =>
          m.message_id === currentPlayableAudio.current?.user_message_id
            ? {
              ...m,
              responses: m.responses.map(n =>
                n.message_id === currentPlayableAudio.current?.response_message_id
                  ? { ...n, audio_state: "paused" }
                  : n
              ),
            }
            : m
        )
      );
    };

    const handleEnded = () => {
      // update ref for centralized audio management
      if (currentPlayableAudio.current) {
        currentPlayableAudio.current.state = "ended"
      }
      setMessages(prev =>
        prev.map(m =>
          m.message_id === currentPlayableAudio.current?.user_message_id
            ? {
              ...m,
              responses: m.responses.map(n =>
                n.message_id === currentPlayableAudio.current?.response_message_id
                  ? { ...n, audio_state: "ended" }
                  : n
              ),
            }
            : m
        )
      );
    };

    audioEl.addEventListener("play", handlePlay);
    audioEl.addEventListener("pause", handlePause);
    audioEl.addEventListener("ended", handleEnded);

    return () => {
      audioEl.removeEventListener("play", handlePlay);
      audioEl.removeEventListener("pause", handlePause);
      audioEl.removeEventListener("ended", handleEnded);

      // reset state for this audio
      setMessages(prev =>
        prev.map(m =>
          m.message_id === currentPlayableAudio.current?.user_message_id
            ? {
              ...m,
              responses: m.responses.map(n =>
                n.message_id === currentPlayableAudio.current?.response_message_id
                  ? { ...n, audio_state: null }
                  : n
              ),
            }
            : m
        )
      );
    };
  }, []);

  useEffect(() => {
    const handleMicStart = () => {
      setIsRecording(true);
      setIsTranscribing(false);
      tempSpeechRef.current = "";
    };

    const handleMicStop = () => {
      setIsRecording(false);
    };

    const handleTranscriptionStart = () => {
      setIsTranscribing(true);
    };

    const handleTranscriptionEnd = () => {
      setIsTranscribing(false);
    };

    const handleSTTResult = (e: Event) => {
      setIsTranscribing(false);
      const customEvent = e as CustomEvent;
      const text = customEvent.detail;

      if (inputRef.current && text) {
        const currentText = inputRef.current.innerText.trim();
        const newText = currentText ? `${currentText} ${text}` : text;

        inputRef.current.innerText = newText;
        committedTextRef.current = newText;


        const range = document.createRange();
        const sel = window.getSelection();
        if (inputRef.current.lastChild) {
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
    window.addEventListener("tadabbur-transcription-start", handleTranscriptionStart);
    window.addEventListener("tadabbur-transcription-error", handleTranscriptionEnd);
    window.addEventListener("tadabbur-stt-result", handleSTTResult);


    return () => {
      window.removeEventListener("tadabbur-mic-start", handleMicStart);
      window.removeEventListener("tadabbur-mic-stop", handleMicStop);
      window.removeEventListener("tadabbur-transcription-start", handleTranscriptionStart);
      window.removeEventListener("tadabbur-transcription-error", handleTranscriptionEnd);
      window.removeEventListener("tadabbur-stt-result", handleSTTResult);
    };
  }, []);

  useEffect(() => {
    const checkPersonalization = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          setIsCheckingPersonalization(false);
          setShowPersonalizationForm(true);
          return;
        }
        const data = await retryOperation(async () => {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/personalization/status`,
            {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            }
          );
          if (!response.ok) {
            console.error("❌ Failed to fetch personalization status:", response.status);
            setShowPersonalizationForm(true);
            setIsCheckingPersonalization(false);
            return;
          }
          return await response.json();
        }, 5, 1000);
        // console.log("📊 Personalization data received:", data);

        if (data.is_personalized && data.username && data.age) {

          // console.log("✅ User already personalized");
          setShowPersonalizationForm(false);


          if (data.age <= 12) {
            setGreeting(
              `Assalamu Alaykum ${data.username}! 🌟 I am Tadabbur, your friend!`
            );
            setPlaceholder("Tell me about prophets...");
          } else {
            setGreeting(
              `Assalamu Alaykum ${data.username}, I am Tadabbur. How may I assist you with your Quranic studies?`
            );
            setPlaceholder("Let's learn about the Quran");
          }
        } else {

          // console.log("❌ User not personalized, showing form");
          setShowPersonalizationForm(true);
        }
      } catch (error) {
        console.error("❌ Error checking personalization:", error);
        setShowPersonalizationForm(true);
      } finally {
        setIsCheckingPersonalization(false);
      }
    };

    checkPersonalization();
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No authentication token found. Cannot connect to chat.");
      return;
    }

    const urlSessionId = searchParams.get("session_id");


    const websocket = new WebSocket(`${process.env.NEXT_PUBLIC_WEBSOCKET_URL}/ws/chat?token=${token}`);
    wsRef.current = websocket;
    websocket.onopen = async () => {
      const user = localStorage.getItem("user");
      let user_id = null;
      if (user) {
        try {
          const userData = JSON.parse(user);
          user_id = userData.id;
        } catch (e) {
          console.error("Error parsing user data:", e);
        }
      }
      const sessionInit: SessionInitMessage = {
        type: "session-init",
        session_id: urlSessionId || "",
        user_id: user_id,
        model: "kimi-k2-instruct-0905",
        mode: "normal"
      };

      try {
        await wsSendAsync(
          websocket,
          sessionInit,
          8,
          500
        );
        if (urlSessionId) {
          await wsSendAsync(
            websocket, {
            type: "get_chat",
            session_id: urlSessionId,
            user_id: user_id,
          }, 8, 500
          )
        }
      }
      catch (error) {
        console.error("❌ Failed to initialize WebSocket session:", error);
      }
      setReportedMessageIDs([]);
    };

    wsRef.current.onerror = (error) => {
      console.error("An error occured in websocket", error);
    };

    wsRef.current.onclose = () => {
      // console.log("Websocket closed!");
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Data from websocket", event.data);

      const type = data.type;
      switch (type) {
        case "undo-report":
          const id = data.message_id;
          if (id) {
            setReportedMessageIDs((prev) => {
              if (!prev) return prev;
              return prev.filter((i) => i !== id);
            });
          }
          break;

        case "tts_audio_url":
          const audio_url = data.audio_url;
          const tts_message_id = data.message_id;
          const user_message_id = data.user_id
          if (audio_url && tts_message_id && user_message_id) {
            // logic here
            try {
              // store the audio_url for next playback
              setMessages(prev => prev.map(m => m.message_id === user_message_id ? { ...m, responses: m.responses.map(r => r.message_id === tts_message_id ? { ...r, audio_link: audio_url } : r) } : m))

              // only play if current playable audio is the one that matches response ID
              if (audioRef.current && currentPlayableAudio.current?.response_message_id == tts_message_id) {
                audioRef.current.src = ""
                audioRef.current.src = audio_url
                audioRef.current.play()
              }
            } catch (err) {
              console.log("Some error occured while assigning audio url", err)
            }
          }
          break;

        case "session_id":
          setCurrentMode(null)
          const session_id = data.session_id;
          const session_status = data.status;
          const message_ids = data.message_ids;
          const session_mode: "story" | "normal" = data.mode || "normal"
          if (session_status === "acknowledged") {
            setSessionID(session_id);
            const currentUrlId = searchParams.get("session_id");
            if (!currentUrlId || currentUrlId === "" || currentMode != session_mode) {
              router.push(`/pages/chatbot?session_id=${session_id}`, { scroll: false });
            }
            setMessages([]);
            setActive([false, false, false])
            setCurrentMode(session_mode)
            setHidePromptExtraOptionsModelBoxArray([])
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
          } else if (history_status === "error") {
            alert("Error loading chat history: " + data.error);
          }
          break;

        case "delete_session":
          const delete_status = data.status;
          if (delete_status === "success") {
            // Refresh chat history
            const user = localStorage.getItem("user");
            let user_id = null;
            if (user) {
              try {
                const userData = JSON.parse(user);
                user_id = userData.id;
              } catch (e) {
                console.error("Error parsing user data:", e);
              }
            }
            if (user_id) {
              wsSendAsync(wsRef.current, {
                type: "chat_history",
                user_id: user_id,
              });
            }
            alert("Chat session deleted successfully");
          } else {
            alert("Error deleting chat session: " + data.error);
          }
          break;

        case "delete_all_sessions":
          const delete_all_status = data.status;
          if (delete_all_status === "success") {
            setChatHistory([]);
            alert("All chat sessions deleted successfully");
          } else {
            alert("Error deleting all chat sessions: " + data.error);
          }
          break;

        case "get_chat":
          const status = data.status;
          const mode: "story" | "normal" = data.mode;
          if (status === "acknowledged") {
            const messageIDs = data.unique_message_ids;
            const session_id = data.session_id
            const chat_history = groupChatMessages(data.chat_history);
            setMessages(chat_history);
            setMessageIDs(messageIDs);
            setCurrentMode(mode)

            // initialize an emtpy array for hidePromptExtraOptionsModelBoxArray
            const array: hidePromptExtraOptionsModelBoxArray[] = [];
            if (data.chat_history.length > 0) {
              for (const record of data.chat_history) {
                if (record.role === "assistant") {
                  array.push({ assistant_message_id: record.message_id, hidePromptExtraOptionsModelBox: true })
                }
              }
            }
            setHidePromptExtraOptionsModelBoxArray(array)
            router.push(`/pages/chatbot?session_id=${session_id}`);
          }
          break;

        case "assistance_response":
          const reply: string = data.content.response ?? "No reply from server";
          const has_verse_audio: boolean = data.content.has_verse_audio
          const has_verse_image: boolean = data.content.has_verse_image
          const message_id: string = data.message_id;
          // assign reply to message ID with order data.reply_to_message_id >> currentMessageIDRef.current >> null
          const reply_to_message_id =
            data.reply_to_message_id || currentMessageIDRef.current || null;
          const resend_flag = data.resend_flag;
          const audio_data: SurahForAudios[] = data.content.audio_data || []
          const verse_images: SurahForVerseImages[] = data.content.verse_images || []
          const story_data: StoryParagraph[] = data.content.story_segments ?? []

          // check if oldMessages is present with resend flag
          if (resend_flag) {
            if (
              !oldMessagesRef.current ||
              oldMessagesRef.current.length === 0
            ) {
              // console.log("No old messages so returning...");
              break;
            }
          }

          messageScrollFlag.current = false;
          setLoadingMessage(null);

          // add a new object for the upcoming assistant's message
          setHidePromptExtraOptionsModelBoxArray((prev) => {
            return [
              ...(prev || []),
              { assistant_message_id: message_id, hidePromptExtraOptionsModelBox: true }
            ];
          });

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
                audio_link: null,
                audio_state: null,
                has_verse_audio: has_verse_audio,
                verse_audio_data: audio_data,
                has_verse_image: has_verse_image,
                verse_images: verse_images,
                story_data: story_data
              });

              // set the number of active message index
              lastUserMessage.active_message_index =
                lastUserMessage.number_of_responses - 1;
            }

            return updated;
          });


          setLoading(false);
          setLoadingMessage(null);
          setIsGenerating(true);
          streamingContentRef.current = "";
          currentStreamingMsgRef.current = {
            message_id: message_id,
            reply_to_message_id: reply_to_message_id || ""
          };
          const tokens = reply.split(/(\s+)/);

          let stopFlag = false;
          stopStreamRef.current = () => { stopFlag = true; };

          (async () => {
            for (let i = 0; i < tokens.length; i += 4) {
              if (stopFlag) break;

              const chunk = tokens.slice(i, i + 4).join("");
              await new Promise((resolve) => setTimeout(resolve, 2));

              if (stopFlag) break;


              setMessages((prev) => {
                if (!prev || prev.length === 0) return prev;
                const updated = [...prev];
                const streamIndex = streamingMessageIndex ?? updated.length - 1;

                if (streamIndex >= 0 && streamIndex < updated.length) {
                  const lastMsg = updated[streamIndex];
                  const lastResIdx = (lastMsg.number_of_responses || 1) - 1;

                  updated[streamIndex].responses[lastResIdx].content =
                    (updated[streamIndex].responses[lastResIdx].content || "") +
                    chunk;
                  streamingContentRef.current = updated[streamIndex].responses[lastResIdx].content;
                }
                return updated;
              });
            }
          })().then(() => {
            setStreamingMessageIndex(null);
            stopStreamRef.current = null;
            setStreamingMessageIndex(null);
            setIsGenerating(false);
            currentStreamingMsgRef.current = null;
            streamingContentRef.current = "";
          });
          break;

        case "stop_acknowledged":
          // reset states related to streaming
          setIsGenerating(false);
          setStreamingMessageIndex(null);
          setLoading(false);
          currentStreamingMsgRef.current = null;
          streamingContentRef.current = "";
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
          setLoading(false)
          setLoadingMessage(message);
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
        default:
          break;
      }
    };
  }, []);

  useEffect(() => {
    let isCancelled = false;

    const processFile = async () => {
      if (attachedFile && !fileContext && !isUploading) {
        setIsUploading(true);
        const formData = new FormData();
        formData.append("file", attachedFile);
        formData.append("session_id", sessionID || "default_session");

        try {
          const data = await retryOperation(async () => {
            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/upload`, {
              method: "POST",
              body: formData,
            });
            if (!response.ok) throw new Error("Upload failed");
            return await response.json();
          }, 8, 1000)

          if (!isCancelled && data.extracted_text) {
            setFileContext(data.extracted_text);
            // console.log("File parsed. Text ready to send on Enter.");
          }
        } catch (error) {
          if (!isCancelled) {
            console.error("Upload error:", error);
            alert("Failed to process file.");
            setAttachedFile(null);
          }
        } finally {
          if (!isCancelled) {
            setIsUploading(false);
          }
        }
      }
    };

    processFile();

    return () => {
      isCancelled = true;
    };
  }, [attachedFile, sessionID]);

  const stopGeneration = () => {
    if (!currentStreamingMsgRef.current || !wsRef.current) return;

    if (stopStreamRef.current) {
      stopStreamRef.current();
      stopStreamRef.current = null;
    }

    const partialContent = streamingContentRef.current;
    const msgId = currentStreamingMsgRef.current.message_id;

    setIsGenerating(false);
    setStreamingMessageIndex(null);
    setLoading(false);

    wsSendAsync(wsRef.current, {
      type: "stop_generation",
      message_id: msgId,
      partial_content: partialContent,
    });

    currentStreamingMsgRef.current = null;
    streamingContentRef.current = "";
  };

  const ask = async (
    input: string,
    guidelines: string | null = null,
    resend_flag: boolean = false,
    resend_message_id: string | null = null,
    old_responses_attachments: { responses: AssistantMessage[], attachments: Attachment[] } | null = null
  ) => {
    if (streamingMessageIndex !== null || (!input.trim() && !fileContext)) return;

    if (resend_flag) {
      if (!old_responses_attachments || old_responses_attachments.responses.length === 0) {
        // console.log("No old assistant responses, continuing....");
        return;
      }
      else {
        // remove the message object only with the user's message id
        setMessages((prev: ChatMessage[]) =>
          prev.filter(
            (m) => m.message_id !== resend_message_id
          )
        );
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
      // console.log("No message ID so returning");
      return;
    }


    const attachments_array: Attachment[] = []
    if (fileContext) {
      if (attachedFile?.name && attachedFile?.type) {
        attachments_array.push({ attachmentName: attachedFile.name, attachmentType: attachedFile?.type })
      }
      // Reset file states
      setAttachedFile(null);

    }

    const userMessage: ChatMessage = {
      message_id: messageID,
      role: "user",
      content: input,
      attachments: resend_flag ? old_responses_attachments?.attachments ?? [] : attachments_array,
      number_of_responses: resend_flag ? old_responses_attachments?.responses.length ?? 0 : 0,
      active_message_index: 0,
      // add a dummy response message for loading state
      responses: [
        {
          role: "assistant",
          message_id: "",
          reply_to_message_id: null,
          content: "",
          feedback: null,
          audio_link: null,
          audio_state: null,
          has_verse_audio: false,
          verse_audio_data: [],
          has_verse_image: false,
          verse_images: [],
          story_data: [],
        },
      ],
    };
    oldMessagesRef.current = resend_flag ? old_responses_attachments?.responses ?? [] : [];

    setMessages((prev) => {
      // prev is already typed correctly from useState
      const updated = [...(prev || []), userMessage];
      // Set the streaming index to the upcoming new message
      setStreamingMessageIndex(updated.length - 1);
      return updated;
    });

    currentMessageIDRef.current = messageID;

    await wsSendAsync(wsRef.current, {
      type: "user_message",
      message_id: messageID,
      role: "user",
      system_instructions: guidelines || "",
      content: input,
      file_name: attachedFile?.name,
      file_type: attachedFile?.type,
      resend_flag: resend_flag,
      resend_message_id: resend_message_id || "",
      new_file_context: fileContext,
    });
    setFileContext(null);
    if (inputRef.current) {
      inputRef.current.innerText = "";
      setShowPlaceholder(true);
    }
  };

  const handleInput = async (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!inputRef.current) return;

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      if (attachedFile && isUploading) {
        alert("File is still uploading, please wait a moment...");
        return;

      }

      const input = inputRef.current?.innerText;
      if (input.trim() != "" || fileContext) {
        ask(input.trim());
      }
    }
  };

  const sendPrompt = () => {
    if (!inputRef.current) return;
    if (attachedFile && isUploading) {
      alert("File is still uploading, please wait a moment...");
      return;

    }

    const input = inputRef.current?.innerText;
    if (input.trim() != "" || fileContext) {
      ask(input.trim());
    }
  }

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

  if (isCheckingPersonalization) {
    return (
      <ProtectedRoute>
        <div className="w-screen h-screen flex items-center justify-center bg-gray-50">
          <div className="flex flex-col items-center gap-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-black"></div>
            <p className="switzer-500 text-gray-600">Loading your profile...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      {/* {showPersonalizationForm ? (
        <RegistrationForm
          onComplete={(data) => {
            setShowPersonalizationForm(false);
            if (data.age <= 12) {
              setGreeting(
                `Assalamu Alaykum ${data.username}! 🌟 I am Tadabbur, your friend!`,
              );
              setPlaceholder("Tell me about prophets...");
            } else {
              setGreeting(
                `Assalamu Alaykum ${data.username}, I am Tadabbur. How may I assist you with your Quranic studies?`,
              );
            }
          }}
        />
      ) : ( */}
      {/* "linear-gradient(to bottom, #001414, #000000 )" */}
      <motion.div
        animate={{
          background: currentMode === "normal"
            ? "#F9FAFB"
            : "#000000",
        }}
        transition={{ duration: 0.3 }}
        className="relative w-screen h-screen flex flex-col items-center">


        <div className="absolute -top-2 right-4">
          {currentMode === "story" ? (
            <Image className="w-16 h-auto object-cover object-top" src={TadabburFontWhite}
              alt="tadabbur-font-white" />
          ) : (<Image className="w-16 h-auto object-cover object-top" src={TadabburFontBlack}
            alt="tadabbur-font-black" />)}
        </div>


        <ChatProvider
          chatHistory={chatHistory}
          setChatHistory={setChatHistory}
          wsRef={wsRef}
          sessionID={sessionID}
          attachedFile={attachedFile}
          setAttachedFile={setAttachedFile}
          messages={messages}
          setMessages={setMessages}
          audioRef={audioRef}
          ask={ask}
          currentPlayableAudio={currentPlayableAudio}
          hideReportContentDialogueBox={hideReportContentDialogueBox}
          setHideReportContentDialogueBox={setHideReportContentDialogueBox}
          hidePromptExtraOptionsModelBoxArray={hidePromptExtraOptionsModelBoxArray}
          setHidePromptExtraOptionsModelBoxArray={setHidePromptExtraOptionsModelBoxArray}
          active={active}
          setActive={setActive}
          openChatHistoryDialogueBox={openChatHistoryDialogueBox}
          setOpenChatHistoryDialogueBox={setOpenChatHistoryDialogueBox}
          currentMode={currentMode}
          setCurrentMode={setCurrentMode}
          setOpenFullStoryView={setOpenFullStoryView}
          setStoryData={setStoryData}
          openStoryModeExtraOptions={openStoryModeExtraOptions}
          setOpenStoryModeExtraOptions={setOpenStoryModeExtraOptions}
        >
          {/* renders only when open chat history dialogue box is true */}
          {/* <ChatHisoryDialogueBox /> */}

          <AnimatePresence>
            {openChatHistoryDialogueBox && (
              <ChatHistoryCupboard />
            )}
          </AnimatePresence>
          <AnimatePresence>
            {openFullStoryView && (
              <FullStoryViewContainer story_data={storyData} />
            )}
          </AnimatePresence>

          <div className={`w-full h-full flex flex-col items-center z-10 ${currentMode === "normal" ? "" : "black-scrollbar"} overflow-y-auto`}>
            <div className="absolute top-0 p-2 w-full">
              {/* 
              <div className="pointer-events-auto">
                <Controls wsRef={wsRef} />
              </div> */}


              {/* <button
                onClick={handleLogout}
                className="pointer-events-auto mr-2 mt-2 px-4 py-2 bg-black hover:bg-gray-800 text-white text-sm font-medium rounded-md shadow-md transition-colors"
              >
                Logout
              </button> */}
            </div>
            <HamBurger />
            <div
              id="chat-bot"
              className={`w-full ${messages && messages?.length > 0 ? "h-max mt-16" : "h-full items-center mt-12"} px-4 lg:w-2/3 flex flex-col gap-y-4 ${!messages ? "justify-center" : ""}`}
            >
              <AnimatePresence>

                {messages?.length === 0 && (
                  <motion.div
                    className="w-full flex flex-col gap-y-4 items-center self-center"
                  >
                    {currentMode === "story" && (
                      <motion.div whileHover={{ backgroundColor: "#ffffff0d" }} className="w-max py-2 px-4 rounded-full border border-white/10 cursor-pointer flex items-center gap-x-1 scale-90 sm:scale-100">
                        <div className="rounded-md py-0.5 px-1 shadow-md bg-red-400 flex justify-center items-center mr-1">
                          <span className="poppins-semibold text-[0.6rem] text-white">NEW</span>
                        </div>
                        <p className="switzer-500 tracking-tight text-[0.8rem] text-white">Introducing Story Mode</p>
                        <ArrowLeft className="w-3 h-3 fill-current rotate-180 text-white" />
                      </motion.div>
                    )}

                    <motion.p
                      initial={false}
                      animate={{
                        color: currentMode === "normal" ? "#000000E6" : "#FFFFFF"
                      }}
                      transition={{ duration: 0.3 }}
                      className={`text-center px-6 ${currentMode === "normal" ? "switzer-500 text-4xl tracking-tight" : "inter-600 text-[2.6rem] sm:text-[2.8rem] tracking-tighter lg:text-6xl leading-9 lg:leading-12 subpixel-antialiased"}`}
                    >
                      {currentMode === "story" ? (
                        <>
                          QURANIC STORIES EXPLAINED WITH <span className="text-cyan-300">POWERFUL</span>,
                          <span className="flex gap-x-1 justify-center items-center text-green-300"><span className="rounded-full border-2 border-dotted border-red-400 p-1.5"><EngagingIcon className="md:w-12 md:h-12 w-8 h-8" /></span> CREATIVE</span> VISUALS.
                        </>
                      ) : (
                        greeting
                      )}
                    </motion.p>

                    {currentMode === "story" && (
                      <div id="default-prompts-box-story" className="w-full relative overflow-x-clip">
                        <motion.div
                          style={{ x }}
                          onMouseEnter={() => animationRef.current?.pause()}
                          onMouseLeave={() => animationRef.current?.play()}
                          onViewportEnter={startAnimation}

                          className="w-max flex gap-x-2">
                          {Array.from({ length: 3 }).map((_, i) => (
                            <motion.div key={i} id="carousel-default-prompts-story" className="w-1/2">
                              <div className="grid grid-cols-4 grid-rows-1 gap-x-4 w-full">
                                <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.5, ease: easeInOut }} className="cursor-pointer w-max flex flex-col gap-y-1 p-1.5 rounded-lg border border-white/10">
                                  <Image className="rounded-md md:w-36 md:h-34 w-34 h-30 object-cover object-top" alt="smiling-boy" src={QuranReading} />
                                  <p className="switzer-500 text-white/80 w-36">Generate the story of the people of the Cave.</p>
                                </motion.div>
                                <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.3, ease: easeInOut }} className="cursor-pointer w-max flex flex-col gap-y-1 p-1.5 rounded-lg border border-white/10">
                                  <Image className="rounded-md md:w-36 md:h-34 w-34 h-30 object-cover object-top" alt="smiling-boy" src={QuranPic} />
                                  <p className="switzer-500 text-white/80 w-36">Narrate the occasion of first revelation.</p>
                                </motion.div>
                                <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.3, ease: easeInOut }} className="cursor-pointer w-max flex flex-col gap-y-1 p-1.5 rounded-lg border border-white/10">
                                  <Image className="rounded-md md:w-36 md:h-34 w-34 h-30 object-cover object-top" alt="smiling-boy" src={DesertPic} />
                                  <p className="switzer-500 text-white/80 w-36">Generate the story of Prophet Yusuf عليه السلام.</p>
                                </motion.div>
                                <motion.div whileHover={{ scale: 1.02 }} transition={{ duration: 0.3, ease: easeInOut }} className="cursor-pointer w-max flex flex-col gap-y-1 p-1.5 rounded-lg border border-white/10">
                                  <Image className="rounded-md md:w-36 md:h-34 w-34 h-30 object-cover object-top" alt="old-ark" src={ArkPic} />
                                  <p className="switzer-500 text-white/80 w-36">Generate the story of Prophet Noah عليه السلام and his people.</p>
                                </motion.div>
                              </div>
                            </motion.div>
                          ))}

                        </motion.div>
                      </div>
                    )}
                    {currentMode === "normal" && (
                      <div className="default-prompts-box-normal w-full relative overflow-x-clip">
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
                            <motion.div key={i} id="carousel-default-prompts-normal" className="carousel w-1/2">
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
                                          `${prompt.title} ${prompt.description}`,
                                        );
                                      }}
                                      className="bg-white rounded-md shadow-sm backdrop-blur-md cursor-pointer"
                                    >
                                      <div className="w-full flex flex-col px-3 pt-3 pb-6 gap-y-1">
                                        <div className="flex gap-x-3">
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
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence mode="popLayout">
                {/* first render user messages */}
                {messages?.map((record, record_index) => {
                  return (
                    <div key={record_index}>
                      {record?.attachments?.length > 0 && (
                        record.attachments.map((attachment, attachment_index) => {
                          return (
                            <div key={attachment_index} id="chatbot-messages-box" className="w-max min-w-60 max-w-70 border border-black/5 ml-auto px-3 py-3 rounded-md text-xs flex items-center gap-x-2 my-2 relative">
                              {attachment.attachmentType === "text/plain" ? (
                                <div className="p-1 border border-[#FFA800]/10 shadow-[0.1rem] rounded-md bg-[#FFA800]/10">
                                  <TextFileIcon className="fill-current text-blue-400 w-8 h-8" />
                                </div>
                              ) : attachment.attachmentType === "application/pdf" ? (
                                <PdfFileIcon className="fill-current text-blue-400 w-8 h-8" />
                              ) : (null)}
                              <div className="absolute border border-black/5 rounded-md w-max px-2 py-0.5 poppins-semibold -top-3 z-10 -right-2 shadow-2xs fill-current text-black/30 bg-gray-50 subpixel-antialiased">
                                <p>ATTACHED</p>
                              </div>
                              <div className="flex flex-col gap-y-0.5">
                                <p className="roboto-600 text-[0.9rem]">{attachment.attachmentName}</p>
                                <p className="subpixel-antialiased text-black/70" style={{ fontStyle: "italic" }}>
                                  {attachment.attachmentType && attachment.attachmentType === "text/plain" ? "Text"
                                    : attachment.attachmentType === "application/pdf" ? "PDF"
                                      : "File"} File
                                </p>
                              </div>
                            </div>
                          )
                        })
                      )}
                      <div>
                        <p className={`ml-auto w-max min-w-40 max-w-[20rem] rounded-md switzer-500 py-2 shadow-md px-3 text-white ${currentMode === "normal" ? "border bg-neutral-900 border-black/5" : "bg-linear-to-b from-[#570900] to-[#8A0F00]"}`}>
                          {record.content}
                        </p>
                      </div>

                      {/* PromptExtraOptions */}
                      <div>
                        <PromptExtraOptions message_id={record.message_id} reply_to_message_id={null} parent_index={record_index} assistant_index={null} messageType="user" />
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
                        ) : !loading && loadingMessage && !ai_msg.content ? (
                          <p key={ai_msg_idx} id="loading-message" className={`switzer-500 animate-pulse ${currentMode === "normal" ? "" : "text-white/80"}`}>{loadingMessage}</p>
                        ) : reportedMessageIDs &&
                          !reportedMessageIDs.includes(ai_msg?.message_id) &&
                          ai_msg_idx === record.active_message_index ? (
                          <div key={ai_msg_idx}>
                            <div className={`w-max min-w-40 max-w-full switzer-500 mt-2 rounded-md px-3 ${currentMode === "normal" ? "bg-white shadow-md py-2" : ""}`}>
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
                                      className={`leading-7 my-2 ${currentMode === "normal" ? "text-gray-700" : "text-white"}`}
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
                                      className="text-blue-600 underline wrap-break-word"
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
                                  table: ({ node, ...props }) => (
                                    <div className="overflow-x-auto my-4 border border-black/20 rounded-lg shadow-sm">
                                      <table className="min-w-full divide-y divide-gray-200" {...props} />
                                    </div>
                                  ),
                                  thead: ({ node, ...props }) => (
                                    <thead
                                      className="bg-gray-50"
                                      {...props}
                                    />
                                  ),
                                  tbody: ({ node, ...props }) => (
                                    <tbody
                                      className="bg-white divide-y divide-gray-200"
                                      {...props}
                                    />
                                  ),
                                  tr: ({ node, ...props }) => (
                                    <tr
                                      className="hover:bg-gray-50"
                                      {...props}
                                    />
                                  ),
                                  th: ({ node, ...props }) => (
                                    <th className="px-4 py-3 text-left text-sm font-medium text-black uppercase tracking-wider border-b" {...props} />
                                  ),
                                  td: ({ node, ...props }) => (
                                    <td className="px-4 py-3 text-sm text-gray-700 border-b border-black/20 whitespace-pre-wrap" {...props} />
                                  ),
                                  code({
                                    inline,
                                    className,
                                    children,
                                    ...props
                                  }: {
                                    inline?: boolean;
                                    className?: string;
                                    children?: ReactNode;
                                  } & HTMLAttributes<HTMLElement>) {
                                    const match = /language-(\w+)/.exec(className || '');

                                    if (!inline && match) {
                                      // Create a clean props object without HTML attributes that conflict
                                      const syntaxHighlighterProps = {
                                        language: match[1],
                                        PreTag: "div" as const,
                                        className: "rounded-md shadow-sm my-4",
                                        style: dracula as { [key: string]: CSSProperties }
                                      };

                                      return (
                                        <SyntaxHighlighter
                                          {...syntaxHighlighterProps}
                                        >
                                          {String(children).replace(/\n$/, "")}
                                        </SyntaxHighlighter>
                                      );
                                    } else {
                                      return (
                                        <code
                                          className="bg-gray-100 text-red-500 px-1.5 py-0.5 rounded text-sm font-mono"
                                          {...props}
                                        >
                                          {children}
                                        </code>
                                      );
                                    }
                                  },
                                }}
                              >
                                {preprocessContent(ai_msg.content)}
                              </ReactMarkdown>
                            </div>

                            {ai_msg.has_verse_audio && ai_msg.verse_audio_data.length > 0 && streamingMessageIndex != record_index && (
                              <>
                                <br />
                                <QuranDialogBox
                                  type="audio"
                                  surahs={ai_msg?.verse_audio_data}
                                />
                              </>
                            )}

                            {ai_msg.has_verse_image && ai_msg.verse_images.length > 0 && streamingMessageIndex != record_index && (
                              <>
                                <br />
                                <QuranDialogBox
                                  type="read"
                                  surahs={ai_msg?.verse_images}
                                />
                              </>
                            )}
                            {ai_msg.story_data?.length > 0 && streamingMessageIndex != record_index && (
                              <StoryContainer story_data={ai_msg.story_data} />
                            )}
                            {streamingMessageIndex != record_index &&
                              reportedMessageIDs &&
                              !reportedMessageIDs.includes(
                                ai_msg?.message_id
                              ) && (
                                <div>
                                  <PromptExtraOptions
                                    message_id={ai_msg?.message_id}
                                    reply_to_message_id={
                                      ai_msg?.reply_to_message_id
                                    }
                                    parent_index={record_index}
                                    assistant_index={ai_msg_idx}
                                    messageType={"assistant"}
                                  />
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
                                  wsSendAsync(wsRef.current, {
                                    type: "undo-report",
                                    message_id: ai_msg.message_id,
                                  });
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

          <AnimatePresence>
            {isRecording && (
              <div className="px-4 w-full lg:w-2/3">
                <WaveForm />
              </div>
            )}
            {/* NEW: Transcribing Loading State in place of Waveform */}
            {!isRecording && isTranscribing && (
              <motion.div
                key="transcribing"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="w-full px-4 lg:w-2/3 flex"
              >
                <div className="bg-white/90 backdrop-blur-sm border ml-auto border-black/5 shadow-lg rounded-full px-4 py-3 flex items-center gap-x-3">
                  <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
                  <p className="switzer-500 text-sm text-black/80">Transcribing audio...</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div animate={{ paddingTop: currentMode === "normal" ? 16 : 20, paddingBottom: currentMode === "normal" ? 16 : 28 }} className={`mr-1.5 px-4 ${currentMode === "normal" ? "w-full lg:w-2/3 mt-4" : "w-[90%] sm:w-[70%] lg:w-1/2 mt-2 flex gap-x-2 items-center"} input-box`}>

            <motion.div
              animate={{ height: currentMode === "normal" ? attachedFile ? 200 : 160 : 42 }}
              transition={{ duration: 0.2, ease: easeInOut }}
              className={`flex relative shadow-md py-2 border gap-x-1 ${currentMode === "normal" ? "bg-white rounded-lg shadow-md px-3 border-black/10 flex-col" : "bg-[##001e1e] rounded-full px-2 border border-white/15 shadow-md justify-between items-center w-full"} `}
            >
              {attachedFile && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="relative w-max bg-white border border-black/10 px-3 py-2 rounded-md text-xs flex items-center gap-x-2 z-10">
                  {attachedFile?.type === "text/plain" ? (
                    <div className="p-1 border border-[#FFA800]/10 shadow-[0.1rem] rounded-md bg-[#FFA800]/10">
                      <TextFileIcon className="fill-current text-blue-400 w-6 h-6" />
                    </div>
                  ) : attachedFile?.type === "application/pdf" ? (
                    <PdfFileIcon className="fill-current text-blue-400 w-6 h-6" />
                  ) : (null)}
                  <div className="flex flex-col gap-y-0.5">
                    <p className="roboto-600 tracking-wide">{attachedFile.name}</p>
                    <p className="subpixel-antialiased text-black/70" style={{ fontStyle: "italic" }}>{attachedFile?.type ? attachedFile.type : "File"} File</p>
                  </div>

                  <div className="absolute -right-2 -top-1.5 bg-red-400 hover:bg-red-500 p-0.3 rounded-full" onClick={() => {
                    setAttachedFile(null);
                    setIsUploading(false);
                  }}>
                    <CrossIcon className="w-4 h-4 cursor-pointer" />
                  </div>
                </motion.div>
              )}
              {currentMode === "story" && (
                <motion.div onClick={() => {
                  setOpenStoryModeExtraOptions(prev => !prev)
                }} whileHover={{ backgroundColor: "#FFFFFF1A" }} className="p-1.5 rounded-full cursor-pointer">
                  <PlusIcon className="w-5 h-5" />
                </motion.div>
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
                className={`switzer-500 focus:outline-none ${currentMode === "normal" ? attachedFile ? "pt-[0.3rem] text-black h-2/3" : "text-black h-2/3" : "text-white pt-[0.02rem]"} overflow-y-auto w-full h-full`}
              ></div>
              {showPlaceholder && (
                <span
                  className={`absolute ${currentMode === "normal" ? attachedFile ? "top-16 text-black" : "top-2 text-black" : "top-1.8 text-white/70 left-11 text-[15px]"} pointer-events-none placeholder-input-box switzer-500`}
                >
                  {placeholder}
                </span>
              )}

              {isGenerating && (
                <div className="flex justify-end mb-1">
                  <button
                    onClick={stopGeneration}
                    className="flex items-center gap-x-2 px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white text-xs rounded-md switzer-500 transition-colors shadow-sm"
                  >
                    <div className="w-2 h-2 bg-white rounded-sm"></div>
                    Stop
                  </button>
                </div>
              )}

              {currentMode === "normal" && (
                <>
                  <BottomOptions />
                  <ExtraOptions />
                  <ModelBox modelList={ModelList} />
                </>
              )}
              {currentMode === "story" && (
                <>
                  <MicStoryMode />
                  <AnimatePresence>
                    {openStoryModeExtraOptions && (
                      <StoryModeExtraOptions />
                    )}
                  </AnimatePresence>
                </>
              )}
              {currentMode === "story" && (
                <motion.div onClick={sendPrompt} style={{ cursor: showPlaceholder ? "default" : "pointer" }} animate={{ backgroundColor: showPlaceholder ? "#FFFFFFCC" : "#FFFFFF" }} className="p-[5px] rounded-full bg-white">
                  <SendIcon className="w-5 h-5 fill-current text-black" />
                </motion.div>
              )}
            </motion.div>

          </motion.div>

          <ReportContentDialogueBox
            hideReportContentDialogueBox={hideReportContentDialogueBox}
            setHideReportContentDialogueBox={setHideReportContentDialogueBox}
          />

          <audio className="hidden" controls ref={audioRef} />
        </ChatProvider>
      </motion.div>
      {/* )} */}
    </ProtectedRoute>
  )
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatContent />
    </Suspense>
  )
}