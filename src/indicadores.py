import pandas as pd


def contar_por_severidade(alertas):
    """Conta a quantidade de alertas de cada severidade."""

    if alertas.empty:
        return {
            "Crítica": 0,
            "Atenção": 0,
            "Informativa": 0,
        }

    contagem = (
        alertas["severidade"]
        .value_counts()
        .to_dict()
    )

    return {
        "Crítica": contagem.get("Crítica", 0),
        "Atenção": contagem.get("Atenção", 0),
        "Informativa": contagem.get("Informativa", 0),
    }


def contar_por_problema(alertas):
    """Retorna uma tabela com a quantidade por problema."""

    colunas_resultado = [
        "codigo_problema",
        "quantidade",
    ]

    if alertas.empty:
        return pd.DataFrame(
            columns=colunas_resultado
        )

    contagem = (
        alertas["codigo_problema"]
        .value_counts()
        .rename_axis("codigo_problema")
        .reset_index(name="quantidade")
    )

    return contagem


def calcular_indicadores(dataframe, alertas):
    """Calcula os indicadores gerais da análise."""

    severidades = contar_por_severidade(alertas)

    if alertas.empty:
        registros_com_alerta = 0
    else:
        registros_com_alerta = (
            alertas["id_linha"].nunique()
        )

    return {
        "registros_analisados": len(dataframe),
        "registros_com_alerta": registros_com_alerta,
        "total_alertas": len(alertas),
        "alertas_criticos": severidades["Crítica"],
        "alertas_atencao": severidades["Atenção"],
        "alertas_informativos": severidades[
            "Informativa"
        ],
    }


def gerar_resumo_indicadores(dataframe, alertas):
    """Gera uma tabela de resumo para exportação."""

    indicadores = calcular_indicadores(
        dataframe,
        alertas,
    )

    return pd.DataFrame(
        [
            {
                "indicador": "Registros analisados",
                "valor": indicadores[
                    "registros_analisados"
                ],
            },
            {
                "indicador": "Registros com alerta",
                "valor": indicadores[
                    "registros_com_alerta"
                ],
            },
            {
                "indicador": "Total de alertas",
                "valor": indicadores["total_alertas"],
            },
            {
                "indicador": "Alertas críticos",
                "valor": indicadores[
                    "alertas_criticos"
                ],
            },
            {
                "indicador": "Alertas de atenção",
                "valor": indicadores[
                    "alertas_atencao"
                ],
            },
            {
                "indicador": "Alertas informativos",
                "valor": indicadores[
                    "alertas_informativos"
                ],
            },
        ]
    )