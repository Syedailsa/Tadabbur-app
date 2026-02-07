import { VerseForAudios, VerseForImages } from "./Verse";


interface SurahForAudios {
    name: string;
    englishName: string;
    revelationType: string;
    ayahs: VerseForImages[]
}


interface SurahForVerseImages {
    name: string;
    englishName: string;
    ayahs: VerseForAudios[]
}

export type { SurahForAudios, SurahForVerseImages }