# CTBaiCalc — сервис расчёта бюджета клинических исследований с AI

Полноценный MVP-сервис «под ключ»:
- конструктор бюджета (статьи расходов, формулы количества, ставки);
- пересчёт сценариев по пациентам/площадкам/визитам;
- расчёт итогов по категориям и общей суммы;
- AI-анализ структуры бюджета через OpenRouter;
- сравнение сценариев (API);
- экспорт в XLSX;
- готовый деплой через Docker Compose.

---

## 1. Архитектура

### Backend
- FastAPI + SQLAlchemy + PostgreSQL
- Jinja2 + Bootstrap UI (серверный рендер + JS)
- OpenRouter integration (server-side key)
- Excel export через `openpyxl`

### Модель данных
- `Study` — исследование
- `BudgetVersion` — версия бюджета
- `BudgetItem` — строка бюджета
- `ScenarioRun` — результат пересчёта сценария
- `AIReport` — сохранённые AI-отчёты

### Логика расчёта
- `line_total = unit_cost * effective_qty`
- `effective_qty` определяется `qty_formula_type`:
  - `per-patient`
  - `per-visit`
  - `per-site`
  - `per-site-visit`
  - `fixed`
- Категории и общий итог считаются агрегированием строк.

---

## 2. Быстрый старт (Docker Compose)

### 2.1 Предусловия
- Docker
- Docker Compose plugin

### 2.2 Запуск
```bash
docker compose up --build -d
```

Сервис будет доступен на:
- `http://localhost:8000`

### 2.3 Переменные окружения
Создай `.env` рядом с `docker-compose.yml`:
```env
OPENROUTER_API_KEY=your_openrouter_token
OPENROUTER_MODEL=openrouter/auto
```

Если `OPENROUTER_API_KEY` не задан, AI-кнопка вернёт безопасный fallback-текст.

### 2.4 Остановка
```bash
docker compose down
```

С удалением тома БД:
```bash
docker compose down -v
```

---

## 3. Инструкция для пользователя

### Шаг 1. Создать исследование
На главной странице:
1. Ввести название исследования.
2. При необходимости indication.
3. Нажать «Создать».

### Шаг 2. Создать версию бюджета
В карточке исследования:
1. Нажать «Создать версию бюджета».
2. Открыть созданную версию.

### Шаг 3. Наполнить бюджет статьями
В версии бюджета:
1. Ввести наименование статьи.
2. Выбрать категорию (Sites/Monitoring/Laboratory/Logistics).
3. Выбрать формулу количества (`per-patient`, `per-visit`, и т.д.).
4. Указать ставку (`unit_cost`) и, если нужно, `manual qty`.
5. Нажать «Добавить».

### Шаг 4. Пересчитать сценарий
1. Ввести label сценария.
2. Указать `patients`, `sites`, `visits`.
3. Нажать «Пересчитать».
4. Получить:
   - `Grand total`;
   - таблицу итогов по категориям;
   - круговую диаграмму структуры затрат.

### Шаг 5. AI-анализ
После расчёта:
1. Нажать «AI анализ».
2. Система отправит snapshot сценария и топ-статей в OpenRouter.
3. Вернётся текстовый анализ: драйверы затрат и идеи оптимизации.

### Шаг 6. Экспорт XLSX
Нажать «XLSX» в блоке результата.
Файл содержит:
- лист `Summary`;
- лист `Line Items`.

---

## 4. API (основные endpoints)
- `POST /api/studies`
- `POST /api/studies/{study_id}/versions`
- `POST /api/versions/{version_id}/items`
- `POST /api/versions/{version_id}/scenarios/recalculate`
- `POST /api/ai/structure-analysis/{scenario_id}`
- `POST /api/ai/compare`
- `GET /api/scenarios/{scenario_id}/export.xlsx`

---

## 5. Локальная разработка без Docker
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
export DATABASE_URL=sqlite:///./ctb.db
python -m app.seed
uvicorn app.main:app --reload
```

---

## 6. Тестирование
```bash
pytest -q
```

---

## 7. Что уже реализовано относительно ТЗ
- ✅ Конструктор бюджета
- ✅ Расчёт категорий и total
- ✅ Сценарии пересчёта
- ✅ AI-анализ структуры и оптимизации (через OpenRouter)
- ✅ Сравнение сценариев (API)
- ✅ Экспорт в XLSX
- ✅ Готовый UI + контейнеризация

## 8. Ограничения текущего MVP
- Авторизация/роли не включены (можно добавить next iteration).
- Compare в UI не вынесен отдельным экраном (есть как API).
- AI-обоснование «для руководства» и отдельный формат compare-объяснений легко расширяются на базе текущего AI-слоя.
