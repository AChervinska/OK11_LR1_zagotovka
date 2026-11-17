
import csv
import statistics
import requests
import matplotlib.pyplot as plt

URL = "http://127.0.0.1:8000/predict"

base_texts = [
    "Great course!",
    "I really enjoyed this lesson.",
    "This experience was terrible.",
    "FastAPI is useful for building AI services.",
    "Machine learning can solve complex problems.",
    "I am disappointed with this application.",
]

# 30 текстів різної довжини
texts = [
    base_texts[i % len(base_texts)] * (1 + i // 6)
    for i in range(30)
]

# Прогрів моделі
warmup = requests.post(
    URL,
    json={"text": "Warmup request"},
    timeout=120
)
warmup.raise_for_status()

measurements = []

for i, text in enumerate(texts, start=1):
    response = requests.post(
        URL,
        json={"text": text},
        timeout=120
    )
    response.raise_for_status()

    data = response.json()

    measurements.append({
        "number": i,
        "length": len(text),
        "latency_ms": data["latency_ms"]
    })

    print(
        f"{i}: length={len(text)}, "
        f"latency={data['latency_ms']:.2f} ms"
    )

latencies = [x["latency_ms"] for x in measurements]

median = statistics.median(latencies)
p95 = sorted(latencies)[
    int(len(latencies) * 0.95) - 1
]

print(f"\nMedian: {median:.2f} ms")
print(f"P95: {p95:.2f} ms")

with open(
    "latency_results.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["number", "length", "latency_ms"]
    )
    writer.writeheader()
    writer.writerows(measurements)

plt.figure(figsize=(9, 5))

plt.scatter(
    [x["length"] for x in measurements],
    latencies
)

plt.xlabel("Text length (characters)")
plt.ylabel("Latency (ms)")
plt.title("Inference latency vs text length")
plt.grid(True)

plt.tight_layout()
plt.savefig("latency_chart.png", dpi=200)
plt.close()
