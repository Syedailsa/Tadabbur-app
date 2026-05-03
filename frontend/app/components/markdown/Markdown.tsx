
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import { useContext } from "react";
import { ReactNode, CSSProperties, HTMLAttributes, } from "react";

import { ChatContext } from "@/app/context/chatbot/ChatContext";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism";

type textContentProp = {
    textContent: string | null
}

const Markdown = ({ textContent}: textContentProp) => {
    const { currentMode } = useContext(ChatContext)!


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

    return (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={{
                // HEADERS
                h1: ({ node, ...props }) => (
                    <h1
                        className={`text-3xl font-bold ${currentMode === "normal" ? "text-gray-700" : "text-white"}`}
                        {...props}
                    />
                ),
                h2: ({ node, ...props }) => (
                    <h2
                        className={`text-2xl font-semibold ${currentMode === "normal" ? "text-gray-700" : "text-white"}`}
                        {...props}
                    />
                ),
                h3: ({ node, ...props }) => (
                    <h3
                        className={`text-xl font-semibold ${currentMode === "normal" ? "text-gray-700" : "text-white"}`}
                        {...props}
                    />
                ),

                // PARAGRAPH
                p: ({ node, ...props }) => (
                    <p
                        className={`leading-7 my-2 wrap-break-word ${currentMode === "normal"
                                    ? "text-gray-700"
                                    : "text-white"
                            }`}
                        {...props}
                    />
                ),

                // STRONG ( **bold** )
                strong: ({ node, ...props }) => (
                    <strong
                        className={`font-bold text-black ${currentMode === "normal" ? "text-gray-700" : "text-white"}`}
                        {...props}
                    />
                ),

                // EMPHASIS ( *italic* )
                em: ({ node, ...props }) => (
                    <em
                        className={`italic ${currentMode === "normal" ? "text-gray-700" : "text-white"}`}
                        {...props}
                    />
                ),

                // LINE BREAK
                br: ({ node, ...props }) => <br />,

                // LINKS
                a: ({ node, ...props }) => (
                    <a
                        className={`${currentMode === "normal" ? "text-blue-600" : "text-blue-400"}  underline wrap-break-word`}
                        target="_blank"
                        rel="noreferrer"
                        {...props}
                    />
                ),

                // LISTS
                ul: ({ node, ...props }) => (
                    <ul
                        className={`list-disc pl-6 ${currentMode === "normal" ? "text-black" : "text-white"}`}
                        {...props}
                    />
                ),
                ol: ({ node, ...props }) => (
                    <ol
                        className={`list-decimal pl-6 ${currentMode === "normal" ? "text-black" : "text-white"}`}
                        {...props}
                    />
                ),
                li: ({ node, ...props }) => (
                    <li className={`my-1 ${currentMode === "normal" ? "text-black" : "text-white"}`} {...props} />
                ),
                blockquote: ({ node, ...props }) => (
                    <blockquote
                        className={`border-l-4 border-gray-400 pl-4 italic my-3 ${currentMode === "normal" ? "text-black" : "text-white"}`}
                        {...props}
                    />
                ),

                // HORIZONTAL RULE
                hr: () => (
                    <hr className="my-4 border-gray-300" />
                ),

                table: ({ node, ...props }) => (
                    <div className={`overflow-x-auto my-4 border ${currentMode === "normal" ? "border-black/20" : "bg-white/20"} rounded-lg shadow-sm`}>
                        <table className={`min-w-full divide-y ${currentMode === "normal" ? "divide-gray-200" : "divide-black"}`} {...props} />
                    </div>
                ),
                thead: ({ node, ...props }) => (
                    <thead
                        className={`${currentMode === "normal" ? "bg-gray-50" : "bg-black"}`}
                        {...props}
                    />
                ),
                tbody: ({ node, ...props }) => (
                    <tbody
                        className={`${currentMode === "normal" ? "bg-white divide-gray-200" : "bg-black divide-black"} divide-y `}
                        {...props}
                    />
                ),
                tr: ({ node, ...props }) => (
                    <tr
                        className={`${currentMode === "normal" ? "hover:bg-gray-50" : ""}`}
                        {...props}
                    />
                ),
                th: ({ node, ...props }) => (
                    <th className={`px-4 py-3 text-left text-sm font-medium ${currentMode === "normal" ? "text-black" : "text-white"} uppercase tracking-wider border-b`} {...props} />
                ),
                td: ({ node, ...props }) => (
                    <td className={`px-4 py-3 text-sm border-b border-black/20 whitespace-pre-wrap ${currentMode === "normal" ? "text-gray-700" : "text-white"}`} {...props} />
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
                                className={`px-1.5 py-0.5 rounded text-sm font-mono ${currentMode === "normal" ? "text-black bg-gray-100" : "text-white bg-black"}`}
                                {...props}
                            >
                                {children}
                            </code>
                        );
                    }
                },
            }}
        >
            {preprocessContent(textContent ?? "")}
        </ReactMarkdown>
    )
}

export default Markdown