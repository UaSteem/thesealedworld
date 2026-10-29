(() => {
  'use strict';
  const log = document.getElementById('chat-messages');
  const input = document.getElementById('chat-input');
  const tabs = [...document.querySelectorAll('[data-chat]')];
  let active = 'world';
  const messages = {
    world: [
      ...Array.from({length:9},(_,i)=>({author:['Лиора','Страж','Путник'][i%3],text:['Кто идёт к арене?','Встречаемся у входа.','Проверка читаемости чата на игровом поле.'][i%3]})),
      {author:'Лиора',text:'Куда отправимся дальше?'}],
    local: [{author:'Система',text:'Это локальный макет канала «Рядом».'}],
    system: [{author:'Система',text:'Лаборатория интерфейса. Игровые сервисы не подключены.'}],
  };
  function render() {
    log.replaceChildren();
    for (const message of messages[active]) {
      const row = document.createElement('p');
      const time = document.createElement('time');time.textContent = '12:40';
      const author = document.createElement('b');author.textContent = message.author;
      const text = document.createElement('span');text.textContent = message.text;
      row.append(time,author,text);log.append(row);
    }
    log.scrollTop = log.scrollHeight;
  }
  tabs.forEach(tab => tab.addEventListener('click', () => {
    active = tab.dataset.chat;
    tabs.forEach(button => {
      const selected = button === tab;
      button.classList.toggle('is-active',selected);button.setAttribute('aria-pressed',String(selected));
    });
    render();
  }));
  document.getElementById('chat-form').addEventListener('submit', event => {
    event.preventDefault();
    if (!input.value.trim()) return;
    messages[active].push({author:'Вы',text:input.value.trim()});input.value='';render();
  });
  render();
})();
