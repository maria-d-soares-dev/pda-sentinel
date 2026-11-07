from pathlib import Path

import plotly.express as px
import streamlit as st

from src.carregamento import (
    COLUNAS_OBRIGATORIAS,
    COLUNAS_RECOMENDADAS,
    ErroCarregamento,
    adicionar_colunas_recomendadas,
    ler_planilha,
    validar_colunas,
)
from src.exportacao import gerar_excel_resultado
from src.indicadores import (
    calcular_indicadores,
    contar_por_problema,
    gerar_resumo_indicadores,
)
from src.limpeza import limpar_dados
from src.mapeamento import (
    COLUNAS_PADRAO,
    ROTULOS_COLUNAS,
    sugerir_mapeamento,
)
from src.validacoes import executar_validacoes

st.set_page_config(
    page_title="PDA Sentinel",
    page_icon="🛡️",
    layout="wide",
)


CAMINHO_EXEMPLO = Path(
    "data/exemplo_operacional.xlsx"
)

OPCAO_NAO_DISPONIVEL = "Não disponível"


REGRAS_POR_DEPENDENCIA = {
    "hora_fim": {
        "HORARIO_INVALIDO",
        "DURACAO_ATIPICA",
        "CONCLUSAO_INCOMPLETA",
        "SOBREPOSICAO_DE_AGENDA",
    },
    "km_inicial": {
        "HODOMETRO_INVALIDO",
        "DIVERGENCIA_QUILOMETRAGEM",
        "QUILOMETRAGEM_ATIPICA",
    },
    "km_final": {
        "HODOMETRO_INVALIDO",
        "DIVERGENCIA_QUILOMETRAGEM",
        "QUILOMETRAGEM_ATIPICA",
    },
    "km_informada": {
        "DIVERGENCIA_QUILOMETRAGEM",
        "QUILOMETRAGEM_ATIPICA",
    },
    "observacao": {
        "EXCECAO_SEM_JUSTIFICATIVA",
    },
}


def limpar_resultado_anterior():
    """Remove resultados armazenados de uma análise anterior."""

    chaves = [
        "dataframe_limpo",
        "alertas",
        "indicadores",
        "resumo",
        "arquivo_excel",
        "nome_arquivo_analisado",
        "campos_nao_mapeados",
        "regras_nao_executadas",
    ]

    for chave in chaves:
        st.session_state.pop(
            chave,
            None,
        )


def criar_assinatura_arquivo(
    arquivo_enviado,
    usar_exemplo,
):
    """Cria uma identificação simples para o arquivo atual."""

    if arquivo_enviado is not None:
        return (
            arquivo_enviado.name,
            arquivo_enviado.size,
        )

    if usar_exemplo:
        return (
            CAMINHO_EXEMPLO.name,
            CAMINHO_EXEMPLO.stat().st_size,
        )

    return None


def aplicar_mapeamento_parcial(
    dataframe,
    mapeamento,
):
    """Renomeia as colunas selecionadas para o padrão interno."""

    renomeacoes = {
        coluna_original: coluna_padrao
        for coluna_padrao, coluna_original
        in mapeamento.items()
    }

    return dataframe.rename(
        columns=renomeacoes
    ).copy()


def identificar_regras_nao_executadas(
    campos_nao_mapeados,
):
    """Identifica regras dependentes de campos indisponíveis."""

    regras = set()

    for campo in campos_nao_mapeados:
        regras.update(
            REGRAS_POR_DEPENDENCIA.get(
                campo,
                set(),
            )
        )

    return sorted(regras)


def remover_alertas_de_regras_indisponiveis(
    alertas,
    regras_nao_executadas,
):
    """Remove resultados de regras sem dados suficientes."""

    if alertas.empty:
        return alertas

    if not regras_nao_executadas:
        return alertas

    return alertas[
        ~alertas["codigo_problema"].isin(
            regras_nao_executadas
        )
    ].reset_index(drop=True)


st.title("PDA Sentinel")

st.subheader(
    "Validação responsável de registros operacionais"
)

st.info(
    "A aplicação sinaliza registros que precisam de revisão. "
    "Um alerta não significa necessariamente que o registro "
    "esteja definitivamente errado."
)


with st.sidebar:
    st.header("Arquivo")

    arquivo_enviado = st.file_uploader(
        "Envie uma planilha operacional",
        type=["xlsx"],
    )

    usar_exemplo = st.checkbox(
        "Usar a planilha sintética de exemplo"
    )

    if CAMINHO_EXEMPLO.exists():
        st.download_button(
            label="Baixar planilha de exemplo",
            data=CAMINHO_EXEMPLO.read_bytes(),
            file_name="exemplo_operacional.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )

    st.divider()

    st.caption(
        "Todos os dados da demonstração são sintéticos."
    )


if arquivo_enviado is None and not usar_exemplo:
    limpar_resultado_anterior()

    st.warning(
        "Envie uma planilha .xlsx ou selecione a planilha "
        "sintética de exemplo na barra lateral."
    )

    st.stop()


assinatura_arquivo = criar_assinatura_arquivo(
    arquivo_enviado,
    usar_exemplo,
)

assinatura_anterior = st.session_state.get(
    "assinatura_arquivo"
)

if assinatura_arquivo != assinatura_anterior:
    limpar_resultado_anterior()

    st.session_state[
        "assinatura_arquivo"
    ] = assinatura_arquivo


try:
    if arquivo_enviado is not None:
        dataframe_bruto = ler_planilha(
            arquivo_enviado,
            nome_arquivo=arquivo_enviado.name,
        )

        nome_arquivo = arquivo_enviado.name

    else:
        dataframe_bruto = ler_planilha(
            CAMINHO_EXEMPLO
        )

        nome_arquivo = CAMINHO_EXEMPLO.name

except ErroCarregamento as erro:
    st.error(str(erro))
    st.stop()


st.success(
    f"Arquivo aberto: {nome_arquivo}"
)


st.subheader("Correspondência das colunas")

st.write(
    "Confirme qual coluna do arquivo corresponde a cada "
    "campo usado pelo PDA Sentinel. Os campos marcados como "
    "obrigatórios precisam ser associados para iniciar a análise."
)


sugestoes = sugerir_mapeamento(
    dataframe_bruto.columns
)

opcoes = [
    OPCAO_NAO_DISPONIVEL,
    *dataframe_bruto.columns.tolist(),
]

mapeamento = {}

coluna_esquerda, coluna_direita = st.columns(2)


for indice, coluna_padrao in enumerate(
    COLUNAS_PADRAO
):
    sugestao = sugestoes.get(
        coluna_padrao
    )

    if sugestao in opcoes:
        indice_sugestao = opcoes.index(
            sugestao
        )

    else:
        indice_sugestao = 0

    if coluna_padrao in COLUNAS_OBRIGATORIAS:
        tipo_campo = "Obrigatório"

    else:
        tipo_campo = "Recomendado"

    recipiente = (
        coluna_esquerda
        if indice % 2 == 0
        else coluna_direita
    )

    coluna_selecionada = recipiente.selectbox(
        label=(
            f"{ROTULOS_COLUNAS[coluna_padrao]} "
            f"({tipo_campo})"
        ),
        options=opcoes,
        index=indice_sugestao,
        key=f"mapeamento_{coluna_padrao}",
        help=f"Campo interno: {coluna_padrao}",
    )

    if coluna_selecionada != OPCAO_NAO_DISPONIVEL:
        mapeamento[coluna_padrao] = (
            coluna_selecionada
        )


campos_obrigatorios_ausentes = sorted(
    COLUNAS_OBRIGATORIAS
    - set(mapeamento)
)

campos_recomendados_ausentes = sorted(
    COLUNAS_RECOMENDADAS
    - set(mapeamento)
)

colunas_selecionadas = list(
    mapeamento.values()
)

existem_repeticoes = (
    len(colunas_selecionadas)
    != len(set(colunas_selecionadas))
)


if campos_obrigatorios_ausentes:
    nomes_ausentes = [
        ROTULOS_COLUNAS[campo]
        for campo in campos_obrigatorios_ausentes
    ]

    st.error(
        "Associe os campos obrigatórios: "
        + ", ".join(nomes_ausentes)
        + "."
    )


if campos_recomendados_ausentes:
    nomes_recomendados = [
        ROTULOS_COLUNAS[campo]
        for campo in campos_recomendados_ausentes
    ]

    st.warning(
        "Campos recomendados não associados: "
        + ", ".join(nomes_recomendados)
        + ". Algumas regras não serão executadas."
    )


if existem_repeticoes:
    st.error(
        "A mesma coluna foi selecionada para mais de um campo. "
        "Cada coluna da planilha deve ser associada apenas uma vez."
    )


analisar = st.button(
    "Confirmar colunas e analisar",
    type="primary",
    disabled=(
        bool(campos_obrigatorios_ausentes)
        or existem_repeticoes
    ),
)


if analisar:
    try:
        dataframe_mapeado = aplicar_mapeamento_parcial(
            dataframe_bruto,
            mapeamento,
        )

        validar_colunas(
            dataframe_mapeado
        )

        dataframe_mapeado = (
            adicionar_colunas_recomendadas(
                dataframe_mapeado
            )
        )

        colunas_disponiveis = [
            coluna
            for coluna in COLUNAS_PADRAO
            if coluna in dataframe_mapeado.columns
        ]

        dataframe_mapeado = dataframe_mapeado[
            colunas_disponiveis
        ].copy()

        dataframe_limpo = limpar_dados(
            dataframe_mapeado
        )

        alertas = executar_validacoes(
            dataframe_limpo
        )

        regras_nao_executadas = (
            identificar_regras_nao_executadas(
                campos_recomendados_ausentes
            )
        )

        alertas = (
            remover_alertas_de_regras_indisponiveis(
                alertas,
                regras_nao_executadas,
            )
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

        st.session_state[
            "dataframe_limpo"
        ] = dataframe_limpo

        st.session_state["alertas"] = alertas

        st.session_state[
            "indicadores"
        ] = indicadores

        st.session_state["resumo"] = resumo

        st.session_state[
            "arquivo_excel"
        ] = arquivo_excel.getvalue()

        st.session_state[
            "nome_arquivo_analisado"
        ] = nome_arquivo

        st.session_state[
            "campos_nao_mapeados"
        ] = campos_recomendados_ausentes

        st.session_state[
            "regras_nao_executadas"
        ] = regras_nao_executadas

    except ErroCarregamento as erro:
        st.error(str(erro))
        st.stop()

    except (KeyError, TypeError, ValueError) as erro:
        st.error(
            "Não foi possível concluir a análise dos dados."
        )

        st.code(str(erro))

        st.stop()


if "indicadores" not in st.session_state:
    st.stop()


dataframe_limpo = st.session_state[
    "dataframe_limpo"
]

alertas = st.session_state["alertas"]

indicadores = st.session_state[
    "indicadores"
]

arquivo_excel = st.session_state[
    "arquivo_excel"
]

nome_arquivo_analisado = st.session_state[
    "nome_arquivo_analisado"
]

regras_nao_executadas = st.session_state.get(
    "regras_nao_executadas",
    [],
)


st.divider()

st.success(
    f"Arquivo analisado: {nome_arquivo_analisado}"
)


if regras_nao_executadas:
    with st.expander(
        "Regras não executadas",
        expanded=True,
    ):
        st.warning(
            "As regras abaixo não foram executadas porque "
            "as colunas necessárias não foram associadas."
        )

        for regra in regras_nao_executadas:
            st.write(f"- {regra}")


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
        "Nenhuma inconsistência foi encontrada "
        "pelas regras que puderam ser executadas."
    )

else:
    st.subheader("Filtros dos alertas")

    coluna_filtro_1, coluna_filtro_2 = st.columns(
        2
    )

    opcoes_severidade = sorted(
        alertas["severidade"]
        .dropna()
        .unique()
        .tolist()
    )

    severidades_selecionadas = (
        coluna_filtro_1.multiselect(
            "Severidade",
            options=opcoes_severidade,
            default=opcoes_severidade,
        )
    )

    opcoes_problemas = sorted(
        alertas["codigo_problema"]
        .dropna()
        .unique()
        .tolist()
    )

    problemas_selecionados = (
        coluna_filtro_2.multiselect(
            "Tipo de problema",
            options=opcoes_problemas,
            default=opcoes_problemas,
        )
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

    colunas_desejadas = [
        "celula",
        "id_linha",
        "id_servico",
        "codigo_problema",
        "severidade",
        "mensagem",
    ]

    colunas_exibidas = [
        coluna
        for coluna in colunas_desejadas
        if coluna in alertas_filtrados.columns
    ]

    st.dataframe(
        alertas_filtrados[colunas_exibidas],
        use_container_width=True,
        hide_index=True,
        column_config={
            "celula": st.column_config.TextColumn(
                "Célula do Excel",
                help=(
                    "Posição do dado na estrutura padronizada."
                ),
            ),
            "id_linha": st.column_config.NumberColumn(
                "Linha do Excel"
            ),
            "id_servico": st.column_config.TextColumn(
                "ID do serviço"
            ),
            "codigo_problema": (
                st.column_config.TextColumn(
                    "Problema"
                )
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

    st.subheader(
        "Quantidade de alertas por problema"
    )

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