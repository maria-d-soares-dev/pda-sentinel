import re
import unicodedata

COLUNAS_PADRAO = [
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
]

ROTULOS_COLUNAS = {
    "id_servico": "ID do serviço",
    "data_servico": "Data do serviço",
    "equipe": "Equipe",
    "tipo_servico": "Tipo de serviço",
    "hora_inicio": "Horário inicial",
    "hora_fim": "Horário final",
    "km_inicial": "Quilometragem inicial",
    "km_final": "Quilometragem final",
    "km_informada": "Quilometragem informada",
    "status": "Status",
    "localidade": "Localidade",
    "observacao": "Observação",
}

ALIASES_COLUNAS = {
    "id_servico": {
        "id_servico",
        "id",
        "codigo",
        "codigo_servico",
        "codigo_os",
        "numero_os",
        "ordem_servico",
        "os",
    },
    "data_servico": {
        "data_servico",
        "data",
        "data_execucao",
        "data_atendimento",
        "dia",
    },
    "equipe": {
        "equipe",
        "equipe_responsavel",
        "turma",
        "time",
        "grupo",
    },
    "tipo_servico": {
        "tipo_servico",
        "servico",
        "categoria",
        "atividade",
        "tipo",
    },
    "hora_inicio": {
        "hora_inicio",
        "horario_inicio",
        "inicio",
        "hora_inicial",
        "entrada",
    },
    "hora_fim": {
        "hora_fim",
        "horario_fim",
        "fim",
        "hora_final",
        "termino",
        "saida",
    },
    "km_inicial": {
        "km_inicial",
        "quilometragem_inicial",
        "hodometro_inicial",
        "odometro_inicial",
        "km_saida",
    },
    "km_final": {
        "km_final",
        "quilometragem_final",
        "hodometro_final",
        "odometro_final",
        "km_chegada",
    },
    "km_informada": {
        "km_informada",
        "quilometragem_informada",
        "km_lancada",
        "km_registrada",
        "distancia",
    },
    "status": {
        "status",
        "situacao",
        "estado",
        "resultado",
    },
    "localidade": {
        "localidade",
        "regiao",
        "setor",
        "area",
        "local",
    },
    "observacao": {
        "observacao",
        "observacoes",
        "comentario",
        "comentarios",
        "justificativa",
        "descricao",
    },
}


def normalizar_nome_coluna(nome):
    """Remove acentos e padroniza o nome de uma coluna."""

    texto = str(nome).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(
        r"[^a-z0-9]+",
        "_",
        texto,
    )

    return texto.strip("_")


def sugerir_mapeamento(colunas_recebidas):
    """Sugere correspondências com base nos aliases conhecidos."""

    sugestoes = {}

    for coluna_original in colunas_recebidas:
        coluna_normalizada = normalizar_nome_coluna(
            coluna_original
        )

        for coluna_padrao, aliases in ALIASES_COLUNAS.items():
            if coluna_normalizada in aliases:
                sugestoes[coluna_padrao] = coluna_original
                break

    return sugestoes


def aplicar_mapeamento(dataframe, mapeamento):
    """Renomeia as colunas selecionadas para o padrão interno."""

    nomes_invertidos = {
        coluna_original: coluna_padrao
        for coluna_padrao, coluna_original
        in mapeamento.items()
        if coluna_original is not None
    }

    return dataframe.rename(
        columns=nomes_invertidos
    )