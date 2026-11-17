"""Leitura de imagens TIFF e séries DICOM."""

from pathlib import Path

import cv2
import numpy as np
import pydicom


def ler_tiff(caminho: Path) -> np.ndarray:
    """Lê um TIFF em tons de cinza sem alterar sua profundidade de bits.

    Usar NumPy para ler os bytes e ``cv2.imdecode`` também funciona com
    diretórios do Windows que contêm caracteres acentuados.
    """
    dados = np.fromfile(caminho, dtype=np.uint8)
    if dados.size == 0:
        raise OSError(f"Arquivo TIFF vazio ou inacessível: {caminho}")

    imagem = cv2.imdecode(dados, cv2.IMREAD_UNCHANGED)
    if imagem is None:
        raise OSError(f"OpenCV não conseguiu decodificar o arquivo TIFF: {caminho}")
    if imagem.ndim != 2:
        raise ValueError(
            f"Esperava TIFF em tons de cinza; recebido formato {imagem.shape}: {caminho}"
        )
    return imagem


def salvar_tiff(caminho: Path, imagem: np.ndarray) -> None:
    """Codifica e grava uma matriz de pixels em um TIFF em tons de cinza."""
    if imagem.ndim != 2 or imagem.dtype != np.uint16:
        raise ValueError(
            "Esperava uma matriz 2D de pixels uint16 para salvar como TIFF."
        )

    sucesso, dados = cv2.imencode(".tif", imagem)
    if not sucesso:
        raise OSError(f"OpenCV não conseguiu codificar o TIFF: {caminho}")
    dados.tofile(caminho)


def ler_dicom_volume(
    diretorio: Path,
) -> tuple[np.ndarray, tuple[float, float, float], list[Path]]:
    """Lê uma série DICOM 2D e ordena os cortes pelas posições físicas.

    Retorna o volume na ordem ``(z, y, x)``, o espaçamento em milímetros
    nessa ordem e os caminhos correspondentes aos cortes carregados.
    """
    arquivos = sorted(diretorio.glob("*.dcm"), key=lambda caminho: caminho.name)
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo DICOM encontrado em: {diretorio}")

    fatias = []
    for caminho in arquivos:
        dataset = pydicom.dcmread(caminho)
        if "PixelData" not in dataset:
            raise ValueError(f"O arquivo não contém PixelData: {caminho}")

        pixels = dataset.pixel_array
        if pixels.ndim != 2:
            raise ValueError(
                f"Esperava uma fatia DICOM 2D; recebido formato {pixels.shape}: {caminho}"
            )
        if "SeriesInstanceUID" not in dataset:
            raise ValueError(f"O arquivo não identifica sua série DICOM: {caminho}")

        fatias.append((caminho, dataset, pixels))

    series_uids = {str(dataset.SeriesInstanceUID) for _, dataset, _ in fatias}
    if len(series_uids) != 1:
        raise ValueError(
            f"Esperava uma série DICOM; encontrei {len(series_uids)} em {diretorio}."
        )

    formas = {pixels.shape for _, _, pixels in fatias}
    if len(formas) != 1:
        raise ValueError(f"As dimensões das fatias DICOM não são iguais: {formas}.")

    pixel_spacings = [
        np.asarray(dataset.PixelSpacing, dtype=float)
        for _, dataset, _ in fatias
        if "PixelSpacing" in dataset
    ]
    if len(pixel_spacings) != len(fatias) or any(
        not np.allclose(spacing, pixel_spacings[0]) for spacing in pixel_spacings
    ):
        raise ValueError("PixelSpacing está ausente ou varia entre as fatias DICOM.")

    possuem_posicao = all(
        "ImagePositionPatient" in dataset and "ImageOrientationPatient" in dataset
        for _, dataset, _ in fatias
    )
    if possuem_posicao:
        orientacao = np.asarray(fatias[0][1].ImageOrientationPatient, dtype=float)
        normal = np.cross(orientacao[:3], orientacao[3:])
        normal_norm = np.linalg.norm(normal)
        if not np.isclose(normal_norm, 1.0, atol=1e-4):
            raise ValueError("ImageOrientationPatient inválido na série DICOM.")
        normal /= normal_norm

        for _, dataset, _ in fatias:
            outra_orientacao = np.asarray(
                dataset.ImageOrientationPatient, dtype=float
            )
            if not np.allclose(outra_orientacao, orientacao, atol=1e-4):
                raise ValueError("A orientação varia entre as fatias DICOM.")

        fatias.sort(
            key=lambda item: float(
                np.dot(
                    np.asarray(item[1].ImagePositionPatient, dtype=float), normal
                )
            )
        )
        posicoes = np.asarray(
            [
                np.dot(
                    np.asarray(dataset.ImagePositionPatient, dtype=float), normal
                )
                for _, dataset, _ in fatias
            ]
        )
        diferencas = np.diff(posicoes)
        if np.any(diferencas <= 0):
            raise ValueError("As posições DICOM dos cortes não são únicas.")
        if not np.all(np.isfinite(diferencas)):
            raise ValueError("Há posições DICOM inválidas na série.")
        espacamento_z = float(np.median(diferencas))
    elif all("InstanceNumber" in dataset for _, dataset, _ in fatias):
        fatias.sort(key=lambda item: int(item[1].InstanceNumber))
        espacamentos = []
        for _, dataset, _ in fatias:
            espacamento = getattr(dataset, "SpacingBetweenSlices", None)
            if espacamento is None:
                espacamento = getattr(dataset, "SliceThickness", None)
            if espacamento is None:
                raise ValueError(
                    "A série não informa o espaçamento entre cortes DICOM."
                )
            espacamentos.append(float(espacamento))
        espacamentos = np.asarray(espacamentos, dtype=float)
        if np.any(espacamentos <= 0):
            raise ValueError("O espaçamento entre as fatias DICOM é inválido.")
        espacamento_z = float(np.median(np.abs(espacamentos)))
    else:
        raise ValueError(
            "A série precisa informar posição/orientação ou InstanceNumber "
            "e espaçamento entre cortes."
        )

    volume = np.stack([pixels for _, _, pixels in fatias], axis=0)
    espacamento_y, espacamento_x = (float(valor) for valor in pixel_spacings[0])
    espacamento_zyx = (espacamento_z, espacamento_y, espacamento_x)
    caminhos_ordenados = [caminho for caminho, _, _ in fatias]
    return volume, espacamento_zyx, caminhos_ordenados
