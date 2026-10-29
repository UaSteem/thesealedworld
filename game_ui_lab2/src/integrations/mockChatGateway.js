export const CHAT_CHANNELS = Object.freeze([
  { id: 'world', label: 'Мир' },
  { id: 'local', label: 'Локация' },
  { id: 'party', label: 'Группа' },
  { id: 'trade', label: 'Торговля' },
  { id: 'system', label: 'Система' },
]);

const initialMessages = {
  world: [
    ...Array.from({ length: 9 }, (_, i) => ({
      author: ['Лиора', 'Страж', 'Путник'][i % 3],
      text: ['Кто идёт к арене?', 'Встречаемся у входа.', 'Проверка читаемости чата на игровом поле.'][i % 3],
    })),
    { author: 'Лиора', text: 'Куда отправимся дальше?' },
  ],
  local: [{ author: 'Система', text: 'Сообщения текущей локации: моковый экземпляр рифта.' }],
  party: [{ author: 'Страж', text: 'Группа: собираемся у входа в рифт.' }],
  trade: [{ author: 'Торговец', text: 'Торговля: обменяю железную руду на травы. Макет.' }],
  system: [{ author: 'Система', text: 'Лаборатория интерфейса. Игровые сервисы не подключены.' }],
};

// UI-only contract: getMessages(channel), send(channel, text), subscribe(listener).
// The mock owns chat history only; combat events have a separate gateway.
export function createMockChatGateway() {
  const history = Object.fromEntries(CHAT_CHANNELS.map(({ id }) => [
    id,
    initialMessages[id].map((message, index) => ({ id: `${id}-${index}`, time: '12:40', ...message })),
  ]));
  const listeners = new Set();
  let nextId = 1;

  function getMessages(channel) {
    if (!Object.hasOwn(history, channel)) return [];
    return history[channel].map((message) => ({ ...message }));
  }

  function send(channel, text) {
    if (!Object.hasOwn(history, channel)) throw new RangeError(`Unknown chat channel: ${channel}`);
    const content = String(text).trim();
    if (!content) return null;
    const message = { id: `local-${nextId++}`, time: '12:40', author: 'Вы', text: content.slice(0, 300) };
    history[channel].push(message);
    for (const listener of listeners) listener({ channel, message: { ...message } });
    return { ...message };
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  return { getMessages, send, subscribe };
}
