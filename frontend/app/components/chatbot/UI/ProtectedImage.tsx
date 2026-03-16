import { useEffect, useState } from "react";

const ProtectedImage = ({ filename, className, alt }: { filename: string, className?: string, alt?: string }) => {
    const [src, setSrc] = useState<string>("")

    useEffect(() => {
        const token = localStorage.getItem("auth_token")
        if (!token || !filename) return

        fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/story-image/${filename}?token=${token}`)
            .then(res => {
                if (!res.ok) throw new Error("Unauthorized")
                return res.blob()
            })
            .then(blob => setSrc(URL.createObjectURL(blob)))
            .catch(err => console.error("Image load failed:", err))
    }, [filename])

    if (!src) return <div className={`${className} bg-white/10 animate-pulse rounded-md`} />
    
    return <img src={src} className={className} alt={alt || ""} />
}

export default ProtectedImage