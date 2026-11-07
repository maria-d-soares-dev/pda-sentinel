from src.exportacao import gerar_excel_resultado

from pathlib import Path

import plotly.express as px
import streamlit as st



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

st.set_page_config(
    page_title="PDA Sentinel",
    page_icon="🛡️",
    layout="wide",
)


st.title("PDA Sentinel")

st.subheader(
    "Validação responsável de registros operacionais"
)

st.info(
    "A aplicação sinaliza registros que precisam de revisão. "
    "Um alerta não significa necessariamente que o registro "
    "esteja definitivamente errado."
)


CAMINHO_EXEMPLO = Path(
    "data/exemplo_operacional.xlsx"
)


with st.sidebar:
    st.header("Arquivo")

    arquivo_enviado = st.file_uploader(
        "Envie uma planilha operacional",
        type=["xlsx"],
    )

    if CAMINHO_EXEMPLO.exists():
        conteudo_exemplo = CAMINHO_EXEMPLO.read_bytes()

        st.download_button(
            label="Baixar planilha de exemplo",
            data=conteudo_exemplo,
            file_name="exemplo_operacional.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

    usar_exemplo = st.checkbox(
        "Usar automaticamente a planilha de exemplo"
    )

    st.divider()

    st.caption(
        "Todos os dados da demonstração são sintéticos."
    )


if arquivo_enviado is None and not usar_exemplo:
    st.warning(
        "Envie uma planilha .xlsx ou selecione a planilha "
        "sintética de exemplo na barra lateral."
    )

    st.stop()


try:
    if arquivo_enviado is not None:
        dataframe_original = carregar_planilha(
            arquivo_enviado,
            nome_arquivo=arquivo_enviado.name,
        )

        nome_arquivo = arquivo_enviado.name

    else:
        dataframe_original = carregar_planilha(
            CAMINHO_EXEMPLO
        )

        nome_arquivo = CAMINHO_EXEMPLO.name

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
    resumo = gerar_resumo_indicadores(
        dataframe_limpo,
        alertas,
    )

    arquivo_excel = gerar_excel_resultado(
        dataframe_limpo,
        alertas,
        resumo,
    )

except ErroCarregamento as erro:
    st.error(str(erro))
    st.stop()

except (KeyError, TypeError, ValueError) as erro:
    st.error(
        "Não foi possível concluir a análise dos dados."
    )

    st.code(str(erro))

    st.stop()


st.success(
    f"Arquivo analisado: {nome_arquivo}"
)


coluna_1, coluna_2, coluna_3, coluna_4 = st.columns(
    4
)

coluna_1.metric(
    "Registros analisados",
    indicadores["registros_analisados"],
)

coluna_2.metric(
    "Registros com alerta",
    indicadores["registros_com_alerta"],
)

coluna_3.metric(
    "Alertas críticos",
    indicadores["alertas_criticos"],
)

coluna_4.metric(
    "Total de alertas",
    indicadores["total_alertas"],
)


st.divider()


if alertas.empty:
    st.success(
        "Nenhuma inconsistência foi encontrada."
    )

    st.subheader("Registros analisados")

    st.dataframe(
        dataframe_limpo,
        use_container_width=True,
        hide_index=True,
    )

    st.stop()


st.subheader("Filtros dos alertas")


coluna_filtro_1, coluna_filtro_2 = st.columns(2)


opcoes_severidade = sorted(
    alertas["severidade"]
    .dropna()
    .unique()
    .tolist()
)

severidades_selecionadas = coluna_filtro_1.multiselect(
    "Severidade",
    options=opcoes_severidade,
    default=opcoes_severidade,
)


opcoes_problemas = sorted(
    alertas["codigo_problema"]
    .dropna()
    .unique()
    .tolist()
)

problemas_selecionados = coluna_filtro_2.multiselect(
    "Tipo de problema",
    options=opcoes_problemas,
    default=opcoes_problemas,
)


alertas_filtrados = alertas[
    alertas["severidade"].isin(
        severidades_selecionadas
    )
    & alertas["codigo_problema"].isin(
        problemas_selecionados
    )
]


st.caption(
    f"{len(alertas_filtrados)} alerta(s) exibido(s)."
)


st.subheader("Alertas encontrados")


colunas_exibidas = [
    "celula",
    "id_linha",
    "id_servico",
    "codigo_problema",
    "severidade",
    "mensagem",
]

st.dataframe(
    alertas_filtrados[colunas_exibidas],
    use_container_width=True,
    hide_index=True,
    column_config={
        "celula": st.column_config.TextColumn(
            "Célula do Excel",
            help=(
                "Posição aproximada do dado no arquivo original."
            ),
        ),
        "id_linha": st.column_config.NumberColumn(
            "Linha do Excel"
        ),
        "id_servico": st.column_config.TextColumn(
            "ID do serviço"
        ),
        "codigo_problema": st.column_config.TextColumn(
            "Problema"
        ),
        "severidade": st.column_config.TextColumn(
            "Severidade"
        ),
        "mensagem": st.column_config.TextColumn(
            "Descrição",
            width="large",
        ),
    },
)


st.divider()


st.subheader("Quantidade de alertas por problema")


contagem_problemas = contar_por_problema(
    alertas_filtrados
)


if not contagem_problemas.empty:
    grafico = px.bar(
        contagem_problemas,
        x="quantidade",
        y="codigo_problema",
        orientation="h",
        labels={
            "quantidade": "Quantidade",
            "codigo_problema": "Problema",
        },
        title="Alertas por tipo de problema",
    )

    grafico.update_layout(
        yaxis={
            "categoryorder": "total ascending"
        }
    )

    st.plotly_chart(
        grafico,
        use_container_width=True,
    )


with st.expander("Ver registros analisados"):
    st.dataframe(
        dataframe_limpo,
        use_container_width=True,
        hide_index=True,
    )


with st.expander("Entenda as regras"):
    st.markdown(
        """
1. **CAMPO_AUSENTE:** campo obrigatório não informado.
2. **POSSIVEL_DUPLICIDADE:** mesma combinação de ID, data e equipe.
3. **HORARIO_INVALIDO:** horário final anterior ao inicial.
4. **DURACAO_ATIPICA:** duração superior a seis horas.
5. **HODOMETRO_INVALIDO:** hodômetro final menor que o inicial.
6. **DIVERGENCIA_QUILOMETRAGEM:** diferença relevante entre quilometragens.
7. **CONCLUSAO_INCOMPLETA:** concluído sem horário final.
8. **QUILOMETRAGEM_ATIPICA:** valor inválido, negativo ou acima de 500 km.
9. **SOBREPOSICAO_DE_AGENDA:** horários sobrepostos para a mesma equipe.
10. **EXCECAO_SEM_JUSTIFICATIVA:** exceção sem observação.
        """
    )

    st.divider()

    st.subheader("Exportar resultado")

    st.write(
        "Baixe o relatório completo com os registros analisados, "
        "os alertas identificados e o resumo dos indicadores."
    )

    st.download_button(
        label="Baixar relatório em Excel",
        data=arquivo_excel,
        file_name="resultado_pda_sentinel.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        type="primary",
    )