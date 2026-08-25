# Coupa Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `coupa-connector`.

## 0. Разница с IDEAL_ONBOARDING.md
Идеал предполагает живую "модульную карту лицензий" сразу при подключении.
Текущая реализация показывает это через `audit_coupa_access` как обычный список
(`ui.DataTable`/Badge), без специализированного виджета — такого примитива в SDK нет.

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Stack`(direction="v", align="stretch") + `ui.Text`(instance label) + `ui.Divider` + navigation `ui.ListItem`(Requisitions/Purchase Orders/Invoices/Suppliers/Contracts/Expense Reports) + `ui.Button`("App settings") | Без карточек по стандарту, без дублирования инструкций из help-диалога. |
| Connect form (sidebar, not connected) | `ui.Form`(action="connect_coupa", submit_label="Verify and connect") + `_field`-labelled `ui.Input`(instance URL, client ID) + `ui.Password`(client secret) + `ui.Button`("How do I get these credentials?" → Dialog) | Форма растянута на всю ширину сайдбара, поля растянуты внутри неё — по UI_INTERFACE_STANDARD. |
| Requisition List (center, `center_overlay=True`) | `ui.Stats`(Total requisitions) + `ui.Input`(param_name="status", placeholder="Например: Approved, Pending Approval...") + `ui.DataTable`(id, title, status Badge, requester, total) | `DataTable` — основной обзор; `Input` для фильтра по статусу. |
| Purchase Order List | `ui.DataTable`(PO number, supplier, status Badge, total, currency) | Тот же паттерн, что requisitions — единообразие. |
| Invoice List | `ui.DataTable`(invoice number, supplier, status Badge, amount, due date) | AP-клерку нужен статус и сумма на одном экране. |
| Supplier List | `ui.DataTable`(name, id, status Badge) | Быстрый обзор по поставщикам. |
| Contract List | `ui.DataTable`(title, supplier, status Badge, end date) | Category manager видит сроки контрактов сразу. |
| Expense Report List | `ui.DataTable`(id, submitter, status Badge, total) | Approver видит очередь на согласование. |
| Access audit (center overview) | `ui.Stats`(Available/Unavailable) + список Badge по модулям | Прозрачная лицензионная карта instance. |
| App settings (center) | `ui.Header` + список подключений + `ui.Button`("Disconnect", variant="danger") | Единственное место для disconnect — не дублируется в сайдбаре. |

## 2. Что НЕ строим (SDK-ограничения)
Нет отдельного примитива "module license map" — заменяется DataTable/Badge
комбинацией, как в Oracle Procurement Cloud Connector и SAP Ariba Connector.
