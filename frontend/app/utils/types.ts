// ============================================
// IMPORTS
// ============================================

import { z } from 'zod';
import { Attachment } from '../components/chatbot/interfaces/ChatMessage';
// ============================================
// MESSAGE TYPES
// ============================================

export type MessageRole = "user" | "assistant";

export interface AssistantMessages {
  role: "assistant";
  message_id: string;
  content: string;
  reply_to_message_id: string | null;
  feedback: "like" | "dislike" | null;
  audio_url?: string | null;
}

export interface AttachedFile {
  file_id: string;
  file_name: string;
  file_type: string;
  created_at: string;
}


export interface ChatMessages {
  message_id: string;
  role: "user";
  content: string;
  responses: AssistantMessages[];
  attached_files?: AttachedFile[];
  number_of_responses?: number;
  active_message_index?: number;
}

// ============================================
// WEBSOCKET MESSAGE TYPES (Backend → Frontend)
// ============================================

export type WebSocketMessageType =
  | "session_id"
  | "assistance_response"
  | "open_audio_dialog"
  | "open_verse_dialog"
  | "tts_audio_chunk"
  | "chat_history"
  | "delete_session"
  | "delete_all_sessions"
  | "get_chat"
  | "agent"
  | "loading_message"
  | "report"
  | "undo-report"
  | "model-selection"
  | "streaming_end";

// Base interface for all WebSocket messages
export interface BaseWebSocketMessage {
  type: WebSocketMessageType;
}

// Session initialization response
export interface SessionIdMessage extends BaseWebSocketMessage {
  type: "session_id";
  session_id: string;
  status: "acknowledged" | "error";
  uploaded_files?: AttachedFile[];
  message_ids: string[];
}

// AI response streaming
export interface AssistanceResponseMessage extends BaseWebSocketMessage {
  type: "assistance_response";
  content: string;
  message_id: string;
  reply_to_message_id?: string;
  resend_flag?: boolean;
}

// Audio dialog request
export interface OpenAudioDialogMessage extends BaseWebSocketMessage {
  type: "open_audio_dialog";
  parsed_request: ParsedAudioRequest;
  original_message: string;
  available_reciters: string[];
  note?: string | undefined;
}

// Verse dialog request
export interface OpenVerseDialogMessage extends BaseWebSocketMessage {
  type: "open_verse_dialog";
  parsed_request: ParsedVerseRequest;
  original_message: string;
  note?: string;
}

// TTS audio chunk
export interface TTSAudioChunkMessage extends BaseWebSocketMessage {
  type: "tts_audio_chunk";
  audio?: string; // base64 encoded audio
  audio_url?: string;
}

// Chat history
export interface ChatHistoryMessage extends BaseWebSocketMessage {
  type: "chat_history";
  chat_history: ChatRecordType[];
  status: "acknowledged" | "error";
  error?: string;
}

// Session deletion
export interface DeleteSessionMessage extends BaseWebSocketMessage {
  type: "delete_session";
  status: "success" | "error";
  error?: string;
}

// Delete all sessions
export interface DeleteAllSessionsMessage extends BaseWebSocketMessage {
  type: "delete_all_sessions";
  status: "success" | "error";
  error?: string;
}

// Get specific chat
export interface GetChatMessage extends BaseWebSocketMessage {
  type: "get_chat";
  status: "acknowledged" | "error";
  unique_message_ids: string[];
  uploaded_files?: AttachedFile[];
  chat_history: ChatMessages[];
}

// Agent type change
export interface AgentMessage extends BaseWebSocketMessage {
  type: "agent";
  agent: "story-telling" | "tafseer";
}

// Loading message
export interface LoadingMessage extends BaseWebSocketMessage {
  type: "loading_message";
  content: string;
}

// Report acknowledgment
export interface ReportMessage extends BaseWebSocketMessage {
  type: "report";
  status: "acknowledged" | "error";
  message_id: string;
}

// Undo report
export interface UndoReportMessage extends BaseWebSocketMessage {
  type: "undo-report";
  message_id: string;
}

// Model selection
export interface ModelSelectionMessage extends BaseWebSocketMessage {
  type: "model-selection";
  status: "acknowledged" | "error";
  display_name: string;
}

// Union type for all possible WebSocket messages
export type WebSocketMessage =
  | SessionIdMessage
  | AssistanceResponseMessage
  | OpenAudioDialogMessage
  | OpenVerseDialogMessage
  | TTSAudioChunkMessage
  | ChatHistoryMessage
  | DeleteSessionMessage
  | DeleteAllSessionsMessage
  | GetChatMessage
  | AgentMessage
  | LoadingMessage
  | ReportMessage
  | UndoReportMessage
  | ModelSelectionMessage;

// ============================================
// WEBSOCKET MESSAGE TYPES (Frontend → Backend)
// ============================================

export type OutgoingMessageType =
  | "session-init"
  | "user_message"
  | "chat_history"
  | "delete_session"
  | "delete_all_sessions"
  | "get_chat"
  | "report"
  | "undo-report"
  | "change_model";

export interface BaseOutgoingMessage {
  type: OutgoingMessageType;
}

// Session initialization
export interface SessionInitMessage extends BaseOutgoingMessage {
  type: "session-init";
  session_id: string;
  user_id: string | null;
  model: string;
  mode:string;
}

// User message
export interface UserMessageOutgoing extends BaseOutgoingMessage {
  type: "user_message";
  message_id: string;
  role: "user";
  system_instructions: string;
  content: string;
  resend_flag?: boolean;
  resend_message_id?: string;
  attached_files: Attachment[];
}

// Request chat history
export interface ChatHistoryRequest extends BaseOutgoingMessage {
  type: "chat_history";
  user_id: string;
}

// Delete session
export interface DeleteSessionRequest extends BaseOutgoingMessage {
  type: "delete_session";
  session_id: string;
  user_id: string;
}

// Delete all sessions
export interface DeleteAllSessionsRequest extends BaseOutgoingMessage {
  type: "delete_all_sessions";
  user_id: string;
}

// Get specific chat
export interface GetChatRequest extends BaseOutgoingMessage {
  type: "get_chat";
  session_id: string;
}

// Report message
export interface ReportRequest extends BaseOutgoingMessage {
  type: "report";
  message_id: string;
  reason: string;
  category: string;
}

// Undo report
export interface UndoReportRequest extends BaseOutgoingMessage {
  type: "undo-report";
  message_id: string;
}

// Change model
export interface ChangeModelRequest extends BaseOutgoingMessage {
  type: "change_model";
  model: string;
}

// Union type for all outgoing messages
export type OutgoingWebSocketMessage =
  | SessionInitMessage
  | UserMessageOutgoing
  | ChatHistoryRequest
  | DeleteSessionRequest
  | DeleteAllSessionsRequest
  | GetChatRequest
  | ReportRequest
  | UndoReportRequest
  | ChangeModelRequest;

// ============================================
// AUDIO & VERSE TYPES
// ============================================

export interface ParsedAudioRequest {
  surah: number;
  ayah?: number;
  ayah_start?: number;
  ayah_end?: number;
  reciter?: string;
}

export interface ParsedVerseRequest {
  surah: number;
  ayah: number;
  ayah_start?: number;
  ayah_end?: number;
  translation?: string;
}

export type Reciter = string;

export interface AudioRequest {
  parsed_request: ParsedAudioRequest;
  original_message: string;
  available_reciters: Reciter[];
  note?: string | undefined;
}

export interface VerseRequest {
  parsed_request: ParsedVerseRequest;
  original_message: string;
  note?: string | undefined;
}

// ============================================
// CHAT HISTORY TYPES
// ============================================

export interface ChatRecordType {
  session_id: string | null;
  title: string | null;
  description: string | null;
  created_at: string | null;
}

// ============================================
// USER & REGISTRATION TYPES
// ============================================

export interface RegistrationDataType {
  username: string;
  age: number;
  email?: string;
  preferences?: UserPreferences;
}

export interface UserPreferences {
  theme?: "light" | "dark";
  language?: "en" | "ur" | "ar";
  notifications?: boolean;
}

export interface UserData extends RegistrationDataType {
  id: string;
  created_at?: string;
}

// ============================================
// FILE UPLOAD TYPES
// ============================================

export interface UploadResponse {
  message_id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  upload_status: "success" | "failed";
  error?: string;
}

// ============================================
// UI STATE TYPES
// ============================================

export interface PromptSuggestion {
  title: string;
  description: string;
  icon?: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  description?: string;
}

// ============================================
// CUSTOM EVENT TYPES
// ============================================

export interface STTResultEvent extends CustomEvent {
  detail: string; // transcribed text
}

export interface CustomEventMap {
  "tadabbur-mic-start": Event;
  "tadabbur-mic-stop": Event;
  "tadabbur-transcription-start": Event;
  "tadabbur-transcription-error": Event;
  "tadabbur-stt-result": STTResultEvent;
}

// ============================================
// AUTHENTICATION TYPES
// ============================================

export type Step = "EMAIL" | "OTP" | "PASSWORD" | "SUCCESS";

export interface ForgotPasswordProps {
  onBackToLogin: () => void;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message?: string;
  detail?: string;
}

export interface VerifyOtpRequest {
  email: string;
  otp: string;
}

export interface VerifyOtpResponse {
  message?: string;
  detail?: string;
}

export interface ChangePasswordRequest {
  email: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message?: string;
  detail?: string;
}

// ============================================
// GOOGLE AUTHENTICATION TYPES
// ============================================

export interface GoogleCredentialResponse {
  credential?: string;
  clientId?: string;
  select_by?: string;
}

export interface GoogleSignInRequest {
  token: string;
}

export interface GoogleSignInResponse {
  token: string;
  message: string;
  loginTime: string;
  user_id: string;
  firstname: string;
}

export interface GoogleLoginProps {
  onSuccess: (data: GoogleSignInResponse) => void;
  onError: (message: string) => void;
  text?: "signin_with" | "signup_with";
}

// ============================================
// LOGIN TYPES
// ============================================

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginInputs = z.infer<typeof loginSchema>;

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  message: string;
  loginTime: string;
  user_id: string;
  firstname: string;
}

export interface LoginProps {
  onSuccess: (data: LoginResponse) => void;
}

// ============================================
// UTILITY TYPES
// ============================================

export type FeedbackType = "like" | "dislike" | null;
export type AgentType = "story-telling" | "tafseer";
export type MessageStatus = "sending" | "sent" | "error";

// ============================================
// CONTEXT TYPES
// ============================================

export interface PromptExtraOptionsContextValue {
  parent_index: number | null;
  assistant_index: number | null;
  messages: ChatMessages[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessages[]>>;
  message_id: string | null;
  reply_to_message_id: string | null;
  hidePromptExtraOptionsModelBox: boolean | null;
  setHidePromptExtraOptionsModelBox: React.Dispatch<React.SetStateAction<boolean | null>>;
  hideReportContentDialogueBox: boolean | null;
  setHideReportContentDialogueBox: React.Dispatch<React.SetStateAction<boolean | null>>;
  sessionID: string | null;
  wsRef: React.RefObject<WebSocket | null>;
  ask: (
    input: string,
    guidelines?: string | null,
    resend_flag?: boolean,
    resend_message_id?: string | null,
    old_assistant_responses?: AssistantMessages[]
  ) => Promise<void>;
  hideResendPromptDialogue: boolean | null;
  setHideResendPromptDialogue: React.Dispatch<React.SetStateAction<boolean | null>>;
  activeMessageIndex: number | null;
  setActiveMessageIndex: React.Dispatch<React.SetStateAction<number | null>>;
}

// ============================================
// COMPONENT PROPS TYPES
// ============================================

export interface ChatProviderProps {
  children: React.ReactNode;
  chatHistory: ChatRecordType[] | null;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecordType[] | null>>;
  wsRef: React.RefObject<WebSocket | null>;
  sessionID: string | null;
  attachedFile: File | null;
  setAttachedFile: React.Dispatch<React.SetStateAction<File | null>>;
  messages: ChatMessages[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessages[]>>;
}

export interface QuranAudioDialogProps {
  isOpen: boolean;
  onClose: () => void;
  parsedRequest: ParsedAudioRequest;
  originalMessage: string;
  availableReciters: string[];
  wsRef: React.RefObject<WebSocket | null>;
}

export interface QuranVerseDialogProps {
  isOpen: boolean;
  onClose: () => void;
  parsedRequest: ParsedVerseRequest;
  originalMessage: string;
  note?: string | null;
  wsRef: React.RefObject<WebSocket | null>;
}

export interface RegistrationFormProps {
  onComplete: (data: RegistrationDataType) => void;
}

export interface ReportContentDialogueBoxProps {
  hideReportContentDialogueBox: boolean | null;
  setHideReportContentDialogueBox: React.Dispatch<React.SetStateAction<boolean | null>>;
}

export interface PromptExtraOptionsProps {
  messageType: "user" | "assistant";
}

export interface ModelBoxProps {
  modelList: ModelInfo[];
}

export interface ControlsProps {
  wsRef: React.RefObject<WebSocket | null>;
}

// Type guard functions
export function isAssistanceResponse(
  msg: WebSocketMessage
): msg is AssistanceResponseMessage {
  return msg.type === "assistance_response";
}

export function isAudioDialog(
  msg: WebSocketMessage
): msg is OpenAudioDialogMessage {
  return msg.type === "open_audio_dialog";
}

export function isVerseDialog(
  msg: WebSocketMessage
): msg is OpenVerseDialogMessage {
  return msg.type === "open_verse_dialog";
}

export function isSessionId(
  msg: WebSocketMessage
): msg is SessionIdMessage {
  return msg.type === "session_id";
}

export function isChatHistory(
  msg: WebSocketMessage
): msg is ChatHistoryMessage {
  return msg.type === "chat_history";
}


// Personalization types
export interface PersonalizationRequest {
  username: string;
  age: number;
}

export interface PersonalizationResponse {
  message: string;
  username: string | null;
  age: number | null;
  is_personalized: boolean;
  timestamp: string;
}