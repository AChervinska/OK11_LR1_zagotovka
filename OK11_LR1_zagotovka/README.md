# ЛР1 · Побудова сервісу інференсу на FastAPI

Повний текст інструкції з теорією, покроковим ходом роботи, посиланнями
на документацію, контрольними питаннями та критеріями оцінювання —
у файлі `ЛР1_Методичні_вказівки.docx` поруч із цим репозиторієм.
Цей README — лише технічна навігація по коду.

Робота має **два рівні**:

- **Базовий (обов'язковий)** — кроки 1–10: FastAPI-сервіс з lifespan,
  `/health`, `/predict`. Перевіряється `pytest -m "not advanced"`.
- **Поглиблений (додатково)** — кроки 11–15: Dependency Injection,
  пакетний ендпоінт `/predict/batch`, offload інференсу в thread pool,
  конфігурація через змінні середовища, структуроване логування.
  Перевіряється `pytest -m advanced`.

## Структура

```
app/
  __init__.py
  schemas.py    — готовий контракт API, базовий + пакетний (не редагувати)
  config.py     — готові налаштування через змінні середовища (не редагувати)
  model.py      — TODO: predict()/load() (базовий), predict_batch() (поглиблений)
  main.py       — TODO: lifespan, /health, /predict (базовий);
                        Depends, /predict/batch, run_in_threadpool (поглиблений)
tests/
  conftest.py          — фікстури з фейковим класифікатором (не редагувати)
  test_api.py          — контрактні тести базового рівня
  test_batch.py         [advanced] — тести /predict/batch
  test_concurrency.py   [advanced] — тест на блокування event loop
  test_real_model.py    — тест на реальній моделі (запускати вручну)
requirements.txt
pytest.ini
```

## Встановлення

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Порядок виконання

**Базовий рівень**

1. Прочитати `ЛР1_Методичні_вказівки.docx`, розділ «Хід роботи», кроки 1–10.
2. `pytest -m "not advanced" -v` — усі 7 мають впасти з `NotImplementedError`.
3. Реалізувати TODO в `app/model.py` (load, predict) та `app/main.py` (lifespan, /health, /predict).
4. `pytest -m "not advanced" -v` — усі 7 мають позеленіти.
5. `uvicorn app.main:app --reload`, перевірка вручну через http://127.0.0.1:8000/docs.
6. Замір латентності на наборі текстів (крок 8 інструкції).

**Поглиблений рівень (додатково)**

7. Прочитати кроки 11–15 інструкції.
8. Реалізувати `predict_batch()` в `app/model.py`.
9. Відредагувати `/health` і `/predict`: додати `Depends(get_classifier)`,
   обгорнути виклик моделі в `run_in_threadpool`.
10. Реалізувати `/predict/batch` в `app/main.py`.
11. `pytest -m advanced -v` — усі 7 мають позеленіти, зокрема
    `test_concurrency.py`, що демонструє звільнення event loop.
12. Заміряти пропускну здатність `/predict/batch` проти послідовних
    викликів `/predict` — порівняння додається до звіту.

**Опційно**

```bash
RUN_SLOW=1 pytest tests/test_real_model.py -v
```

## Типові проблеми

Див. розділ «Типові помилки» методички. Коротко: якщо перший запит
до `/predict` займає секунди — модель вантажиться не там, де треба.
Якщо `test_concurrency.py` падає з часом ≈0.4с замість <0.2с —
виклик моделі не офлоаджено в thread pool.
