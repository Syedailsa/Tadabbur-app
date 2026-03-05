import { useCallback, useContext, useEffect, useRef } from "react";
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import { motion } from "framer-motion";
import DownArrow from "../../../../icons/arrow-down-head.svg";
import AttachIcon from "../../../../icons/attach_icon.svg";
import PlusIcon from "../../../../icons/plus-icon-black.svg";
import StoryIcon from "../../../../icons/story_telling_icon.svg";
import MicIcon from "../../../../icons/mic_icon.svg";
import { retryOperation, wsSendAsync } from "@/app/utils/retryOpernation";


const BottomOptions = () => {
  const {
    wsRef,
    hideExtraOptions,
    setHideExtraOptions,
    selectedModel,
    setHideModelBox,
    active,
    setActive,
    setAttachedFile,
  } = useContext(ChatContext)!;

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]); // Store audio chunks locally
  const fileInputRef = useRef<HTMLInputElement>(null);
  const micActive = useRef<boolean>(false);

  const isMicActive = active[2];

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
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/`, {
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


  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (file.type !== "application/pdf" && file.type !== "text/plain") {
      alert("Only PDF and TXT files are allowed.");
      return;
    }
    console.log("📂 File selected:", file.name);
    setAttachedFile(file);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="w-full flex gap-x-1 mt-auto items-center">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept=".pdf,.txt"
      />
      <motion.div
        whileTap={{ backgroundColor: "#0000003D" }}
        whileHover={{ backgroundColor: "#0000000D" }}
        animate={{ backgroundColor: active[0] ? "#0000000D" : "#00000000" }}
        id="choose-model-box"
        onClick={(e) => {
          e.stopPropagation();
          setHideModelBox((prev: boolean | null) => !prev);
          setActive((prev: boolean[]) => {
            const current = [...prev];
            current[0] = !current[0];
            return current;
          });
        }}
        className="relative flex-row-reverse gap-x-1 py-1 pr-3 pl-4 rounded-full cursor-pointer items-center hidden sm:flex"
      >
        <motion.div className="mt-0.2">
          <DownArrow className="w-5 h-5" />
        </motion.div>
        <p className="switzer-500 text-[0.91rem] sm:text-[0.96rem]">
          {selectedModel}
        </p>
      </motion.div>
      <motion.div className={`ml-auto flex gap-x-1`}>
        <motion.div
          onClick={(e) => {
            e.stopPropagation();
            setHideExtraOptions((prev: boolean) => !prev);
          }}
          animate={{
            backgroundColor: hideExtraOptions ? "#00000000" : "#0000000D",
          }}
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className={`w-9 h-9 rounded-full flex items-center justify-center cursor-pointer
          }`}
        >
          <PlusIcon className="fill-current w-5 h-5 text-black" />
        </motion.div>
        <motion.div
          id="story-telling-box"
          onClick={async () => {
            setActive((prev: boolean[]) => {
              const current = [...prev];
              if (current[1]) {
                wsSendAsync(wsRef.current, { type: "agent", agent: "normal" });
              } else {
                wsSendAsync(wsRef.current, { type: "agent", agent: "story-telling" });
              }
              current[1] = !current[1];
              return current;
            });
          }}
          animate={{ backgroundColor: active[1] ? "#0000000D" : "#00000000" }}
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="flex gap-x-1 px-3 py-1 rounded-full cursor-pointer items-center"
        >
          <StoryIcon className="fill-current w-5 h-5 text-black" />
          <span className="w-max switzer-500 text-[0.96rem]">
            Story telling
          </span>
        </motion.div>

        <motion.div
          id="mic-icon-box"
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          onClick={() => {
            setActive((prev: boolean[]) => {
              const current = [...prev];
              current[2] = !current[2];
              return current;
            });
          }}
          animate={{ backgroundColor: active[2] ? "#ff000020" : "#00000000" }}
          className="w-9 h-9 rounded-full flex items-center justify-center cursor-pointer"
        >
          <MicIcon
            className={`w-5 h-5 fill-current ${active[2] ? "text-red-600" : "text-black"
              }`}
          />
        </motion.div>

        <motion.div
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="rounded-full w-9 h-9 cursor-pointer flex justify-center items-center"
          id="attach-files-box"
          onClick={() => fileInputRef.current?.click()}
        >
          <AttachIcon className="fill-current text-black w-5 h-5" />
        </motion.div>
      </motion.div>
    </div>
  );
};

export default BottomOptions;