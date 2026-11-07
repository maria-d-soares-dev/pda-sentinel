from pathlib import Path
from typing import BinaryIO

import pandas as pd

COLUNAS_OBRIGATORIAS = {
    "id_servico",
    "data_servico",
    "equipe",
    "tipo_servico",
    "hora_inicio",
    "hora_fim",
    "km_inicial",
    "km_final",
    "km_informada",
    "status",
    "localidade",
    "observacao",
}


class ErroCarregamento(Exception):
    """Erro compreensível ocorrido durante o carregamento do arquivo."""


def validar_extensao(nome_arquivo: str) -> None:
    """
    Verifica se o arquivo possui a extensão .xlsx.

    Não retorna nenhum valor quando a extensão é válida.
    Levanta ErroCarregamento quando a extensão é inválida.
    """

    extensao = Path(nome_arquivo).suffix.lower()

    if extensao != ".xlsx":
        raise ErroCarregamento(
            "Formato de arquivo inválido. "
            "Envie uma planilha no formato .xlsx."
        )


def identificar_colunas_ausentes(
    dataframe: pd.DataFrame,
) -> list[str]:
    """Retorna uma lista ordenada das colunas obrigatórias ausentes."""

    colunas_encontradas = set(dataframe.columns)

    colunas_ausentes = (
        COLUNAS_OBRIGATORIAS - colunas_encontradas
    )

    return sorted(colunas_ausentes)


def validar_colunas(dataframe: pd.DataFrame) -> None:
    """
    Verifica se todas as colunas obrigatórias estão presentes.

    Levanta ErroCarregamento quando alguma coluna está ausente.
    """

    colunas_ausentes = identificar_colunas_ausentes(
        dataframe
    )

    if colunas_ausentes:
        lista_colunas = "\n".join(
            f"- {coluna}"
            for coluna in colunas_ausentes
        )

        raise ErroCarregamento(
            "Não foi possível analisar o arquivo.\n\n"
            "Colunas ausentes:\n"
            f"{lista_colunas}"
        )


def carregar_planilha(
    arquivo: str | Path | BinaryIO,
    nome_arquivo: str | None = None,
) -> pd.DataFrame:
    """
    Carrega um arquivo Excel e verifica suas colunas.

    O parâmetro arquivo pode ser:
    - um caminho local;
    - um arquivo enviado pelo Streamlit;
    - um objeto binário compatível com pandas.

    O nome_arquivo é necessário para verificar a extensão de
    arquivos enviados pela interface.
    """

    if isinstance(arquivo, (str, Path)):
        caminho = Path(arquivo)
        validar_extensao(caminho.name)

        if not caminho.exists():
            raise ErroCarregamento(
                f"O arquivo não foi encontrado: {caminho}"
            )

    elif nome_arquivo is not None:
        validar_extensao(nome_arquivo)

    try:
        dataframe = pd.read_excel(
            arquivo,
            engine="openpyxl",
        )

    except FileNotFoundError as erro:
        raise ErroCarregamento(
            "O arquivo informado não foi encontrado."
        ) from erro

    except ValueError as erro:
        raise ErroCarregamento(
            "Não foi possível interpretar a planilha. "
            "Verifique se o arquivo é um Excel válido."
        ) from erro

    except OSError as erro:
        raise ErroCarregamento(
            "Não foi possível abrir o arquivo. "
            "Verifique se ele está disponível e não está corrompido."
        ) from erro

    if dataframe.empty:
        raise ErroCarregamento(
            "A planilha está vazia."
        )

    validar_colunas(dataframe)

    return dataframe