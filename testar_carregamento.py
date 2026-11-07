from src.carregamento import (
    ErroCarregamento,
    carregar_planilha,
)
from src.limpeza import limpar_dados
from src.validacoes import executar_validacoes


CAMINHO_ARQUIVO = "data/exemplo_operacional.xlsx"


try:
    dataframe_original = carregar_planilha(
        CAMINHO_ARQUIVO
    )

    dataframe_limpo = limpar_dados(
        dataframe_original
    )

    alertas = executar_validacoes(
        dataframe_limpo
    )

    print("Análise concluída com sucesso.")

    print(
        f"Registros analisados: {len(dataframe_limpo)}"
    )

    print(
        f"Total de alertas: {len(alertas)}"
    )

    print("\nQuantidade por problema:")

    print(
        alertas["codigo_problema"]
        .value_counts()
        .to_string()
    )



    print("\nPossíveis duplicidades:")

    duplicidades = alertas[
        alertas["codigo_problema"]
        == "POSSIVEL_DUPLICIDADE"
    ]

    print(
        duplicidades[
            [
                "id_linha",
                "id_servico",
                "codigo_problema",
                "mensagem",
            ]
        ].to_string(index=False)
    )
    print("\nHodômetros inválidos:")

    hodometros_invalidos = alertas[
        alertas["codigo_problema"]
        == "HODOMETRO_INVALIDO"
        ]

    print(
        hodometros_invalidos[
            [
                "id_linha",
                "id_servico",
                "codigo_problema",
                "mensagem",
            ]
        ].to_string(index=False)
    )


except ErroCarregamento as erro:
    print(erro)