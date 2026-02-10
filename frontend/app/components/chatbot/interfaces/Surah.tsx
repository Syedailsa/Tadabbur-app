import { VerseForAudios, VerseForImages } from "./Verse";


interface SurahForAudios {
    name: string;
    englishName: string;
    revelationType: string;
    ayahs: VerseForAudios[]
}


interface SurahForVerseImages {
    name: string;
    englishName: string;
    ayahs: VerseForImages[]
}

export type { SurahForAudios, SurahForVerseImages }