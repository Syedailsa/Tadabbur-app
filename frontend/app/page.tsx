"use client"

import type React from "react"
import ReactMarkdown from "react-markdown"
import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send, MessageCircle } from "lucide-react"

export default function ChatPage() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const viewportRef = useRef<HTMLDivElement | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          role: "assistant",
          content:
            "👋 Hi, I'm Tadabbur your Quran AI app! ask me what you want about quran.",
        },
      ])
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const ask = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!question.trim()) return
    const q = question.trim()

    setMessages((prev) => [...prev, { role: "user", content: q }])
    setQuestion("")
    setLoading(true)

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${process.env.NEXT_PUBLIC_CHAT_API_KEY}`,
        },
        body: JSON.stringify({
          messages: [...messages, { role: "user", content: q }].slice(-10),
        }),
      })

      if (!res.ok) {
        const txt = await res.text()
        throw new Error(txt || "API error")
      }

      const data = await res.json()
      const reply = data.reply ?? "No reply from server"
      setMessages((prev) => [...prev, { role: "assistant", content: reply }])
    } catch (err: any) {
      setError(err?.message ?? "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen bg-gradient-to-br from-background via-background to-secondary flex flex-col">
      <div className="bg-gradient-to-r from-primary to-accent shadow-sm border-b border-border">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="bg-primary-foreground p-2 rounded-lg">
            <MessageCircle className="w-6 h-6 text-emerald-900" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-primary-foreground">Tadabbur AI App</h1>
            <p className="text-sm text-primary-foreground/80">guidance on Quranic knowledge</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        <div ref={viewportRef} className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((m, i) => {
              const isUser = m.role === "user"
              return (
                <div
                  key={i}
                  className={`flex ${isUser ? "justify-end" : "justify-start"} animate-in fade-in slide-in-from-bottom-2`}
                  role="group"
                  aria-label={isUser ? "User message" : "Assistant message"}
                >
                  <div
                    className={`max-w-[80%] md:max-w-[65%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                      isUser
                        ? "bg-primary text-primary-foreground rounded-br-none"
                        : "bg-card text-foreground border border-border rounded-bl-none"
                    }`}
                  >
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown
                        components={{
                          p: ({ node, ...props }) => <p className="mb-1 last:mb-0" {...props} />,
                          strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
                          ul: ({ node, ...props }) => <ul className="list-disc pl-4 my-1" {...props} />,
                          ol: ({ node, ...props }) => <ol className="list-decimal pl-4 my-1" {...props} />,
                          li: ({ node, ...props }) => <li className="mb-0.5" {...props} />,
                          a: ({ node, ...props }) => <a className="text-accent underline" {...props} />,
                        }}
                      >
                        {m.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                </div>
              )
            })}
            {loading && (
              <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2">
                <div className="bg-card text-foreground border border-border rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                      <div
                        className="w-2 h-2 bg-accent rounded-full animate-pulse"
                        style={{ animationDelay: "0.2s" }}
                      />
                      <div
                        className="w-2 h-2 bg-accent rounded-full animate-pulse"
                        style={{ animationDelay: "0.4s" }}
                      />
                    </div>
                    <span className="text-xs text-muted-foreground">thinking...</span>
                  </div>
                </div>
              </div>
            )}
            {error && (
              <div className="flex justify-center">
                <div className="bg-destructive/10 text-destructive px-4 py-2 rounded-lg text-sm border border-destructive/20">
                  {error}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="border-t border-border bg-card shadow-lg">
          <form onSubmit={ask} className="max-w-3xl mx-auto p-4 md:p-6 space-y-2">
            <div className="flex gap-2 items-end">
              <Textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask me about quran related topics... (Shift+Enter for new line)"
                className="min-h-12 max-h-32 resize-none bg-background border-border text-foreground placeholder:text-muted-foreground"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    ask(e as any)
                  }
                }}
              />
              <Button
                type="submit"
                disabled={loading || !question.trim()}
                className="bg-primary hover:bg-accent text-primary-foreground px-6 h-12 transition-all"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>

            <div className="text-xs text-muted-foreground text-center">
              Helpful information for demonstration purposes only.
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
