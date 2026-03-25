import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { ReactNode, HTMLAttributes, CSSProperties, useContext, useState, useEffect } from "react";
import { motion } from "framer-motion"
import { StoryParagraph } from "../interfaces/ChatMessage"
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import FullViewIcon from "../../../../icons/full_size_icon.svg"
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import ProtectedImage from "./ProtectedImage";
import Markdown from "../../markdown/Markdown";


const StoryContainer = ({ story_data }: { story_data: StoryParagraph[] }) => {

    const { setOpenFullStoryView, setStoryData, currentMode } = useContext(ChatContext)!
    if (!story_data || story_data.length <= 0) return null

    return (
        <motion.div className="z-10 flex flex-col">
            <div className="rounded-md flex flex-col gap-y-6 shadow-md mt-4 pt-2 pb-6 px-3">
                {story_data.map((seg, idx) => {
                    return (
                        <div id="story-container" key={idx}>
                            <div className="flex flex-col items-center gap-y-1 switzer-500">
                                <div className="self-start">
                                    <p className="switzer-600 text-lg tracking-tight text-white">{idx + 1}. {seg.paragraph_title}</p>
                                </div>
                                <Markdown textContent={seg.story_paragraph}/>
                                <div className="self-start w-full">
                                    {idx === (story_data.length - 1) ? (
                                        <div className="flex flex-col gap-y-2 justify-between">
                                            <div className="w-[80%] sm:w-[50%] md:w-[45%] lg:w-[30%] h-auto">
                                                <ProtectedImage filename={seg.image} className="rounded-md" alt={`image${idx}`} />
                                            </div>

                                            <div onClick={() => {
                                                setOpenFullStoryView(true)
                                                setStoryData(story_data)
                                            }} className="flex gap-x-2 h-max w-max items-center border border-white/10 px-2 py-0.5 rounded-md cursor-pointer hover:text-white/90 text-white/70">
                                                <FullViewIcon className="w-3 h-3 fill-current" />
                                                <p className="switzer-500 w-max tracking-tight text-[0.8rem]">View in full mode</p>
                                            </div>
                                        </div>
                                    ) : (<div className="w-[80%] sm:w-[50%] md:w-[45%] lg:w-[30%] h-auto">
                                        <ProtectedImage filename={seg.image} className="rounded-md" alt={`image${idx}`} />
                                    </div>

                                    )}

                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </motion.div>
    )
}

export default StoryContainer