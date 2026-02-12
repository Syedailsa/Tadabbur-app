"use client";
export const dynamic = "force-dynamic";
import type React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { useEffect, useRef, useState, CSSProperties, ReactNode, HTMLAttributes, Suspense } from "react";
import ChatProvider from "@/app/providers/chatbot/ChatProvider";
import DisclaimerIcon from "../../../icons/disclaimer.svg";
import CrossIcon from "../../../icons/cross_icon.svg"
import TextFileIcon from "../../../icons/text-file-icon.svg"
import PdfFileIcon from "../../../icons/pdf-file-icon.svg"
import UndoArrow from "../../../icons/refresh.svg";
import { AssistantMessage, Attachment } from "@/app/components/chatbot/interfaces/ChatMessage";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
    motion,
    easeInOut,
    AnimatePresence,
    useAnimationControls,
} from "framer-motion";
import ProtectedRoute from "@/app/utils/ProtectedRoutes";
import RegistrationForm from "@/app/components/chatbot/UI/ReactForm";
import { ModelList } from "@/static/data";
import BottomOptions from "../../components/chatbot/UI/BottomOptions";
import ExtraOptions from "../../components/chatbot/UI/ExtraOptions";
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
import groupChatMessages from "@/utils/groupChatMessages";
import WaveForm from "../../components/chatbot/UI/WaveForm";
import hidePromptExtraOptionsModelBoxArray from "@/app/components/chatbot/interfaces/hidePromptExtraOptionsModelBoxArray";
import { useRouter, useSearchParams } from "next/navigation";
import {
    SessionInitMessage,
    ChatRecordType,
} from "../../utils/types";


export default function ChatPage() {
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
        "Let's learn about the Quran",
    );
    const draculaTheme = dracula as { [key: string]: CSSProperties };
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
    const searchParams = useSearchParams()
    const oldMessagesRef = useRef<AssistantMessage[]>([]);
    const controls = useAnimationControls();
    const [hidePromptExtraOptionsModelBoxArray, setHidePromptExtraOptionsModelBoxArray] =
        useState<hidePromptExtraOptionsModelBoxArray[]>([]);

    const router = useRouter()

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
        const playableAudio = currentPlayableAudio.current
        if (!audioEl || !playableAudio) return;

        const handlePlay = () => {
            // update ref for centralized audio management
            if (playableAudio) {
                playableAudio.state = "playing"
            }
            setMessages(prev =>
                prev.map(m =>
                    m.message_id === playableAudio?.user_message_id
                        ? {
                            ...m,
                            responses: m.responses.map(n =>
                                n.message_id === playableAudio?.response_message_id
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
            if (playableAudio) {
                playableAudio.state = "paused"
            }
            setMessages(prev =>
                prev.map(m =>
                    m.message_id === playableAudio?.user_message_id
                        ? {
                            ...m,
                            responses: m.responses.map(n =>
                                n.message_id === playableAudio?.response_message_id
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
            if (playableAudio) {
                playableAudio.state = "ended"
            }
            setMessages(prev =>
                prev.map(m =>
                    m.message_id === playableAudio?.user_message_id
                        ? {
                            ...m,
                            responses: m.responses.map(n =>
                                n.message_id === playableAudio?.response_message_id
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
                    m.message_id === playableAudio?.user_message_id
                        ? {
                            ...m,
                            responses: m.responses.map(n =>
                                n.message_id === playableAudio?.response_message_id
                                    ? { ...n, audio_state: null }
                                    : n
                            ),
                        }
                        : m
                )
            );
        };
    }, [audioRef]);


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
                    // console.log("❌ No token found, showing personalization form");
                    setIsCheckingPersonalization(false);
                    setShowPersonalizationForm(true);
                    return;
                }

                // console.log("🔍 Checking personalization status with token...");

                // Backend se personalization status check karo
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

                const data = await response.json();
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

        websocket.onopen = () => {
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
            };

            if (websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify(sessionInit));

                if (urlSessionId) {
                    websocket.send(JSON.stringify({
                        type: "get_chat",
                        session_id: urlSessionId,
                        user_id: user_id,
                    }));
                }
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
            // console.log("Data from websocket", event.data);

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
                    const session_id = data.session_id;
                    const session_status = data.status;
                    const message_ids = data.message_ids;
                    if (session_status === "acknowledged") {
                        setSessionID(session_id);
                        const currentUrlId = searchParams.get("session_id");
                        if (!currentUrlId || currentUrlId === "") {
                            router.push(`/pages/chatbot?session_id=${session_id}`, { scroll: false });
                        }
                        setMessages([]);
                        setMessages((prevMessages) => {
                            if (prevMessages && prevMessages.length > 0) {
                                return [];
                            }
                            return prevMessages; // Return unchanged if no messages
                        });
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
                            wsRef.current?.send(
                                JSON.stringify({
                                    type: "chat_history",
                                    user_id: user_id,
                                }),
                            );
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
                    if (status === "acknowledged") {
                        const messageIDs = data.unique_message_ids;
                        const session_id = data.session_id
                        const chat_history = groupChatMessages(data.chat_history);
                        setMessages(chat_history);
                        setMessageIDs(messageIDs);

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
                                verse_images: verse_images
                            });

                            // set the number of active message index
                            lastUserMessage.active_message_index =
                                lastUserMessage.number_of_responses - 1;
                        }

                        return updated;
                    });


                    setLoading(false);
                    setLoadingMessage(null);
                    const tokens = reply.split(/(\s+)/);

                    (async () => {
                        for (let i = 0; i < tokens.length; i += 4) {
                            const chunk = tokens.slice(i, i + 4).join("");

                            await new Promise((resolve) => setTimeout(resolve, 2));

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
                    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/upload`, {
                        method: "POST",
                        body: formData,
                    });

                    if (!response.ok) throw new Error("Upload failed");

                    const data = await response.json();

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
    }, [fileContext, isUploading, attachedFile, sessionID]);

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
                    verse_images: []
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
        try {
            wsRef.current?.send(
                JSON.stringify({
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
                })
            );
            setFileContext(null);

            if (inputRef.current) {
                inputRef.current.innerText = "";
                setShowPlaceholder(true);
            }
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("Something went wrong");
            }
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

    useEffect(() => {
        if (messageScrollFlag.current) return;
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        messageScrollFlag.current = true;
    }, [messages]);

    useEffect(() => {
        controls?.start({
            x: "-60%",
        });
    }, [controls]);


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
                        audioRef={audioRef}
                        ask={ask}
                        currentPlayableAudio={currentPlayableAudio}
                        hideReportContentDialogueBox={hideReportContentDialogueBox}
                        setHideReportContentDialogueBox={setHideReportContentDialogueBox}
                        hidePromptExtraOptionsModelBoxArray={hidePromptExtraOptionsModelBoxArray}
                        setHidePromptExtraOptionsModelBoxArray={setHidePromptExtraOptionsModelBoxArray}
                    >
                        <ChatHisoryDialogueBox />

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
                                id="chat-box-messages"
                                className={`w-full ${messages && messages?.length > 0 ? "h-max" : "h-full"} px-4 mt-12 lg:w-2/3 flex flex-col gap-y-4 ${!messages ? "justify-center items-center" : ""}`}
                            >
                                <AnimatePresence>
                                    {messages?.length === 0 && (
                                        <motion.div
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
                                                    <p className="ml-auto w-max min-w-40 max-w-[20rem] bg-neutral-900 text-white switzer-500 py-2 px-3 rounded-md shadow-md border border-black/5">
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
                                                                        h1: ({ ...props }) => (
                                                                            <h1
                                                                                className="text-3xl font-bold"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        h2: ({ ...props }) => (
                                                                            <h2
                                                                                className="text-2xl font-semibold"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        h3: ({ ...props }) => (
                                                                            <h3
                                                                                className="text-xl font-semibold"
                                                                                {...props}
                                                                            />
                                                                        ),

                                                                        // PARAGRAPH
                                                                        p: ({ ...props }) => (
                                                                            <p
                                                                                className="leading-7 my-2 text-gray-800"
                                                                                {...props}
                                                                            />
                                                                        ),

                                                                        // STRONG ( **bold** )
                                                                        strong: ({ ...props }) => (
                                                                            <strong
                                                                                className="font-bold text-black"
                                                                                {...props}
                                                                            />
                                                                        ),

                                                                        // EMPHASIS ( *italic* )
                                                                        em: ({ ...props }) => (
                                                                            <em
                                                                                className="italic text-gray-700"
                                                                                {...props}
                                                                            />
                                                                        ),

                                                                        // LINE BREAK
                                                                        br: () => <br />,

                                                                        // LINKS
                                                                        a: ({ ...props }) => (
                                                                            <a
                                                                                className="text-blue-600 underline"
                                                                                target="_blank"
                                                                                rel="noreferrer"
                                                                                {...props}
                                                                            />
                                                                        ),

                                                                        // LISTS
                                                                        ul: ({ ...props }) => (
                                                                            <ul
                                                                                className="list-disc pl-6"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        ol: ({ ...props }) => (
                                                                            <ol
                                                                                className="list-decimal pl-6"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        li: ({ ...props }) => (
                                                                            <li className="my-1" {...props} />
                                                                        ),
                                                                        blockquote: ({ ...props }) => (
                                                                            <blockquote
                                                                                className="border-l-4 border-gray-400 pl-4 italic my-3"
                                                                                {...props}
                                                                            />
                                                                        ),

                                                                        // HORIZONTAL RULE
                                                                        hr: () => (
                                                                            <hr className="my-4 border-gray-300" />
                                                                        ),
                                                                        table: ({ ...props }) => (
                                                                            <div className="overflow-x-auto my-4 border border-black/20 rounded-lg shadow-sm">
                                                                                <table className="min-w-full divide-y divide-gray-200" {...props} />
                                                                            </div>
                                                                        ),
                                                                        thead: ({ ...props }) => (
                                                                            <thead
                                                                                className="bg-gray-50"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        tbody: ({ ...props }) => (
                                                                            <tbody
                                                                                className="bg-white divide-y divide-gray-200"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        tr: ({ ...props }) => (
                                                                            <tr
                                                                                className="hover:bg-gray-50"
                                                                                {...props}
                                                                            />
                                                                        ),
                                                                        th: ({ ...props }) => (
                                                                            <th className="px-4 py-3 text-left text-sm font-medium text-black uppercase tracking-wider border-b" {...props} />
                                                                        ),
                                                                        td: ({ ...props }) => (
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
                                                                                // Extract only the props that SyntaxHighlighter accepts
                                                                                const { style: _, ...syntaxProps } = props;

                                                                                return (
                                                                                    <SyntaxHighlighter
                                                                                        style={dracula as { [key: string]: CSSProperties }}
                                                                                        language={match[1]}
                                                                                        PreTag="div"
                                                                                        className="rounded-md shadow-sm my-4"
                                                                                        {...syntaxProps}
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
                                                            {/* Place it here, inside the div */}
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

                                                            {ai_msg.has_verse_audio && ai_msg.verse_audio_data.length > 0 && streamingMessageIndex != record_index && (
                                                                <QuranDialogBox
                                                                    type="audio"
                                                                    surahs={ai_msg?.verse_audio_data}
                                                                />
                                                            )}
                                                            <br />
                                                            {ai_msg.has_verse_image && ai_msg.verse_images.length > 0 && streamingMessageIndex != record_index && (
                                                                <QuranDialogBox
                                                                    type="read"
                                                                    surahs={ai_msg?.verse_images}
                                                                />
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
                                                                            }),
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

                        <div className="mr-1.5 py-4 mt-4 px-4 rounded-md w-full lg:w-2/3 input-box">
                            <motion.div
                                animate={{ height: attachedFile ? 200 : 160 }}
                                transition={{ duration: 0.2, ease: easeInOut }}
                                className={`flex flex-col relative border border-black/10 px-3 py-2 rounded-lg shadow-md bg-white`}
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
                                    className={`h-2/3 switzer-500 ${attachedFile ? "pt-[0.3rem]" : ""} focus:outline-none overflow-y-auto`}
                                ></div>

                                {showPlaceholder && (
                                    <span
                                        className={`absolute ${attachedFile ? "top-16" : "top-2"} pointer-events-none placeholder-input-box switzer-500 text-black`}
                                    >
                                        {placeholder}
                                    </span>
                                )}

                                <BottomOptions />
                                <ExtraOptions />
                                <ModelBox modelList={ModelList} />
                            </motion.div>
                        </div>

                        <ReportContentDialogueBox
                            hideReportContentDialogueBox={hideReportContentDialogueBox}
                            setHideReportContentDialogueBox={setHideReportContentDialogueBox}
                        />

                        <audio className="hidden" controls ref={audioRef} />
                    </ChatProvider>
                </div>
            )}
        </ProtectedRoute>

    )
}
