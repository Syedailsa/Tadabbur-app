import { useEffect, useState } from "react";

const imageCache = new Map<string, string>()

const ProtectedImage = ({ filename, className, alt }: { filename: string, className?: string, alt?: string }) => {
    const [src, setSrc] = useState<string>("")
    const [retryCount, setRetryCount] = useState<number>(0)
    const [error, setError] = useState<boolean>(false)

    useEffect(() => {
        const token = localStorage.getItem("auth_token")
        if (!token || !filename) return

        if (imageCache.has(filename)) {
            setSrc(imageCache.get(filename)!)
            return
        }

        fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/story-image/${filename}?token=${token}`)
            .then(res => {
                if (!res.ok) throw new Error("Unauthorized")
                return res.blob()
            })
            .then(blob => {
                const url = URL.createObjectURL(blob)
                imageCache.set(filename, url)
                setSrc(url)
            })
            .catch(err => {
                console.error("Image load failed:", err)
                if (retryCount < 3) {
                    setTimeout(() => setRetryCount(prev => prev + 1), 5000)
                } else {
                    setError(true)
                }
            })
    }, [filename, retryCount])

    if (error) return (
        <div className="w-full rounded-md border border-white/10 flex flex-col items-center justify-center gap-y-2" style={{ height: "160px" }}>
            <p className="switzer-500 text-white/40 text-xs">Image could not be loaded</p>
            <button
                onClick={() => { setError(false); setRetryCount(0); }}
                className="text-white/30 hover:text-white/60 text-xs switzer-500 border border-white/10 px-2 py-0.5 rounded-md transition-colors"
            >
                Retry
            </button>
        </div>
    )

    if (!src) return (
        <div className="animate-pulse rounded-md w-full" style={{ height: "160px", backgroundColor: "rgba(255,255,255,0.45)" }} />
    )

    return <img src={src} className={className} alt={alt || ""} />
}

export default ProtectedImage
