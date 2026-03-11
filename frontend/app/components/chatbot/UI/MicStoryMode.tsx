import MicIcon from "../../../../icons/mic_icon.svg"
import { motion } from "framer-motion"
import { useContext, useCallback, useRef, useEffect } from "react";
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import { retryOperation } from "@/app/utils/retryOpernation";

const MicStoryMode = () => {
    const {
        active,
        setActive,
    } = useContext(ChatContext)!;

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]); // Store audio chunks locally
    const isMicActive = active[2];
    const micActive = useRef<boolean>(false);

    const startRecording = useCallback(async () => {
        try {
            console.log("🎤 Mic Request (Batch Mode)...");

            // Signal UI to show WaveForm
            window.dispatchEvent(new Event("tadabbur-mic-start"));

            audioChunksRef.current = [];

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;

            // Collect Data
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach((track) => track.stop());

                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

                if (audioBlob.size > 0) {
                    await uploadAudioForTranscription(audioBlob);
                }
            };

            mediaRecorder.start();
            console.log("🎙️ Recording Started locally.");

        } catch (micErr) {
            console.error("❌ Mic denied:", micErr);
            setActive((prev: boolean[]) => {
                const c = [...prev];
                c[2] = false;
                return c;
            });
        }
    }, [setActive]);

    const stopRecording = useCallback(() => {
        if (
            mediaRecorderRef.current &&
            mediaRecorderRef.current.state !== "inactive"
        ) {
            mediaRecorderRef.current.stop();
        }

        // Signal UI to stop WaveForm
        window.dispatchEvent(new Event("tadabbur-mic-stop"));
    }, []);

    const uploadAudioForTranscription = async (audioBlob: Blob) => {
        const formData = new FormData();
        formData.append("file", audioBlob, "voice_note.webm");

        try {
            console.log("📤 Uploading audio for transcription...");

            // 1. Dispatch event to tell ChatPage to show loading state
            window.dispatchEvent(new Event("tadabbur-transcription-start"));
            const data = await retryOperation(async () => {
                const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/transcribe`, {
                    method: "POST",
                    body: formData,
                });

                if (!response.ok) throw new Error("Transcription failed");

                return await response.json();
            }, 8, 1000)

            const text = data.text;

            if (text) {
                console.log("✅ Transcription Received:", text);
                const event = new CustomEvent("tadabbur-stt-result", { detail: text });
                window.dispatchEvent(event);
                // Note: ChatPage will turn off loading when it receives "tadabbur-stt-result"
            }

        } catch (error) {
            console.error("Transcription Error:", error);
            // 2. Dispatch error event so ChatPage stops loading
            window.dispatchEvent(new Event("tadabbur-transcription-error"));
            alert("Failed to transcribe audio.");
        }
    };


    useEffect(() => {
        if (isMicActive) {
            console.log("Starting mic");
            startRecording();
            micActive.current = true;
        } else if (!isMicActive && micActive.current) {
            console.log("Stopping mic");
            stopRecording();
            micActive.current = false;
        }
        return () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
                mediaRecorderRef.current.stop();
            }
        };
    }, [isMicActive, startRecording, stopRecording]);


    return (
        <motion.div onClick={() => {
            setActive((prev: boolean[]) => {
                const current = [...prev];
                current[2] = !current[2];
                return current;
            });
        }}
            animate={{ backgroundColor: active[2] ? "#ff000020" : "#00000000" }} whileHover={{ backgroundColor: active[2] ? "##ff000020" : "#FFFFFF1A" }}
            whileTap={{ backgroundColor: "#FFFFFF33" }} className="p-2 rounded-full cursor-pointer bg-white/5">
            <MicIcon
                className={`w-5.5 h-5.5 fill-current ${active[2] ? "text-red-600" : "text-white"
                    }`}
            />
        </motion.div>
    )
}

export default MicStoryMode