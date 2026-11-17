"""Converte os cortes binários originais do CThead em imagens TIFF de 16 bits."""

from pathlib import Path

import numpy as np

from leitura import ler_tiff, salvar_tiff

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "original" / "raw"
TIFF_DIR = PROJECT_ROOT / "data" / "original" / "tiff"
SLICE_COUNT = 113
IMAGE_SHAPE = (256, 256)
BYTES_PER_SLICE = IMAGE_SHAPE[0] * IMAGE_SHAPE[1] * 2


def convert_slices() -> None:
    """Converte os cortes big-endian, sem alterar os valores dos pixels."""
    TIFF_DIR.mkdir(parents=True, exist_ok=True)

    converted_count = 0
    for index in range(1, SLICE_COUNT + 1):
        raw_path = RAW_DIR / f"CThead.{index}"
        tiff_path = TIFF_DIR / f"cthead-{index:03}.tif"

        if not raw_path.is_file():
            raise FileNotFoundError(f"Corte original não encontrado: {raw_path}")

        raw_data = raw_path.read_bytes()
        if len(raw_data) != BYTES_PER_SLICE:
            raise ValueError(
                f"{raw_path.name} tem {len(raw_data)} bytes; "
                f"eram esperados {BYTES_PER_SLICE}."
            )

        pixels = (
            np.frombuffer(raw_data, dtype=">u2")
            .astype(np.uint16)
            .reshape(IMAGE_SHAPE)
        )
        if tiff_path.exists():
            existing_pixels = ler_tiff(tiff_path)
            if not np.array_equal(existing_pixels, pixels):
                raise ValueError(
                    f"O TIFF existente não corresponde ao corte original: {tiff_path}"
                )
        else:
            salvar_tiff(tiff_path, pixels)
        converted_count += 1

    print(f"Cortes convertidos e verificados: {converted_count}")
    print(f"TIFFs: {TIFF_DIR}")


if __name__ == "__main__":
    convert_slices()
