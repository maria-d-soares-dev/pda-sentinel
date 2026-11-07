from src.carregamento import (
    ErroCarregamento,
    carregar_planilha,
)
from src.indicadores import (
    calcular_indicadores,
    contar_por_problema,
    gerar_resumo_indicadores,
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

    indicadores = calcular_indicadores(
        dataframe_limpo,
        alertas,
    )

    problemas = contar_por_problema(
        alertas
    )

    resumo = gerar_resumo_indicadores(
        dataframe_limpo,
        alertas,
    )

    print("Análise concluída com sucesso.")

    print(
        f"Registros analisados: "
        f"{indicadores['registros_analisados']}"
    )

    print(
        f"Registros com alerta: "
        f"{indicadores['registros_com_alerta']}"
    )

    print(
        f"Total de alertas: "
        f"{indicadores['total_alertas']}"
    )

    print(
        f"Alertas críticos: "
        f"{indicadores['alertas_criticos']}"
    )

    print(
        f"Alertas de atenção: "
        f"{indicadores['alertas_atencao']}"
    )

    print(
        f"Alertas informativos: "
        f"{indicadores['alertas_informativos']}"
    )

    print("\nQuantidade de alertas por problema:")

    if problemas.empty:
        print("Nenhum alerta encontrado.")

    else:
        print(
            problemas.to_string(index=False)
        )

    print("\nPrimeiros 20 alertas:")

    if alertas.empty:
        print("Nenhum alerta encontrado.")

    else:
        colunas_exibidas = [
            "celula",
            "id_linha",
            "id_servico",
            "codigo_problema",
            "severidade",
            "mensagem",
        ]

        print(
            alertas[
                colunas_exibidas
            ]
            .head(20)
            .to_string(index=False)
        )

    print("\nResumo para exportação:")

    print(
        resumo.to_string(index=False)
    )

except ErroCarregamento as erro:
    print("Erro ao carregar a planilha:")
    print(erro)

except KeyError as erro:
    print("Erro durante o processamento dos dados:")
    print(f"Coluna não encontrada: {erro}")

except (TypeError, ValueError) as erro:
    print("Erro durante a análise dos dados:")
    print(erro)