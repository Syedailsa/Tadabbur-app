import crypto from "crypto"
const generateSessionId = (): string => {
    return `sess_${crypto.randomBytes(6).toString('hex')}`;
};

export default generateSessionId;