from datetime import datetime, time

import pandas as pd

COLUNAS_TEXTO = [
    "id_servico",
    "equipe",
    "tipo_servico",
    "status",
    "localidade",
    "observacao",
]

COLUNAS_NUMERICAS = [
    "km_inicial",
    "km_final",
    "km_informada",
]

COLUNAS_HORARIO = [
    "hora_inicio",
    "hora_fim",
]


def padronizar_textos(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove espaços extras das colunas de texto."""

    for coluna in COLUNAS_TEXTO:
        dataframe[coluna] = (
            dataframe[coluna]
            .astype("string")
            .str.strip()
        )

    return dataframe


def converter_datas(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Converte a data do serviço para o formato de data do pandas."""

    dataframe["data_servico"] = pd.to_datetime(
        dataframe["data_servico"],
        errors="coerce",
        dayfirst=True,
    )

    return dataframe


def converter_horario(valor):
    """
    Converte diferentes representações de horário.

    Valores inválidos ou ausentes são convertidos para pd.NaT.
    """

    if pd.isna(valor):
        return pd.NaT

    if isinstance(valor, time):
        return valor

    if isinstance(valor, datetime):
        return valor.time()

    texto = str(valor).strip()

    formatos_aceitos = [
        "%H:%M:%S",
        "%H:%M",
    ]

    for formato in formatos_aceitos:
        try:
            return datetime.strptime(
                texto,
                formato,
            ).time()

        except ValueError:
            continue

    return pd.NaT


def converter_horarios(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Converte as colunas de horário sem interromper por valores inválidos."""

    for coluna in COLUNAS_HORARIO:
        dataframe[coluna] = dataframe[coluna].apply(
            converter_horario
        )

    return dataframe


def converter_colunas_numericas(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Converte as colunas de quilometragem para valores numéricos."""

    for coluna in COLUNAS_NUMERICAS:
        dataframe[coluna] = pd.to_numeric(
            dataframe[coluna],
            errors="coerce",
        )

    return dataframe


def adicionar_identificador_linha(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Adiciona um identificador estável para relacionar registros e alertas.

    O número começa em 2 porque a primeira linha do Excel é o cabeçalho.
    """

    dataframe.insert(
        0,
        "id_linha",
        range(2, len(dataframe) + 2),
    )

    return dataframe


def limpar_dados(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Cria uma cópia e executa todas as etapas de limpeza.

    O DataFrame original permanece inalterado.
    """

    dataframe_limpo = dataframe.copy()

    dataframe_limpo = padronizar_textos(
        dataframe_limpo
    )

    dataframe_limpo = converter_datas(
        dataframe_limpo
    )

    dataframe_limpo = converter_horarios(
        dataframe_limpo
    )

    dataframe_limpo = converter_colunas_numericas(
        dataframe_limpo
    )

    dataframe_limpo = adicionar_identificador_linha(
        dataframe_limpo
    )

    return dataframe_limpo