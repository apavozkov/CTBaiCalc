# CTBaiCalc — Clinical Trial Budget AI Calculator

## 1) Цель проекта
Создать веб-сервис для быстрого и прозрачного расчёта бюджетов клинических исследований с поддержкой AI-аналитики и сравнением сценариев. Система должна заменить ручной Excel-процесс, снизить риск ошибок и ускорить согласование между PM/финансами.

## 2) Подтверждение и уточнение исходных идей
Ваше понимание задачи корректное и практичное:
- **Деплой на личный сервер** — подходит, если есть Docker + reverse proxy + HTTPS.
- **OpenRouter токен** — логично использовать как AI-шлюз (без привязки к одному вендору модели).
- **Тестовые данные** — обязательно (демо-набор + seed-скрипт).
- **Модель UI “Исследование → Версии бюджета”** — оптимальная для сценарного анализа.
- **Экспорт в XLSX** — соответствует требованиям бизнеса.
- **Фокус на core-функциях** — верный при сжатых сроках.

## 3) Финальный облик системы (MVP+)

### 3.1 Основные сущности
1. **Study (Клиническое исследование)**
   - `id`, `name` (unique), `indication`, `phase`, `status`, `created_at`
2. **BudgetVersion (Версия бюджета)**
   - `id`, `study_id`, `name` (например, Baseline / Amend-1), `assumptions_json`, `currency`, `created_by`, `created_at`, `is_locked`
3. **BudgetItem (Статья расходов)**
   - `id`, `budget_version_id`, `category`, `subcategory`, `item_name`, `unit`, `unit_cost`, `qty_formula_type`, `manual_qty`, `notes`
4. **ScenarioRun (Рассчитанный сценарий для версии)**
   - `id`, `budget_version_id`, `label`, `patients`, `sites`, `visits`, `extra_params_json`, `calculated_totals_json`, `created_at`
5. **AIReport**
   - `id`, `scenario_run_id` (или pair для compare), `report_type` (structure/justification/compare/optimization), `prompt_version`, `model`, `input_snapshot_json`, `output_text`, `created_at`

### 3.2 Категории бюджета (базовая таксономия)
- **Sites** (оплата площадок: визиты/процедуры/инклюзия)
- **Monitoring** (инициация, мониторинговые визиты, close-out)
- **Laboratory** (центральная/локальная лаборатория, анализы)
- **Logistics** (доставка/хранение/температурная логистика)
- (опционально) **Project Management / Vendor / Regulatory**

### 3.3 Математика расчёта
Для каждой статьи:
- `line_total = unit_cost * effective_qty`
- `effective_qty` зависит от типа статьи:
  - per-patient: `patients`
  - per-visit: `patients * visits`
  - per-site: `sites`
  - per-site-visit: `sites * monitoring_visits_per_site`
  - fixed: `manual_qty`

Итоги:
- `category_total = Σ line_total within category`
- `grand_total = Σ all category_total`
- `% category_share = category_total / grand_total`

### 3.4 Сценарии и сравнение
- Внутри одной версии создаются сценарии (например, 80/12/6 и 120/20/8).
- Side-by-side таблица:
  - абсолютная разница: `delta = B - A`
  - относительная: `delta_pct = (B - A) / A`
- Подсветка:
  - красный: рост > +10%
  - зелёный: снижение < -10%
  - нейтральный: -10%…+10%

### 3.5 AI-функции (обязательные)
1. **Анализ структуры**: top-драйверы затрат, доли категорий, концентрация бюджета.
2. **Потенциал оптимизации**: где снижать cost без ущерба data quality.
3. **Обоснование для руководства**: 1-page narrative на человеческом языке.
4. **Сравнение сценариев**: объяснение, почему B дороже/дешевле A и за счёт каких статей.

## 4) Рекомендуемый технологический стек

### 4.1 Frontend
- **Next.js 14 (App Router) + TypeScript**
- **UI**: shadcn/ui + Tailwind CSS
- **Charts**: Recharts
- **Таблицы**: TanStack Table
- **State/Form**: React Hook Form + Zod

Почему: быстро сделать «приятный» UI, хорошие компоненты, высокая скорость MVP.

### 4.2 Backend
- **NestJS (TypeScript)** или **FastAPI (Python)**.
- Для скорости и единообразия с Next.js рекомендую **NestJS**.
- API: REST (достаточно для MVP).
- Валидация DTO: class-validator / Zod контрактно.

### 4.3 База данных
- **PostgreSQL**
- ORM: **Prisma**
- Миграции: Prisma Migrate
- Seed: Prisma seed script (тестовые исследования, версии, статьи)

### 4.4 AI-интеграция
- Провайдер: **OpenRouter API** (через server-side only)
- Рекомендуемый паттерн:
  - backend endpoint получает структурированные данные сценария
  - собирает deterministic prompt
  - вызывает OpenRouter
  - сохраняет prompt snapshot + ответ в `AIReport`
- Фолбэк: при недоступности AI — отдавать “analysis unavailable”, чтобы UI не ломался.

### 4.5 Экспорт XLSX
- Node библиотека: **exceljs**
- Формат экспорта:
  - Лист 1: Summary (итоги и категории)
  - Лист 2: Line Items (все статьи)
  - Лист 3: Scenario Compare (если выбраны 2+ сценария)

### 4.6 Инфраструктура / деплой
- Docker + docker-compose
- Nginx/Caddy reverse proxy + Let’s Encrypt
- PM2 не нужен при контейнерах
- Логи: stdout + ротация на уровне Docker
- ENV: `.env` / `.env.production` (OPENROUTER_API_KEY только на сервере)

## 5) Минимальный состав экранов (UI)
1. **Studies List** (карточки исследований, кнопка создать)
2. **Study Details** (версии бюджета + метаданные)
3. **Budget Version Editor** (таблица статей, параметры, пересчёт)
4. **Scenario Compare** (A/B/С сравнение)
5. **AI Insights** (структура, оптимизация, обоснование, compare summary)
6. **Export Panel** (скачать XLSX)

## 6) API-контракты (черновой минимум)
- `POST /studies`
- `GET /studies`
- `POST /studies/:id/versions`
- `GET /versions/:id`
- `POST /versions/:id/items`
- `POST /versions/:id/scenarios/recalculate`
- `POST /ai/structure-analysis`
- `POST /ai/justification`
- `POST /ai/compare`
- `GET /scenarios/:id/export.xlsx`

## 7) AI prompt framework (чтобы ответы были стабильными)

### 7.1 System prompt (суть)
- Ты финансовый аналитик клинических исследований.
- Не выдумывай данные, используй только переданный JSON.
- Выдавай: краткое резюме, топ-5 драйверов, риски, 3-5 рекомендаций по оптимизации без ущерба качеству данных.

### 7.2 Guardrails
- Явно просить “не медицинские рекомендации, только бюджет/операции”.
- Если данных не хватает — перечислить, чего не хватает.
- Форматировать ответ в markdown секции для прямого рендера на UI.

## 8) Тестовые данные (обязательный seed)
Нужно создать минимум:
- 5 исследований
- в каждом 2–3 версии бюджета
- в каждой версии 30–80 статей
- 2–3 сценария на версию

Это позволит демонстрировать сравнение и AI-анализ на реалистичной нагрузке.

## 9) Нефункциональные требования (реально важные)
- Время пересчёта сценария: < 1 сек на 500 строк
- Время ответа AI: 3–15 сек (асинхронный индикатор загрузки)
- Аудит изменений: кто/когда создал версию и сценарий
- Идемпотентность перерасчёта (при одинаковом input один и тот же result)

## 10) Безопасность и эксплуатация
- Ключ OpenRouter хранить только на backend.
- Rate limit на AI endpoints (чтобы не сжечь токен).
- Базовая auth (email/password или magic link) — хотя бы role `admin/editor/viewer`.
- Логировать вызовы AI без PII.

## 11) План реализации по этапам (короткий срок)
1. Скелет проекта + БД + миграции + seed.
2. CRUD исследований/версий/статей.
3. Модуль расчёта и сценарии.
4. Сравнение сценариев + UI-дифф.
5. AI endpoints через OpenRouter.
6. XLSX экспорт.
7. Полировка UI + e2e smoke + деплой.

## 12) Definition of Done (чек-лист сдачи)
- Можно создать исследование, версию, статьи и пересчитать бюджет.
- Есть сравнение минимум двух сценариев с дельтами.
- Есть AI-анализ структуры, оптимизации и текст обоснования.
- Есть экспорт в XLSX.
- Проект развёрнут на сервере, доступен по URL.
- Есть демо-данные для показа и тестирования.

## 13) Готовый контекст для переноса в новый чат
**Проект:** CTBaiCalc — веб-сервис расчёта бюджета клинических исследований с AI.
**Иерархия данных:** Study → BudgetVersion → BudgetItems + ScenarioRuns.
**Ключевые функции:** расчёт категорий и total, сценарный пересчёт, side-by-side compare, AI-анализ/оптимизация/обоснование, экспорт XLSX.
**AI-провайдер:** OpenRouter (server-side key).
**Стек:** Next.js + NestJS + PostgreSQL + Prisma + Tailwind/shadcn + Recharts + exceljs + Docker.
**Ограничение:** короткий срок, фокус на core value, без избыточной сложности.
