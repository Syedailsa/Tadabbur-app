import { useState, useContext, useEffect, useRef } from "react";
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import { motion } from "framer-motion";
import DownArrow from "../../../../icons/arrow-down-head.svg";
import AttachIcon from "../../../../icons/attach_icon.svg";
import PlusIcon from "../../../../icons/plus-icon.svg";
import StoryIcon from "../../../../icons/story_telling_icon.svg";
import MicIcon from "../../../../icons/mic_icon.svg";

const BottomOptions = () => {
  const {
    wsRef,
    hideExtraOptions,
    setHideExtraOptions,
    selectedModel,
    setHideModelBox,
    active,
    setActive,
    setInput,
    sessionID, 
  } = useContext(ChatContext);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const isMicActive = active[2];
    if (isMicActive) {
      startRecording();
    } else {
      stopRecording();
    }
    return () => stopRecording();
  }, [active[2]]);

  const startRecording = async () => {
    try {
      console.log("🎤 Mic Request...");

      window.dispatchEvent(new Event("tadabbur-mic-start"));

      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error("❌ Main WebSocket not connected!");
        alert("Please wait for chat connection...");
        setActive((prev: boolean[]) => {
          const c = [...prev];
          c[2] = false;
          return c;
        });
        return;
      }

      wsRef.current.send(JSON.stringify({ type: "start_mic" }));

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (
          event.data.size > 0 &&
          wsRef.current?.readyState === WebSocket.OPEN
        ) {
          wsRef.current.send(event.data);
        }
      };

      mediaRecorder.start(1000);
      console.log("🎙️ Recording via Main Socket!");
    } catch (micErr) {
      console.error("❌ Mic denied:", micErr);
      setActive((prev: boolean[]) => {
        const c = [...prev];
        c[2] = false;
        return c;
      });
    }
  };

  const stopRecording = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "stop_mic" }));
    }

    window.dispatchEvent(new Event("tadabbur-mic-stop"));
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    console.log("📂 File selected:", file.name);
    console.log("🆔 Current Session ID:", sessionID);

    if (file.type !== "application/pdf" && file.type !== "text/plain") {
      alert("Only PDF and TXT files are allowed.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    
    const activeSession = sessionID || "default_session";
    formData.append("session_id", activeSession); 

    try {
      console.log(`🚀 Uploading to session: ${activeSession}`);
      
      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        console.error("❌ Upload failed:", err);
        alert(`Upload failed: ${err.detail}`);
        return;
      }

      const data = await response.json();
      console.log("✅ Upload successful:", data);
      alert("File uploaded successfully! Ask me about it.");
      
      if (fileInputRef.current) fileInputRef.current.value = "";

    } catch (error) {
      console.error("❌ Network error:", error);
      alert("Failed to upload file.");
    }
  };

  return (
    <div className="w-full flex gap-x-1 mt-auto items-center">
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        style={{ display: 'none' }} 
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
          onClick={() => {
            setActive((prev: boolean[]) => {
              const current = [...prev];
              if (current[1]) {
                wsRef.current?.send(
                  JSON.stringify({ type: "agent", agent: "normal" })
                );
              } else {
                wsRef.current?.send(
                  JSON.stringify({ type: "agent", agent: "story-telling" })
                );
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
            className={`w-5 h-5 fill-current ${
              active[2] ? "text-red-600" : "text-black"
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
