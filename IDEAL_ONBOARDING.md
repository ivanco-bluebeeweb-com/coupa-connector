# Coupa Connector — идеальный первый запуск

Источник: `ONBOARDING_FIRST_LAUNCH_STANDARD.md`. Целевой пользователь: закупочный
аналитик, AP-клерк или category manager, впервые открывающий приложение.

## 1. Credential type
OAuth2 Client Credentials, instance-scoped: instance URL (`*.coupahost.com` или
кастомный домен) + client_id/client_secret, полученные через Coupa admin
(Setup > OAuth2/OpenID Connect Clients) для конкретного instance.

## 2. Идеальный флоу (без ограничений SDK)
1. **Первое открытие** — простыми словами объяснить: "URL вашего Coupa-инстанса,
   например https://acme.coupahost.com — так же, как вы заходите в Coupa в браузере".
2. **Форма подключения** — instance URL + OAuth client_id/client_secret, без
   лишних полей (token_url выводится автоматически из instance URL).
3. **После успеха** — сразу пробный вызов к каждому из шести модулей
   (Requisitions/POs/Invoices/Suppliers/Contracts/Expense Reports) и явная карта
   "что включено для этого instance" — Coupa лицензирует модули отдельно, никогда
   не предполагать, что все доступны.
4. **Живая сводка** — открытые requisitions на approval, просроченные invoices,
   pending expense reports — сразу actionable, не пустой экран.
5. **Ошибка "module not licensed"** — отдельное явное сообщение, какой именно
   модуль недоступен для этого instance и что нужно уточнить у Coupa admin/success
   manager, а не общий 403.
6. **Multi-instance** — если у консультанта несколько Coupa-инстансов клиентов
   (sandbox + production — Coupa всегда даёт оба), явный переключатель между
   сохранёнными подключениями с пометкой "Sandbox" / "Production".
7. **Sourcing/SIM предупреждение** — явно объяснить в help-диалоге, что RFx/аукционы
   и полный SIM onboarding не входят в это приложение (см. `CONNECTOR_DISCOVERY.md`
   §4), чтобы пользователь не ждал функциональности, которой здесь не будет.

## 3. Разница с реализацией сейчас
См. `UI_COMPONENT_PLAN.md` §0 — реализация показывает карту доступности модулей
как обычный список (DataTable/Badge), без специализированного визуального виджета —
такого примитива в SDK нет.
