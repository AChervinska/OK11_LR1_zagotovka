
import csv
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000"
OUT = Path("results")
OUT.mkdir(exist_ok=True)

sizes = [5, 10, 20, 30, 50]
rows = []

for size in sizes:
    texts = [
        f"This is sample sentence number {i}. "
        "The application is working correctly."
        for i in range(size)
    ]

    # Послідовний інференс
    start = time.perf_counter()

    for text in texts:
        response = requests.post(
            f"{BASE_URL}/predict",
            json={"text": text},
            timeout=120
        )
        response.raise_for_status()

    sequential_ms = (time.perf_counter() - start) * 1000

    # Пакетний інференс
    start = time.perf_counter()

    response = requests.post(
        f"{BASE_URL}/predict/batch",
        json={"texts": texts},
        timeout=120
    )
    response.raise_for_status()

    batch_ms = (time.perf_counter() - start) * 1000

    throughput = size / (batch_ms / 1000)

    rows.append({
        "batch_size": size,
        "sequential_ms": round(sequential_ms, 2),
        "batch_ms": round(batch_ms, 2),
        "throughput_per_sec": round(throughput, 2)
    })

    print(
        f"{size} texts | "
        f"Sequential: {sequential_ms:.2f} ms | "
        f"Batch: {batch_ms:.2f} ms | "
        f"Throughput: {throughput:.2f} texts/s"
    )

with open(
    OUT / "batch_comparison.csv",
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(rows)

print("\nResults saved to results/batch_comparison.csv")
