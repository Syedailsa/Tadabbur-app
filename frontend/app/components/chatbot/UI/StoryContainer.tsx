import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { ReactNode, HTMLAttributes, CSSProperties, useContext } from "react";
import { motion } from "framer-motion"
import { StoryParagraph } from "../interfaces/ChatMessage"
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import FullViewIcon from "../../../../icons/full_size_icon.svg"
import { ChatContext } from "@/app/context/chatbot/ChatContext";


const StoryContainer = ({ story_data }: { story_data: StoryParagraph[] }) => {

    const { setOpenFullStoryView, setStoryData } = useContext(ChatContext)!
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
                                                className="leading-7 my-2 text-white"
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
                                    {seg.story_paragraph}
                                </ReactMarkdown>
                                <div className="self-start">
                                    {idx === (story_data.length - 1) ? (
                                        <div className="flex flex-col gap-y-2 justify-between">
                                            <div className="w-[80%] sm:w-[50%] md:w-[45%] lg:w-[30%] h-auto">
                                                <img className="rounded-md" src={`data:image/png;base64,${seg.image}`} />
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
                                        <img className="rounded-md" src={`data:image/png;base64,${seg.image}`} />
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