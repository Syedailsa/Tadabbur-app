import { AssistantMessage } from "@/app/components/chatbot/interfaces/ChatMessage";

function groupChatMessages(chatMessages: any) {
  const userMessagesMap = new Map();

  // First, create all user messages in the map
  chatMessages.forEach((msg: any) => {
    if (msg.role === "user") {
      userMessagesMap.set(msg.message_id, {
        message_id: msg.message_id || null,
        role: "user",
        content: msg.content,
        attachments: msg.attachments,
        responses: [],
        number_of_responses: 0,
        active_message_index: 0,
      });
    }
  });

  // Then, attach assistant messages to their respective user messages
  chatMessages.forEach((msg: any) => {
    if (msg.role === "assistant") {
      const parentId = msg.reply_to_message_id;
      if (parentId && userMessagesMap.has(parentId)) {
        const userMsg = userMessagesMap.get(parentId);
        const assistantMsg: AssistantMessage = {
          message_id: msg.message_id,
          role: "assistant",
          content: msg.content,
          reply_to_message_id: parentId,
          feedback: msg.feedback,
          audio_link: msg.audio_url,
          audio_state: null,
          has_verse_audio: msg.has_verse_audio,
          verse_audio_data: msg.audio_data,
          has_verse_image: msg.has_verse_image,
          verse_images: msg.verse_images,
          story_data: []

        };
        userMsg.responses.push(assistantMsg);
        userMsg.number_of_responses = userMsg.responses.length;
      }
    }
  });

  // Return as array of user messages with responses
  return Array.from(userMessagesMap.values());
}

export default groupChatMessages;
