from pathlib import Path

import pandas as pd

COLUNAS_OBRIGATORIAS = {
    "id_servico",
    "data_servico",
    "equipe",
    "tipo_servico",
    "hora_inicio",
    "status",
}

COLUNAS_RECOMENDADAS = {
    "hora_fim",
    "km_inicial",
    "km_final",
    "km_informada",
    "localidade",
    "observacao",
}


class ErroCarregamento(Exception):
    """Erro compreensível ocorrido durante o carregamento."""


def validar_extensao(nome_arquivo):
    """Verifica se o arquivo possui a extensão xlsx."""

    extensao = Path(nome_arquivo).suffix.lower()

    if extensao != ".xlsx":
        raise ErroCarregamento(
            "Formato de arquivo inválido. "
            "Envie uma planilha no formato .xlsx."
        )


def ler_planilha(
    arquivo,
    nome_arquivo=None,
):
    """Lê o Excel sem exigir nomes padronizados nas colunas."""

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

    return dataframe


def identificar_colunas_ausentes(dataframe):
    """Retorna as colunas obrigatórias ausentes."""

    colunas_encontradas = set(
        dataframe.columns
    )

    colunas_ausentes = (
        COLUNAS_OBRIGATORIAS
        - colunas_encontradas
    )

    return sorted(colunas_ausentes)


def identificar_colunas_recomendadas_ausentes(
    dataframe,
):
    """Retorna as colunas recomendadas ausentes."""

    colunas_encontradas = set(
        dataframe.columns
    )

    colunas_ausentes = (
        COLUNAS_RECOMENDADAS
        - colunas_encontradas
    )

    return sorted(colunas_ausentes)


def validar_colunas(dataframe):
    """Verifica se todas as colunas obrigatórias existem."""

    colunas_ausentes = identificar_colunas_ausentes(
        dataframe
    )

    if not colunas_ausentes:
        return

    lista_colunas = "\n".join(
        f"- {coluna}"
        for coluna in colunas_ausentes
    )

    raise ErroCarregamento(
        "Não foi possível analisar o arquivo.\n\n"
        "Campos obrigatórios ainda não associados:\n"
        f"{lista_colunas}"
    )


def adicionar_colunas_recomendadas(dataframe):
    """Adiciona como vazias as colunas recomendadas ausentes."""

    dataframe_completo = dataframe.copy()

    colunas_ausentes = (
        identificar_colunas_recomendadas_ausentes(
            dataframe_completo
        )
    )

    for coluna in colunas_ausentes:
        dataframe_completo[coluna] = pd.NA

    return dataframe_completo


def carregar_planilha(
    arquivo,
    nome_arquivo=None,
):
    """Lê, valida e prepara uma planilha já padronizada."""

    dataframe = ler_planilha(
        arquivo,
        nome_arquivo=nome_arquivo,
    )

    validar_colunas(
        dataframe
    )

    dataframe = adicionar_colunas_recomendadas(
        dataframe
    )

    return dataframe