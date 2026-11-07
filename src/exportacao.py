from io import BytesIO

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COR_CABECALHO = "1F4E78"
COR_TEXTO_CABECALHO = "FFFFFF"


def ajustar_largura_colunas(planilha):
    """Ajusta a largura das colunas de uma planilha."""

    for coluna in planilha.columns:
        maior_tamanho = 0

        letra_coluna = get_column_letter(
            coluna[0].column
        )

        for celula in coluna:
            if celula.value is None:
                continue

            tamanho = len(str(celula.value))

            maior_tamanho = max(maior_tamanho, tamanho)

        largura = min(
            maior_tamanho + 2,
            60,
        )

        planilha.column_dimensions[
            letra_coluna
        ].width = largura


def formatar_cabecalho(planilha):
    """Aplica formatação ao cabeçalho da planilha."""

    preenchimento = PatternFill(
        fill_type="solid",
        fgColor=COR_CABECALHO,
    )

    fonte = Font(
        color=COR_TEXTO_CABECALHO,
        bold=True,
    )

    for celula in planilha[1]:
        celula.fill = preenchimento
        celula.font = fonte
        celula.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    planilha.freeze_panes = "A2"
    planilha.auto_filter.ref = planilha.dimensions


def formatar_conteudo(planilha):
    """Configura alinhamento e quebra de texto."""

    for linha in planilha.iter_rows(
        min_row=2
    ):
        for celula in linha:
            celula.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )


def preparar_registros_para_exportacao(dataframe):
    """Prepara os registros para escrita no arquivo Excel."""

    registros = dataframe.copy()

    colunas_data = [
        "data_servico",
    ]

    for coluna in colunas_data:
        if coluna in registros.columns:
            registros[coluna] = registros[
                coluna
            ].dt.strftime("%d/%m/%Y")

    colunas_horario = [
        "hora_inicio",
        "hora_fim",
    ]

    for coluna in colunas_horario:
        if coluna in registros.columns:
            registros[coluna] = registros[
                coluna
            ].apply(
                lambda valor: (
                    valor.strftime("%H:%M")
                    if pd.notna(valor)
                    else ""
                )
            )

    return registros


def gerar_excel_resultado(
    dataframe,
    alertas,
    resumo,
):
    """Gera o relatório final em memória."""

    buffer = BytesIO()

    registros_exportacao = (
        preparar_registros_para_exportacao(
            dataframe
        )
    )

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl",
    ) as writer:
        registros_exportacao.to_excel(
            writer,
            sheet_name="Registros analisados",
            index=False,
        )

        alertas.to_excel(
            writer,
            sheet_name="Alertas",
            index=False,
        )

        resumo.to_excel(
            writer,
            sheet_name="Resumo",
            index=False,
        )

        for planilha in writer.book.worksheets:
            formatar_cabecalho(planilha)
            formatar_conteudo(planilha)
            ajustar_largura_colunas(planilha)

    buffer.seek(0)

    return buffer