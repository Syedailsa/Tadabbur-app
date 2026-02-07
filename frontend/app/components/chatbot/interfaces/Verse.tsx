
interface VerseForAudios {
    audio: string;
    numberInSurah: number;
    juz: number;
    manzil: number;
    ruku: number;
    sajda: boolean | SajdaVerse
}

interface VerseForImages {
    numberInSurah: number;
    text: string;
    verse_image_url: string;
}

type SajdaVerse = {
    id: number;
    recommended: boolean;
    obligatory: boolean
}

export type { VerseForAudios, VerseForImages }