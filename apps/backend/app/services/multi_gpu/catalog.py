"""GPU SKU catalog — H100, A100, L40S, RTX, Cloud."""

from __future__ import annotations

from app.services.multi_gpu.models import GpuCapabilities, GpuSku

GPU_SKUS: tuple[GpuSku, ...] = ("H100", "A100", "L40S", "RTX", "CLOUD")

CAPABILITIES: dict[GpuSku, GpuCapabilities] = {
    "H100": GpuCapabilities(
        sku="H100",
        vram_mb=81920,
        fp16_tflops=1979.0,
        supports_rt=False,
        supports_nvlink=True,
        cloud=True,
        notes="Top-tier training/inference; prefer cinema / heavy particle / multi-scene",
    ),
    "A100": GpuCapabilities(
        sku="A100",
        vram_mb=40960,
        fp16_tflops=312.0,
        supports_rt=False,
        supports_nvlink=True,
        cloud=True,
        notes="Strong production throughput; NVLink multi-GPU scaling",
    ),
    "L40S": GpuCapabilities(
        sku="L40S",
        vram_mb=49152,
        fp16_tflops=362.0,
        supports_rt=True,
        supports_nvlink=False,
        cloud=True,
        notes="Ray-tracing + inference hybrid; ideal for scene render RT path",
    ),
    "RTX": GpuCapabilities(
        sku="RTX",
        vram_mb=24576,
        fp16_tflops=165.0,
        supports_rt=True,
        supports_nvlink=False,
        cloud=False,
        notes="Workstation / edge RTX class; draft–production RT capable",
    ),
    "CLOUD": GpuCapabilities(
        sku="CLOUD",
        vram_mb=24576,
        fp16_tflops=120.0,
        supports_rt=True,
        supports_nvlink=False,
        cloud=True,
        notes="Generic cloud GPU pool (auto-mapped to available provider SKUs)",
    ),
}

# Quality / workload → preferred SKU order
PREFERENCE_BY_QUALITY: dict[str, list[GpuSku]] = {
    "draft": ["RTX", "CLOUD", "L40S", "A100", "H100"],
    "preview": ["L40S", "RTX", "CLOUD", "A100", "H100"],
    "production": ["A100", "L40S", "H100", "CLOUD", "RTX"],
    "cinema": ["H100", "A100", "L40S", "CLOUD", "RTX"],
}


def normalize_sku(value: str | None) -> GpuSku | None:
    if not value:
        return None
    key = value.strip().upper().replace(" ", "")
    aliases = {
        "H100": "H100",
        "NVIDIAH100": "H100",
        "A100": "A100",
        "NVIDIAA100": "A100",
        "L40S": "L40S",
        "L40": "L40S",
        "RTX": "RTX",
        "RTX4090": "RTX",
        "RTX5090": "RTX",
        "GEFORCERTX": "RTX",
        "CLOUD": "CLOUD",
        "CLOUDGPU": "CLOUD",
    }
    return aliases.get(key)  # type: ignore[return-value]


def caps(sku: GpuSku) -> GpuCapabilities:
    return CAPABILITIES[sku]


def preferred_skus(
    *,
    quality: str | None = None,
    require_rt: bool = False,
    min_vram_mb: int = 0,
) -> list[GpuSku]:
    q = (quality or "production").lower()
    order = list(PREFERENCE_BY_QUALITY.get(q, PREFERENCE_BY_QUALITY["production"]))
    out: list[GpuSku] = []
    for sku in order:
        c = CAPABILITIES[sku]
        if require_rt and not c.supports_rt:
            continue
        if c.vram_mb < min_vram_mb:
            continue
        out.append(sku)
    # Fallback: ignore RT filter if nothing matched
    if not out:
        out = [s for s in order if CAPABILITIES[s].vram_mb >= min_vram_mb] or list(order)
    return out
