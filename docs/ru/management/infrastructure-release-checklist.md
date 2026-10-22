# Инфраструктура: применение перед выпуском

Локальные исправления не меняют запущенный сервер. Этот список — единый
операционный этап перед выпуском, а не новые мелкие задачи разработки.
Коммит, push, слияние и deployment требуют отдельного поручения владельца.

Общий остаток разработки: [audit/remaining_work.md](../../../audit/remaining_work.md).

## Секреты и права

- Создать отдельные runtime и migration PostgreSQL roles на site/game базах;
  проверить владельцев объектов, PUBLIC privileges и default privileges.
  Runtime не получает superuser, CREATE ROLE или доступ к другой базе.
- MongoDB приложениям выдать роли только в используемой базе, отдельно от root.
  Проверить нужные индексы/коллекции и отказ обращения к другой базе.
- Для Redis составить матрицу фактических key prefixes и команд. Shared streams
  и общие ключи нельзя объявить изолированными только по имени worker.
  Studio нужны только читающие команды; приложениям не нужны CONFIG/ACL/FLUSHALL.
- Создать отдельные credentials, передать их нужным сервисам и только после
  проверки отозвать прежние. Не переключать Compose на ещё не созданные роли.
- Для Studio задать отдельный `STUDIO_ACCESS_TOKEN`, открыть только через
  loopback/SSH tunnel или HTTPS, использовать username `studio` и token как пароль.
  Убедиться, что production source использует отдельные read-only DB credentials.

## Backup и обнаружение сбоев

- Назначить владельца и согласовать schedule, retention, RPO/RTO, offsite и
  шифрование для site/game PostgreSQL, MongoDB, Redis, assets и конфигурации.
- Восстановить реальный backup в изоляции; проверить данные и общий recovery
  checkpoint между хранилищами. Измерить время и записать evidence.
- Подключить [проверку recovery evidence](recovery-evidence.md) к расписанию и
  каналу дежурного; проверить доставку alert искусственным отказом.
- Проверить уведомления при недоступности сервисов, ошибках worker и TLS renewal.
  Наличие метрик или systemd exit само по себе не доказывает доставку alert.

## Публикация и smoke

- До merge устранить известные игровые failures общего прогона: два inventory
  ожидания отсутствия metrics и missing loot profile golem_foundry. В текущем
  инфраструктурном пакете игровая логика и эти ожидания не изменялись.

- Повторно проверить GitHub protections, reviewers и область production secrets.
  Опубликовать согласованный workflow через разрешённое слияние develop → main.
- Задать корректный production `SITE_BASE_URL` с HTTPS для почтовых ссылок.
- Применить итоговые allowlists и сеть пересозданием сервисов. Проверить реальные
  эффективные имена переменных без вывода значений секретов.
- Проверить API auth, Studio auth/read-only, email origin, readiness, backup и
  доставку alerts на фактически развёрнутой версии. Зафиксировать rollback.

Эти действия в локальном пакете 22.10.2026 не выполнялись: рабочие данные,
production, GitHub secrets и существующие credentials не изменялись.
