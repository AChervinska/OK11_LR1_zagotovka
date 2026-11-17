"""
Сервіс інференсу на FastAPI — ЛР1 з дисципліни
«Інтеграція та супровід систем штучного інтелекту».

БАЗОВИЙ РІВЕНЬ (кроки 1-10 інструкції): lifespan, /health, /predict.
ПОГЛИБЛЕНИЙ РІВЕНЬ (кроки 11-15, додатково): Dependency Injection,
/predict/batch, offload інференсу в thread pool, структуроване
логування запитів, конфігурація через змінні середовища.

Документація FastAPI (розділи, потрібні для цієї роботи):
- Request Body:      https://fastapi.tiangolo.com/tutorial/body/
- Response Model:    https://fastapi.tiangolo.com/tutorial/response-model/
- Handling Errors:   https://fastapi.tiangolo.com/tutorial/handling-errors/
- Lifespan events:   https://fastapi.tiangolo.com/advanced/events/
- Dependencies:      https://fastapi.tiangolo.com/tutorial/dependencies/
- Middleware:        https://fastapi.tiangolo.com/tutorial/middleware/
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.model import SentimentClassifier
from app.schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    HealthResponse,
    PredictionItem,
    PredictRequest,
    PredictResponse,
)

# Налаштування читаються зі змінних середовища (префікс OK11_) — поглиблений
# рівень; за замовчуванням поводиться так само, як хардкод-константа раніше.
settings = Settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("ok11.lr1")

# Єдиний екземпляр класифікатора на весь час життя процесу (базовий рівень).
classifier = SentimentClassifier(settings.model_name)


def get_classifier() -> SentimentClassifier:
    """
    FastAPI-залежність (Dependency Injection) над класифікатором — готова
    інфраструктура для кроку 11 (поглиблений рівень).

    Технічно це тонка обгортка над модульною глобальною змінною classifier:
    навмисно, щоб перехід ендпоінтів на Depends(get_classifier) НЕ ламав
    тести базового рівня — вони й далі підміняють classifier через
    monkeypatch(main_module, "classifier", ...), а ця функція щоразу читає
    актуальне (можливо, підмінене) значення глобальної змінної.
    """
    return classifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Завантаження моделі...")

    classifier.load()

    logger.info("Модель готова до роботи")

    yield

    logger.info("Завершення роботи сервісу")


app = FastAPI(
    title="Сервіс класифікації тональності тексту",
    description="ЛР1 · ОК11 «Інтеграція та супровід систем штучного інтелекту»",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health(
    clf: SentimentClassifier = Depends(get_classifier),
) -> HealthResponse:

    if not clf.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Модель ще не завантажена"
        )

    return HealthResponse(
        status="ok",
        model_name=clf.model_name
    )


@app.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    clf: SentimentClassifier = Depends(get_classifier),
) -> PredictResponse:

    if not clf.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Модель ще не завантажена"
        )

    start = time.perf_counter()

    label, score = await run_in_threadpool(
        clf.predict,
        request.text
    )

    latency_ms = (time.perf_counter() - start) * 1000

    return PredictResponse(
        label=label,
        score=score,
        latency_ms=latency_ms
    )


# =============================================================================
# ПОГЛИБЛЕНИЙ РІВЕНЬ — додаткові завдання (кроки 11-15 інструкції)
# =============================================================================


@app.post(
    "/predict/batch",
    response_model=BatchPredictResponse
)
async def predict_batch(
    request: BatchPredictRequest,
    clf: SentimentClassifier = Depends(get_classifier),
) -> BatchPredictResponse:

    if not clf.is_ready:
        raise HTTPException(
            status_code=503,
            detail="Модель ще не завантажена"
        )

    if len(request.texts) > settings.max_batch_size:
        raise HTTPException(
            status_code=422,
            detail=(
                "Розмір пакета перевищує ліміт "
                f"{settings.max_batch_size}"
            )
        )

    start = time.perf_counter()

    pairs = await run_in_threadpool(
        clf.predict_batch,
        request.texts
    )

    total_latency_ms = (
        time.perf_counter() - start
    ) * 1000

    results = [
        PredictionItem(label=label, score=score)
        for label, score in pairs
    ]

    batch_size = len(results)

    throughput = (
        batch_size / (total_latency_ms / 1000)
        if total_latency_ms > 0
        else 0.0
    )

    return BatchPredictResponse(
        results=results,
        batch_size=batch_size,
        total_latency_ms=total_latency_ms,
        throughput_per_sec=throughput
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логування HTTP-запитів і виявлення повільних операцій."""

    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    if duration_ms > settings.slow_request_ms:
        logger.warning(
            "SLOW request_id=%s path=%s duration_ms=%.1f",
            request_id,
            request.url.path,
            duration_ms,
        )

    response.headers["X-Request-ID"] = request_id

    return response
