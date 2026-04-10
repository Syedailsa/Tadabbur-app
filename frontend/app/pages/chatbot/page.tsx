"use client";

import type React from "react";
import { useEffect, useRef, useState, HTMLAttributes, Suspense } from "react";
import Image from "next/image"
import ChatProvider from "@/app/providers/chatbot/ChatProvider";
import DisclaimerIcon from "../../../icons/disclaimer.svg";
import CrossIcon from "../../../icons/cross_icon.svg"
import TextFileIcon from "../../../icons/text-file-icon.svg"
import SendIcon from "../../../icons/send_icon.svg";
import PdfFileIcon from "../../../icons/pdf-file-icon.svg"
import PlusIcon from "../../../icons/plus-icon-white.svg"
import TadabburFontWhite from "../../../images/tadabbur-font-white.png"
import TadabburFontBlack from "../../../images/tadabbur-font-black.png"
import EngagingIcon from "../../../icons/engage_icon.svg"
import ArrowLeft from "../../../icons/arrow-left-bold.svg"
import UndoArrow from "../../../icons/refresh.svg";
import { AssistantMessage, Attachment, StoryParagraph } from "@/app/components/chatbot/interfaces/ChatMessage";
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
import { defaultPromptsNormalMode, defaultPromptsStoryMode } from "@/static/data";
import BottomOptions from "../../components/chatbot/UI/BottomOptions";
import ExtraOptions from "../../components/chatbot/UI/ExtraOptions";
import MicStoryMode from "@/app/components/chatbot/UI/MicStoryMode";
import PromptExtraOptions from "../../components/chatbot/UI/PrompExtraOptions";
import generateUUID from "@/app/utils/generateShortId";
import generateSessionId from "@/app/utils/generateSessionID";
import { SurahForAudios, SurahForVerseImages } from "@/app/components/chatbot/interfaces/Surah";
import ReportContentDialogueBox from "../../components/chatbot/UI/ReportContentDialogueBox";
import { ChatMessage } from "../../components/chatbot/interfaces/ChatMessage";
import QuranDialogBox from "@/app/components/chatbot/UI/QuranDialogBox";
import StoryContainer from "@/app/components/chatbot/UI/StoryContainer";
import groupChatMessages from "@/app/utils/groupChatMessages";
import WaveForm from "../../components/chatbot/UI/WaveForm";
import hidePromptExtraOptionsModelBoxArray from "@/app/components/chatbot/interfaces/hidePromptExtraOptionsModelBoxArray";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";
import {
  SessionInitMessage,
  ChatRecordType,
} from "../../utils/types";
import { retryOperation, wsSendAsync } from "@/app/utils/retryOpernation";
import HamBurger from "@/app/components/chatbot/UI/HamBurger";
import ChatHistoryCupboard from "@/app/components/chatbot/UI/ChatHistoryCupboard";
import FullViewStoryContainer from "@/app/components/chatbot/UI/FullViewStoryContainer";
import StoryModeExtraOptions from "@/app/components/chatbot/UI/StoryModeExtraOptions";
import ImageContainer from "@/app/components/chatbot/UI/ImageContainer";
import Markdown from "@/app/components/markdown/Markdown";



function ChatContent() {
  const [serverErrorToast, setServerErrorToast] = useState<string | null>(null);
  useEffect(() => {
    if (serverErrorToast) {
      const timer = setTimeout(() => {
        setServerErrorToast(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [serverErrorToast]);

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
  const constraintRefNormalMode = useRef(null)
  const constraintRefStoryMode = useRef(null)
  const [openImageContainer, setOpenImageContainer] = useState<boolean>(false)
  const [currentMode, setCurrentMode] = useState<"normal" | "story" | null>("normal");
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
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected">("connected");
  const streamingMessageIndexRef = useRef<number | null>(null);
  const setStreamingMessageIndexSynced = (val: number | null) => {
    streamingMessageIndexRef.current = val;
    setStreamingMessageIndex(val);
  };
  const [showDeleteSuccess, setShowDeleteSuccess] = useState(false);
  const [paragraphCount, setParagraphCount] = useState<number>(3);
  const [isInputBoxAdaptable, setIsInputBoxAdaptable] = useState<boolean>(false)
  const pendingPromptRef = useRef<{
    input: string;
    guidelines: string | null;
    resend_flag: boolean;
    resend_message_id: string | null;
    old_responses_attachments: { responses: AssistantMessage[], attachments: Attachment[] } | null;
    target_session_id: string | null;
    timestamp: number | null;
  } | null>(null);
  const heartbeatRef = useRef<NodeJS.Timeout | null>(null);
  const lastPongRef = useRef<number>(Date.now());
  const reconnectAttemptRef = useRef(0);
  const urlSessionId = searchParams.get("session_id");
  const totalReconnectAttempts = useRef(0);
  const [showOfflineToast, setShowOfflineToast] = useState(false);
  const [reconnectTrigger, setReconnectTrigger] = useState<number>(0);
  const MAX_RECONNECT_TRIES = 5;
  const [openFullStoryView, setOpenFullStoryView] = useState<boolean>(false)
  const [storyData, setStoryData] = useState<StoryParagraph[]>([])
  const [userImages, setUserImages] = useState<{ image_url: string }[]>([])
  const router = useRouter()
  const [openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox] = useState<
    boolean
  >(false);

  const x = useMotionValue(0)
  const animationRef = useRef<ReturnType<typeof animate> | null>(null)

  const startAnimation = () => {
    animationRef.current = animate(x, -1000, {
      duration: 15,
      ease: "linear",
      repeat: Infinity,
      repeatType: "loop"
    })
  }

  useEffect(() => {
    const savedPrompt = localStorage.getItem("tadabbur_pending_prompt");
    if (savedPrompt) {
      try {
        const parsed = JSON.parse(savedPrompt);
        const isExpired = Date.now() - (parsed.timestamp || 0) > 3600000;

        if (isExpired) {
          console.log(" Pending prompt expired, clearing from storage.");
          localStorage.removeItem("tadabbur_pending_prompt");
        } else {
          pendingPromptRef.current = parsed;
          console.log(" Recovered a valid pending message.");
        }
      } catch (e) {
        localStorage.removeItem("tadabbur_pending_prompt");
      }
    }
  }, []);

  useEffect(() => {
    const handleOffline = () => {
      console.log("🌐 Browser report: Network is OFF");
      setConnectionStatus("disconnected");
    };
    type PendingDelete = { type: string; user_id: string | null; session_id?: string };

    const handleOnline = () => {
      console.log("🌐 Browser report: Network is ON");
      const pending: PendingDelete[] = JSON.parse(localStorage.getItem("tadabbur_pending_deletes") || "[]");
      if (pending.length > 0) {
        pending.forEach((op) => {
          wsSendAsync(wsRef.current, op);
        });
        localStorage.removeItem("tadabbur_pending_deletes");
        console.log("🗑️ Pending deletes executed after reconnection");
      }
      setConnectionStatus("connected");
      setReconnectTrigger(prev => prev + 1);
    };

    window.addEventListener("offline", handleOffline);
    window.addEventListener("online", handleOnline);

    return () => {
      window.removeEventListener("offline", handleOffline);
      window.removeEventListener("online", handleOnline);
    };
  }, []);

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

  useEffect(() => {
    const audioEl = audioRef.current;
    if (!audioEl) return;

    const handlePlay = () => {
      // update ref for centralized audio management
      if (currentPlayableAudio.current) {
        currentPlayableAudio.current.state = "playing"
      }
      console.log("Play fired!")
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
      console.log("Paused fired!")
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
      console.log("Ended fired!")
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
    if (inputRef.current) {
      inputRef.current.textContent = ""
      setShowPlaceholder(true)
    }
    setIsInputBoxAdaptable(false)
    setIsRecording(false)
    setIsTranscribing(false)
  }, [currentMode])

  useEffect(() => {
    const checkPersonalization = async () => {
      try {
        const token = localStorage.getItem("auth_token");
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
        console.log("📊 Personalization data received:", data);
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
    let reconnectTimeout: NodeJS.Timeout;
    const connect = () => {
      if (totalReconnectAttempts.current >= MAX_RECONNECT_TRIES) {
        console.log(" Max reconnect attempts reached. Waiting for manual user action.");
        setConnectionStatus("disconnected");
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) {
        console.error("No authentication token found. Cannot connect to chat.");
        return;
      }

      const websocket = new WebSocket(`${process.env.NEXT_PUBLIC_WEBSOCKET_URL}/ws/chat?token=${token}`);
      wsRef.current = websocket;
      websocket.onopen = async () => {
        reconnectAttemptRef.current = 0;
        totalReconnectAttempts.current = 0;
        const user = localStorage.getItem("user");

        try {
          if (typeof urlSessionId === 'string' && urlSessionId.length > 0) {
            console.log("Sending get_chat")
            await wsSendAsync(
              websocket, {
              type: "get_chat",
              session_id: urlSessionId,
            }, 8, 500)
          } else {
            const sessionID = generateSessionId()
            const sessionInit: SessionInitMessage = {
              type: "session-init",
              session_id: sessionID,
              mode: currentMode
            };
            console.log("Sending session init")
            await wsSendAsync(
              websocket,
              sessionInit,
              8,
              500
            );
          }

        } catch (error) {
          console.error("❌ Failed to initialize WebSocket session:", error);
          setConnectionStatus("disconnected");
        }
        setReportedMessageIDs([]);
      };

      wsRef.current.onclose = () => {
        if (heartbeatRef.current) {
          clearInterval(heartbeatRef.current);
          heartbeatRef.current = null;
        }
        setConnectionStatus("disconnected");
        totalReconnectAttempts.current += 1;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptRef.current), 30000);

        console.log(`❌ Socket closed. Retrying in ${delay / 1000}s...`);

        reconnectTimeout = setTimeout(() => {
          reconnectAttemptRef.current += 1;
          connect();
        }, delay);
      };

      wsRef.current.onerror = (error) => {
        console.log("An error occured in websocket", error);
        setConnectionStatus("disconnected");
        websocket.close();
      };


      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("Data from websocket", event.data);

        const type = data.type;

        const FAILED_STATUSES = new Set([
          "not-acknowledged",
          "not_acknowledged",
          "Not_acknowledged",
          "Not_acknowledeged",
          "error",
        ]);

        const SKIP_TYPES = new Set(["tts_audio_url", "get_images", "chat_history"]);

        if (data.status && FAILED_STATUSES.has(data.status) && !SKIP_TYPES.has(type)) {
          showFriendlyError(type);
          return;
        }

        switch (type) {
          case "pong":
            console.log("Pong received - connection alive");
            lastPongRef.current = Date.now();
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

          case "tts_audio_url":
            const tts_audio_status = data.status
            if (tts_audio_status === "acknowledged") {
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
            }

            break;

          case "session_id":
            // reset everything  
            audioRef?.current?.pause()
            setCurrentMode(null)
            setError(null)
            setMessages(prev =>
              prev.map(m =>
                m.message_id === currentPlayableAudio.current?.user_message_id
                  ? {
                    ...m,
                    responses: m.responses.map(n =>
                      n.message_id === currentPlayableAudio.current?.response_message_id
                        ? { ...n, audio_state: "ended" }
                        // nullify the rest
                        : { ...n, audio_state: null }
                    ),
                  }
                  : { ...m, responses: m.responses.map(b => ({ ...b, audio_state: null })) }
              )
            );
            const session_id = data.session_id;
            const session_status = data.status;
            const message_ids = data.message_ids;
            const session_mode: "story" | "normal" = data.mode || "normal"
            if (session_status === "acknowledged") {
              setSessionID(session_id);
              const currentUrlId = searchParams.get("session_id");
              if (!currentUrlId || currentUrlId === "" || currentMode != session_mode) {
                router.replace(`/pages/chatbot?session_id=${session_id}`, { scroll: false });
              } else {
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

          case "error":
            setMessages(prev => {
              const updated = [...prev];
              const lastMsg = updated[updated.length - 1];
              if (lastMsg && lastMsg.responses) {
                lastMsg.responses = lastMsg.responses.filter(r => r.content !== "");
              }
              return updated;
            });
            setLoading(false);
            setLoadingMessage(null);
            setIsGenerating(false);
            setError(data.message);
            break;

          case "chat_history":
            const chat_history = data.chat_history;
            const history_status = data.status;
            // handle chat history
            if (history_status === "acknowledged") {
              setChatHistory(chat_history);
            } else if (history_status === "error") {
              showFriendlyError("chat_history");
            }
            break;

          case "delete_session":
            const delete_status = data.status;
            if (delete_status === "acknowledged") {
              window.dispatchEvent(new CustomEvent("tadabbur-session-deleted", {
                detail: { session_id: data.session_id }
              }));

              const currentUrlSessionId = new URLSearchParams(window.location.search).get("session_id");
              if (currentUrlSessionId === data.session_id) {
                setMessages([]);
                setSessionID(null);
                setMessageIDs([]);
                setHidePromptExtraOptionsModelBoxArray([]);
                setLoading(false);
                setIsGenerating(false);

                const u = localStorage.getItem("user");
                let uid = null;
                try { uid = u ? JSON.parse(u).id : null; } catch { }
                const sessionID = generateSessionId()
                wsSendAsync(wsRef.current, {
                  type: "session-init",
                  session_id: sessionID,
                });
              }


              const user = localStorage.getItem("user");
              let user_id: string = "";

              try {
                const userData = JSON.parse(user || "{}");
                user_id = userData.id;
              } catch (e) {
                console.error("Error parsing user data:", e);
              }

              if (user_id) {
                wsSendAsync(wsRef.current, {
                  type: "chat_history",
                  user_id: user_id,
                });
              }
              setShowDeleteSuccess(true);
              setTimeout(() => setShowDeleteSuccess(false), 3000);
              type PendingDelete = { type: string; user_id: string | null; session_id?: string };
              const pending: PendingDelete[] = JSON.parse(localStorage.getItem("tadabbur_pending_deletes") || "[]");
              const updated = pending.filter((op) => op.session_id !== data.session_id);
              localStorage.setItem("tadabbur_pending_deletes", JSON.stringify(updated));

            }
            break;

          case "delete_all_sessions":
            const delete_all_status = data.status;
            if (delete_all_status === "success") {
              if (setOpenChatHistoryDialogueBox) setOpenChatHistoryDialogueBox(false);
              setChatHistory([]);
              window.dispatchEvent(new CustomEvent("tadabbur-all-sessions-deleted"));
              localStorage.removeItem("tadabbur_pending_deletes");

              setMessages([]);
              setSessionID(null);
              setMessageIDs([]);
              setHidePromptExtraOptionsModelBoxArray([]);
              router.push('/pages/chatbot', { scroll: false });

              wsSendAsync(wsRef.current, {
                type: "session-init",
                session_id: "",
              });
            }
            break;
          case "get_images":
            const get_image_status = data.status
            const images = data.images || []
            if (get_image_status != "acknowledged" || images.length <= 0) {
              break
            }
            setUserImages(images)
            setOpenImageContainer(true)
            break

          case "get_chat":
            setError(null)
            const status = data.status;
            if (status === "acknowledged") {
              // reset audio
              audioRef?.current?.pause()
              setMessages(prev =>
                prev.map(m =>
                  m.message_id === currentPlayableAudio.current?.user_message_id
                    ? {
                      ...m,
                      responses: m.responses.map(n =>
                        n.message_id === currentPlayableAudio.current?.response_message_id
                          ? { ...n, audio_state: "ended" }
                          // nullify the rest
                          : { ...n, audio_state: null }
                      ),
                    }
                    : { ...m, responses: m.responses.map(b => ({ ...b, audio_state: null })) }
                )
              );
              const mode: "story" | "normal" = data.mode;
              const messageIDs = data.unique_message_ids;
              const session_id = data.session_id
              const chat_history = groupChatMessages(data.chat_history);
              setMessages(chat_history);
              setMessageIDs(messageIDs);
              setSessionID(session_id)
              setConnectionStatus("connected")
              setCurrentMode(mode)
              setLoading(false);

              const saved = localStorage.getItem("tadabbur_pending_prompt");
              if (saved) {
                try {
                  const pendingData = JSON.parse(saved);
                  // Only auto-send if it belongs to this session or session is new
                  const isCorrectSession = !pendingData.target_session_id || pendingData.target_session_id === session_id;

                  if (isCorrectSession && pendingData.input) {
                    console.log("🚀 Connection restored. Sending pending prompt from localStorage...");
                    ask(
                      pendingData.input,
                      pendingData.guidelines,
                      pendingData.resend_flag,
                      pendingData.resend_message_id,
                      pendingData.old_responses_attachments,
                      true,
                      null
                    );

                    localStorage.removeItem("tadabbur_pending_prompt");
                    pendingPromptRef.current = null;
                  }
                } catch (e) {
                  console.error("Error processing pending prompt:", e);
                  localStorage.removeItem("tadabbur_pending_prompt");
                }
              }

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
            const assistant_response_status = data.status
            if (assistant_response_status === "acknowledged") {
              const reply: string = data.content.response ?? "No reply from server";
              const has_verse_audio: boolean = data.content.has_verse_audio || false
              const has_verse_image: boolean = data.content.has_verse_image || false
              const is_error: boolean = data.is_error || false;
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

                const targetIndex = reply_to_message_id
                  ? updated.findIndex((m) => m.message_id === reply_to_message_id)
                  : updated.length - 1;

                // If not found, return unchanged
                if (targetIndex === -1) {
                  console.warn("⚠️ Could not find target message for assistance_response, skipping");
                  return prev;
                }

                setStreamingMessageIndexSynced(targetIndex);

                const targetMessage = updated[targetIndex];

                // Check if already rendered with content
                const alreadyRendered = targetMessage.responses?.some(
                  (r) => r.message_id === message_id && r.content !== ""
                );
                if (alreadyRendered) return prev;

                if (!targetMessage.number_of_responses) {
                  targetMessage.number_of_responses = 1;
                } else {
                  targetMessage.number_of_responses += 1;
                }
                targetMessage.responses = oldMessagesRef.current ?? []
                targetMessage.responses.push({ role: "assistant", message_id: message_id, content: "", reply_to_message_id: reply_to_message_id, feedback: null, audio_link: null, audio_state: null, has_verse_audio: has_verse_audio, verse_audio_data: audio_data, has_verse_image: has_verse_image, verse_images: verse_images, is_error: is_error, story_data: story_data, clicked_feedback: [false, false] });
                targetMessage.active_message_index = targetMessage.number_of_responses - 1;

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
                      // console.log("Last User Message", lastMsg)
                      if (!lastMsg.responses || lastMsg.responses.length === 0) return prev;
                      const lastResIdx = (lastMsg.number_of_responses || 1) - 1;

                      updated[streamIndex].responses[lastResIdx].content =
                        (updated[streamIndex].responses[lastResIdx]?.content || "") +
                        chunk;
                      streamingContentRef.current = updated[streamIndex].responses[lastResIdx].content;
                    }
                    return updated;
                  });
                }
              })().then(() => {
                stopStreamRef.current = null;
                setStreamingMessageIndexSynced(null);
                setIsGenerating(false);
                currentStreamingMsgRef.current = null;
                streamingContentRef.current = "";
              });
            }
            break;

          case "stop_acknowledged":
            const stop_generation_status = data.status
            if (stop_generation_status === "acknowledged") {
              // reset states related to streaming
              setIsGenerating(false);
              setStreamingMessageIndexSynced(null);
              setLoading(false);
              currentStreamingMsgRef.current = null;
              streamingContentRef.current = "";
              break;
            }

          case "feedback":
            const feedback_status = data.status
            if (feedback_status === "acknowledged") {
              const message_id = data.message_id
              const feedback_type = data.feedback_type
              const reply_to_message_id = data.reply_to_message_id
              // add extra protection checks - even though not needed
              if (message_id && ["liked", "disliked"].includes(feedback_type) && reply_to_message_id) {
                setMessages((prev: ChatMessage[]) => {
                  return prev.map((m) =>
                    m.message_id === reply_to_message_id
                      ? {
                        ...m,
                        responses: m.responses.map((r) =>
                          r.message_id === message_id
                            ? { ...r, feedback: feedback_type, clicked_feedback: feedback_type === "liked" ? [false, r.clicked_feedback[1]] : [r.clicked_feedback[0], false] }
                            : r
                        )
                      }
                      : m
                  )
                }
                );
              }
            }
            break
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
            setParagraphCount(data.paragraph_count ?? 3);
            break;
          case "regenerate_required":
            const orphanMsgId = data.message_id;
            const orphanContent = data.content;

            if (orphanMsgId && orphanContent) {
              console.log("🔄 Regenerating orphaned message:", orphanMsgId);
              setTimeout(() => {
                streamingMessageIndexRef.current = null;
                setStreamingMessageIndex(null);
                setIsGenerating(false);
                setLoading(false);
                setMessages(prev => prev.filter(m => m.message_id !== orphanMsgId));

                ask(
                  orphanContent,
                  null,
                  false,
                  null,
                  null,
                  true,
                  orphanMsgId
                );
              }, 500);
            }
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
      }
    };

    connect();
    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onmessage = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };

  }, [reconnectTrigger]);

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
    setStreamingMessageIndexSynced(null);
    setLoading(false);

    wsSendAsync(wsRef.current, {
      type: "stop_generation",
      message_id: msgId,
      partial_content: partialContent,
    });

    currentStreamingMsgRef.current = null;
    streamingContentRef.current = "";
  };

  const showFriendlyError = (type: string) => {
    const messages: Record<string, string> = {
      session_id: "Couldn't load your session. Please refresh the page.",
      delete_session: "Session couldn't be deleted right now. Please try again.",
      delete_all_sessions: "Couldn't delete all sessions. Please try again.",
      "model-selection": "Model switch failed. Your previous model is still active.",
      report: "Report couldn't be submitted. Please try again.",
      "undo-report": "Couldn't undo the report. Please try again.",
      tts_audio_url: "Audio generation failed. The text response is still available.",
      get_images: "Couldn't load your images. Please try again later.",
      chat_history: "Couldn't load chat history. Please try again.",
      "session-init": "Couldn't switch to Story Mode. Please try again.",
      default: "Something went wrong on our end. Please try again in a moment.",
    };

    setServerErrorToast(messages[type] ?? messages.default);
    setTimeout(() => setServerErrorToast(null), 4000);
  };

  const ask = async (
    input: string,
    guidelines: string | null = null,
    resend_flag: boolean = false,
    resend_message_id: string | null = null,
    old_responses_attachments: { responses: AssistantMessage[], attachments: Attachment[] } | null = null,
    bypassCheck: boolean = false,
    message_id: string | null = null
  ) => {
    if (streamingMessageIndexRef.current !== null || (!input.trim() && !fileContext)) return;

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
      messageID = message_id || generateUUID();
      while (messageIDs?.includes(messageID)) {
        messageID = generateUUID();
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
        attachments_array.push({ attachmentName: attachedFile.name, attachmentType: attachedFile.type })
      }
      // Reset file states
      setAttachedFile(null);

    }
    if (connectionStatus !== "connected" && !bypassCheck) {
      console.log("📡 Socket not ready. Saving prompt to pending queue.");
      const pendingData = {
        input,
        guidelines,
        resend_flag,
        resend_message_id: messageID,
        old_responses_attachments,
        target_session_id: urlSessionId,
        timestamp: Date.now()
      };
      pendingPromptRef.current = pendingData;
      try {
        localStorage.setItem("tadabbur_pending_prompt", JSON.stringify(pendingData));
        console.log("prompt saved to pending queue:", pendingData);
      } catch (error) {
        console.warn("⚠️ Some error occured while saving prompt to local Storage, message only saved in memory:", error);
      }
      setShowOfflineToast(true);
      setTimeout(() => setShowOfflineToast(false), 4000);
      return;
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
          clicked_feedback: [false, false]
        },
      ],
    };
    oldMessagesRef.current = resend_flag ? old_responses_attachments?.responses ?? [] : [];

    setMessages((prev) => {
      const isExisting = prev.some(m => m.message_id === messageID);
      if (isExisting) {
        return prev;
      }
      const updated = [...(prev || []), userMessage];
      setStreamingMessageIndexSynced(updated.length - 1);
      return updated;
    });
    if (currentMode === "story") {
      setIsInputBoxAdaptable(false)
    }
    currentMessageIDRef.current = messageID;

    try {
      await wsSendAsync(wsRef.current, {
        type: "user_message",
        message_id: messageID,
        role: "user",
        system_instructions: guidelines || "",
        content: input,
        resend_flag: resend_flag,
        resend_message_id: resend_message_id || "",
        new_file_context: fileContext ?? "",
        file_name: attachedFile?.name ?? null,
        file_type: attachedFile?.type ?? null,
      });
      localStorage.removeItem("tadabbur_pending_prompt");
      setFileContext(null);
      if (inputRef.current) {
        inputRef.current.innerText = "";
        setShowPlaceholder(true);
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      setConnectionStatus("disconnected");
      // Also save to pending if the actual send fails
      const pendingData = {
        input, guidelines, resend_flag, resend_message_id, old_responses_attachments,
        target_session_id: urlSessionId,
        timestamp: Date.now()
      };
      pendingPromptRef.current = pendingData;
      localStorage.setItem("tadabbur_pending_prompt", JSON.stringify(pendingData));
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

  const manageInputHeight = (boxHeight: number, inputText: string) => {

    if (boxHeight > 24 && !isInputBoxAdaptable) {
      setIsInputBoxAdaptable(true)

    }
    else if (inputText === "" && isInputBoxAdaptable) {

      setIsInputBoxAdaptable(false)
    }
  }

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
      {showPersonalizationForm ? (
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
      ) : (
        <motion.div
          animate={{
            background: currentMode === "normal"
              ? "#F9FAFB"
              : "#000000",
          }}
          transition={{ duration: 0.3 }}
          className="relative w-screen h-svh flex flex-col justify-center items-center overflow-hidden">
          {/* --- UI STATUS INDICATOR --- */}
          <AnimatePresence>
            {showDeleteSuccess && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="fixed top-10 left-1/2 -translate-x-1/2 bg-emerald-700 text-white text-[0.75rem] switzer-600 px-4 py-2 rounded-full shadow-xl z-9999 whitespace-nowrap flex items-center gap-2"
              >
                Session Deleted Successfully
              </motion.div>
            )}
          </AnimatePresence>
          <div className="fixed top-4 right-4 z-9999 flex flex-col items-end gap-y-2 pointer-events-none">
            <AnimatePresence mode="wait">
              {connectionStatus === "disconnected" && (
                <motion.span
                  key="offline"
                  initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="bg-red-500 text-white px-3 py-1.5 rounded-full text-[0.7rem] switzer-600 shadow-lg animate-pulse"
                >
                  OFFLINE - TRYING TO RECONNECT
                </motion.span>
              )}
              {showOfflineToast && (
                <motion.div
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  className="fixed bottom-24 z-100 bg-amber-100 border border-amber-300 text-amber-900 px-4 py-3 rounded-lg shadow-xl flex items-center gap-3"
                >
                  <div className="bg-amber-500 text-white rounded-full p-1">
                    <UndoArrow className="w-4 h-4 rotate-180" />
                  </div>
                  <p className="switzer-500 text-sm">
                    {"You're offline check your network connection ! "}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>


            <AnimatePresence>
              {serverErrorToast && (
                <motion.div
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="fixed top-10 left-1/2 -translate-x-1/2 z-9999 bg-red-50 border border-red-200 text-red-800 text-[0.75rem] switzer-600 px-4 py-2 rounded-full shadow-xl whitespace-nowrap flex items-center gap-2"
                >
                  <span>⚠️</span>
                  <p>{serverErrorToast}</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <ChatProvider
            chatHistory={chatHistory}
            setChatHistory={setChatHistory}
            wsRef={wsRef}
            inputRef={inputRef}
            sessionID={sessionID}
            attachedFile={attachedFile}
            setAttachedFile={setAttachedFile}
            messages={messages}
            setMessages={setMessages}
            audioRef={audioRef}
            ask={ask}
            currentPlayableAudio={currentPlayableAudio}
            hideReportContentDialogueBox={hideReportContentDialogueBox}
            openChatHistoryDialogueBox={openChatHistoryDialogueBox}
            setOpenChatHistoryDialogueBox={setOpenChatHistoryDialogueBox}
            setHideReportContentDialogueBox={setHideReportContentDialogueBox}
            hidePromptExtraOptionsModelBoxArray={hidePromptExtraOptionsModelBoxArray}
            setHidePromptExtraOptionsModelBoxArray={setHidePromptExtraOptionsModelBoxArray}
            active={active}
            setActive={setActive}
            currentMode={currentMode}
            setCurrentMode={setCurrentMode}
            setOpenFullStoryView={setOpenFullStoryView}
            setStoryData={setStoryData}
            openStoryModeExtraOptions={openStoryModeExtraOptions}
            setOpenStoryModeExtraOptions={setOpenStoryModeExtraOptions}
            isUploading={isUploading}
            fileContext={fileContext}
            stopGeneration={stopGeneration}
            showPlaceholder={showPlaceholder}
            isGenerating={isGenerating}
            setOpenImageContainer={setOpenImageContainer}
          >

            <AnimatePresence>
              {openChatHistoryDialogueBox && (
                <ChatHistoryCupboard />
              )}
            </AnimatePresence>
            <AnimatePresence>
              {openFullStoryView && (
                <FullViewStoryContainer story_data={storyData} />
              )}
            </AnimatePresence>


            <div className={`w-full flex flex-col items-center relative ${currentMode === "normal" ? "" : "black-scrollbar"} ${messages.length > 0 ? "h-full" : " justify-center"} overflow-y-auto`}>

              {/* navbar for top options background */}
              <div id="navbar" style={{ backgroundColor: currentMode === "normal" ? "#F9FAFB99" : "#00000099" }} className={`fixed top-0 w-[98%] z-20 h-14 flex items-center shrink-0 backdrop-blur-md border-b ${currentMode === "normal" ? "border-black/5" : "border-white/10"} ${messages.length > 0 ? "pr-2 pl-4" : "px-2"}`}>
                <div className="mr-4 z-40">
                  <HamBurger wsRef={wsRef} openChatHistoryDialogueBox={openChatHistoryDialogueBox} setOpenChatHistoryDialogueBox={setOpenChatHistoryDialogueBox} currentMode={currentMode} />
                </div>
                <div className="ml-auto">
                  {currentMode === "story" ? (
                    <Image className="w-16 h-auto object-cover object-center" src={TadabburFontWhite}
                      alt="tadabbur-font-white" />
                  ) : (<Image className="w-16 h-auto object-cover object-center" src={TadabburFontBlack}
                    alt="tadabbur-font-black" />)}
                </div>

              </div>

              <div
                id="chat-bot"
                className={`w-full ${messages && messages?.length > 0 ? "h-max" : "items-center"} mt-16 px-4 lg:w-2/3 flex flex-col gap-y-4 ${!messages ? "justify-center" : ""}`}
              >
                <AnimatePresence>

                  {messages?.length === 0 && (
                    <motion.div
                      className="w-full flex flex-col gap-y-4 items-center self-center"
                    >
                      {currentMode === "story" && (
                        <motion.div whileHover={{ backgroundColor: "#ffffff0d" }} className="w-max py-2 px-4 rounded-full border border-white/10 cursor-pointer flex items-center gap-x-1 scale-90 sm:scale-100">
                          <div className="rounded-md py-0.5 px-1 shadow-md bg-red-400 flex justify-center items-center mr-1">
                            <span className="poppins-semibold text-[0.5rem] text-white">NEW</span>
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
                        className={`text-center px-6 ${currentMode === "normal" ? "switzer-500 tracking-tight text-4xl" : "inter-600 text-[2.6rem] sm:text-[2.8rem] tracking-tighter lg:text-[3.2rem] leading-9 lg:leading-11 subpixel-antialiased"}`}
                      >
                        {currentMode === "story" ? (
                          <>
                            QURANIC STORIES EXPLAINED WITH <span className="text-cyan-300">POWERFUL</span>,
                            <span className="flex gap-x-1 justify-center items-center text-green-300"><span className="rounded-full border-2 border-dotted border-red-400 p-1.5"><EngagingIcon className="md:w-10 md:h-10 w-8 h-8" /></span> CREATIVE</span> VISUALS.
                          </>
                        ) : (
                          greeting
                        )}
                      </motion.p>

                      {currentMode === "story" && (
                        <div ref={constraintRefStoryMode} id="default-prompts-box-story" className="w-full relative overflow-x-clip">
                          <motion.div
                            style={{ x }}
                            drag="x"
                            dragConstraints={constraintRefStoryMode}
                            onMouseEnter={() => animationRef.current?.pause()}
                            onMouseLeave={() => animationRef.current?.play()}
                            onViewportEnter={startAnimation}

                            className="w-max flex gap-x-2">
                            {Array.from({ length: 3 }).map((_, i) => (
                              <motion.div key={i} id="carousel-default-prompts-story" className="w-1/2">
                                <div className="grid grid-cols-4 grid-rows-1 gap-x-4 w-full">
                                  {defaultPromptsStoryMode.map((record, index) => {
                                    return (
                                      <motion.div key={index} whileHover={{ scale: 1.02 }} transition={{ duration: 0.5, ease: easeInOut }}
                                        onClick={() => {
                                          ask(
                                            `${record.prompt}`,
                                          );
                                        }} className="cursor-pointer w-max flex flex-row gap-x-3 sm:flex-col gap-y-1 p-2 rounded-lg border border-white/10 shadow-sm">
                                        <Image className="rounded-md sm:w-36 sm:h-34 w-30 h-28 object-cover object-top" alt="smiling-boy" src={record.imageSrc} />

                                        <p className="w-45 sm:hidden switzer-500 text-white/80">{record.prompt}</p>
                                        <p className="hidden w-36 sm:block switzer-500 text-white/80">{record.shortPrompt}</p>

                                      </motion.div>
                                    )
                                  })}
                                </div>
                              </motion.div>
                            ))}

                          </motion.div>
                        </div>
                      )}
                      {currentMode === "normal" && (
                        <div ref={constraintRefNormalMode} className="default-prompts-box-normal w-full relative overflow-x-clip">
                          <motion.div
                            drag="x"
                            dragConstraints={constraintRefNormalMode}
                            animate={controls}
                            transition={{
                              duration: 25,
                              ease: easeInOut,
                              repeat: Infinity,
                              repeatType: "loop",
                            }}
                            onMouseOver={() => {
                              controls.stop();
                            }}
                            onMouseLeave={() => {
                              controls.start({ x: "-60%" });
                            }}
                            className="w-[1200%] md:w-[600%] flex gap-x-2"
                          >
                            {Array.from({ length: 3 }).map((_, i) => (
                              <motion.div key={i} id="carousel-default-prompts-normal" className="carousel w-1/2">
                                <div className="carousel-controls-slider flex">
                                  <div
                                    className="h-max grid grid-cols-6 grid-rows-1 rounded-md gap-4 w-full">
                                    {defaultPromptsNormalMode.map((prompt, index) => (
                                      <motion.div
                                        key={index}
                                        whileHover={{ scale: 1.01 }}
                                        transition={{
                                          duration: 0.5,
                                          ease: easeInOut,
                                        }}

                                        onClick={() => {
                                          ask(
                                            `${prompt.title} ${prompt.description}`,
                                          );
                                        }}
                                        className="bg-white rounded-md shadow-sm backdrop-blur-md cursor-pointer"
                                      >
                                        <div className="w-full flex flex-col px-3 pt-3 pb-4 gap-y-1">
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
                  {messages && messages.length > 0 && (
                    messages.map((record, record_index) => {
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
                            <p className={`ml-auto w-max min-w-40 wrap-break-word max-w-[20rem] rounded-md switzer-500 py-2 shadow-md px-3 text-white ${currentMode === "normal" ? "border bg-neutral-900 border-black/5" : "bg-linear-to-b from-[#570900] to-[#8A0F00]"}`}>
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
                              <div key={ai_msg_idx}
                                className="px-3">
                                <motion.div
                                  animate={{ scale: [1, 1.2, 1] }}
                                  transition={{
                                    duration: 0.4,
                                    ease: easeInOut,
                                    repeat: Infinity,
                                    repeatType: "loop",
                                  }}
                                  className={`w-3 h-3 rounded-full ${currentMode === "normal" ? "bg-black" : "bg-white"}`}
                                ></motion.div>
                              </div>
                            ) : loadingMessage && !ai_msg.content ? (
                              <div key={ai_msg_idx} className="flex flex-col gap-y-2 mt-2 px-1">
                                <div className={`flex items-center animate-pulse ${currentMode === "normal" ? "text-black/40" : "text-white/60"} sm:scale-105 md:scale-110`}>
                                  <p className={`switzer-500 text-sm `}>{loadingMessage}</p>
                                  <motion.div initial={{ x: 0 }} animate={{ x: 20 }} transition={{ duration: 1, ease: "linear", repeat: Infinity }} className="ml-2 mb-[2px]">
                                    <ArrowLeft className="-rotate-180 w-3 h-3 fill-current" />
                                  </motion.div>
                                </div>
                                {ai_msg.story_data?.length > 0 && (
                                  Array.from({ length: paragraphCount }).map((_, i) => (
                                    <div key={i} className="flex flex-col gap-y-3">
                                      <div className="h-4 w-36 rounded-md bg-linear-to-r from-white/5 via-white/15 to-white/5 animate-pulse" />
                                      <div className="flex flex-col gap-y-2">
                                        <div className="h-3 w-full rounded-md bg-linear-to-r from-white/5 via-white/15 to-white/5 animate-pulse" />
                                        <div className="h-3 w-[85%] rounded-md bg-linear-to-r from-white/5 via-white/15 to-white/5 animate-pulse" />
                                        <div className="h-3 w-[70%] rounded-md bg-linear-to-r from-white/5 via-white/15 to-white/5 animate-pulse" />
                                      </div>
                                      <div className="w-[80%] sm:w-[50%] md:w-[45%] lg:w-[30%] h-auto aspect-video rounded-md bg-linear-to-br from-white/5 via-white/10 to-white/5 animate-pulse border border-white/5" />
                                    </div>
                                  ))
                                )}
                              </div>
                            ) : reportedMessageIDs &&
                              !reportedMessageIDs.includes(ai_msg?.message_id) &&
                              ai_msg_idx === record.active_message_index ? (
                              <div key={ai_msg_idx}>
                                <div className={`w-max min-w-40 max-w-full switzer-500 mt-2 rounded-md px-3 ${ai_msg.is_error
                                  ? "bg-red-50 border border-red-200 py-2"
                                  : currentMode === "normal"
                                    ? "bg-white shadow-md py-2"
                                    : ""
                                  }`}>
                                  <Markdown textContent={ai_msg.content} isError={ai_msg.is_error} />
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
                      )
                    })
                  )}

                </AnimatePresence >

                <div ref={messagesEndRef}></div>

              </div >

            </div >

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
                  <div className={`${currentMode === "normal" ? "bg-white/90" : "bg-black shadow-sm shadow-red-500"} backdrop-blur-sm border ml-auto border-black/5 shadow-lg rounded-full px-4 py-3 flex items-center gap-x-3`}>
                    <div className={`w-4 h-4 border-2 ${currentMode === "normal" ? "border-black/20" : "border-white"} border-t-black rounded-full animate-spin`}></div>
                    <p className={`switzer-500 text-sm ${currentMode === "normal" ? "text-black/80" : "text-white"}`}>Transcribing audio</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full lg:w-2/3 px-4"
              >
                <p className="text-red-500 switzer-500 text-sm">{error}</p>
              </motion.div>
            )}
            <motion.div animate={{ paddingTop: currentMode === "normal" ? 16 : 20, paddingBottom: currentMode === "normal" ? 16 : 28 }} className={`mx-1.5 px-4 h-max ${currentMode === "normal" ? "w-full lg:w-2/3 mt-4" : "w-full sm:w-[70%] lg:w-1/2 mt-2 flex flex-col gap-x-2 items-center"} input-box`}>
              <motion.div
                className={`relative shadow-md border gap-x-1 ${currentMode === "normal"
                  ? `${attachedFile ? "h-[200px]" : `h-40`} flex bg-white rounded-lg shadow-md border-black/10 px-3 py-2 flex-col`
                  : `h-auto bg-[##001e1e] border border-white/15 shadow-md w-full ${isInputBoxAdaptable ? "flex-col rounded-lg py-3 px-2" : "flex justify-center items-center rounded-full p-1"}`
                  }`}
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
                  <AnimatePresence>
                    {openStoryModeExtraOptions && (
                      <StoryModeExtraOptions />
                    )}
                  </AnimatePresence>
                )}
                {currentMode === "story" && !isInputBoxAdaptable && (
                  <motion.div onClick={() => {
                    setOpenStoryModeExtraOptions(prev => !prev)
                  }} whileHover={{ backgroundColor: "#FFFFFF1A" }} className="p-2 rounded-full cursor-pointer">
                    <PlusIcon className="w-5.5 h-5.5" />
                  </motion.div>
                )}
                <div
                  ref={inputRef}
                  onInput={(e) => {
                    const target = e.target as HTMLDivElement;
                    const text = target.textContent.trim() ?? "";
                    setShowPlaceholder(text === "");
                    if (inputRef.current && currentMode === "story") {
                      const newHeight = inputRef.current.scrollHeight ?? 24
                      manageInputHeight(newHeight, text)

                    }
                  }}
                  onKeyDown={(e) => {
                    handleInput(e);
                  }}
                  contentEditable
                  className={`switzer-500 focus:outline-none w-full ${currentMode === "normal" ? attachedFile ? "pt-[0.3rem] text-black h-2/3 overflow-y-auto" : "text-black h-full overflow-y-auto" : "text-white pt-[0.02rem] overflow-hidden max-h-[100px]"}`}
                ></div>
                {showPlaceholder && (
                  <span
                    className={`absolute ${currentMode === "normal" ? attachedFile ? "top-16 text-black" : "top-2 text-black" : "top-1.8 text-white/70 left-12 text-[15px]"} pointer-events-none placeholder-input-box switzer-500`}
                  >
                    {placeholder}
                  </span>
                )}
                <div className={`transition-opacity duration-300 ${connectionStatus !== "connected" ? "pointer-events-none opacity-50" : "opacity-100"}`}>
                  {currentMode === "normal" && (
                    <>
                      <BottomOptions />
                      <ExtraOptions />
                      {/* <ModelBox modelList={ModelList} /> */}
                    </>
                  )}
                  {currentMode === "story" && !isInputBoxAdaptable ? (
                    <div className="flex items-center gap-x-1 mr-1.5">
                      <MicStoryMode />
                      {isGenerating ? (
                        <button
                          onClick={stopGeneration}
                          className="flex items-center gap-x-2 w-5 h-5 p-1.5 bg-white/80 opacity-75 hover:opacity-100 rounded-xs transition-colors cursor-pointer"
                        >
                          <div className="w-2 h-2 bg-black"></div>
                        </button>
                      ) : (
                        <motion.div onClick={sendPrompt} style={{ cursor: showPlaceholder ? "default" : "pointer" }} initial={{ backgroundColor: "#FFFFFFCC" }} animate={{ backgroundColor: showPlaceholder ? "#FFFFFFCC" : "#ffffff" }} className="p-2 rounded-full scale-90">
                          <SendIcon className="w-5.5 h-5.5 fill-current text-black" />
                        </motion.div>
                      )}

                    </div>
                  ) : currentMode === "story" && isInputBoxAdaptable ? (
                    <div className="flex mt-2">
                      <motion.div onClick={() => {
                        setOpenStoryModeExtraOptions(prev => !prev)
                      }} whileHover={{ backgroundColor: "#FFFFFF1A" }} className="p-2 rounded-full cursor-pointer">
                        <PlusIcon className="w-5.5 h-5.5" />
                      </motion.div>
                      <AnimatePresence>
                        {openStoryModeExtraOptions && (
                          <StoryModeExtraOptions />
                        )}
                      </AnimatePresence>
                      <div className="ml-auto flex gap-x-1 items-center mr-1.5">
                        <MicStoryMode />
                        {isGenerating ? (
                          <button
                            onClick={stopGeneration}
                            className="flex items-center gap-x-2 w-5 h-5 p-1.5 bg-white/80 opacity-75 hover:opacity-100 rounded-sm transition-colors cursor-pointer"
                          >
                            <div className="w-2 h-2 bg-black"></div>
                          </button>
                        ) : (
                          <motion.div onClick={sendPrompt} style={{ cursor: showPlaceholder ? "default" : "pointer" }} initial={{ backgroundColor: "#FFFFFFCC" }} animate={{ backgroundColor: showPlaceholder ? "#FFFFFFCC" : "#ffffff" }} className="p-2 rounded-full scale-90">
                            <SendIcon className="w-5.5 h-5.5 fill-current text-black" />
                          </motion.div>
                        )}
                      </div>
                    </div>
                  )
                    : (null)}
                </div>
              </motion.div>

            </motion.div>
            <AnimatePresence>
              {openImageContainer && (
                <ImageContainer images={userImages} />
              )}
            </AnimatePresence>

            <AnimatePresence>
              {!hideReportContentDialogueBox && (
                <ReportContentDialogueBox
                  hideReportContentDialogueBox={hideReportContentDialogueBox}
                  setHideReportContentDialogueBox={setHideReportContentDialogueBox}
                />
              )}
            </AnimatePresence>

            <audio className="hidden" controls ref={audioRef} />
          </ChatProvider >
        </motion.div >
      )
      }
    </ProtectedRoute >
  )
}

export default function ChatPage() {
  return (
    <Suspense>
      <ChatContent />
    </Suspense>
  )
}




