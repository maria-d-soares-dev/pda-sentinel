import pandas as pd

CAMPOS_OBRIGATORIOS = [
    "id_servico",
    "data_servico",
    "equipe",
    "tipo_servico",
    "hora_inicio",
    "status",
]

COLUNAS_DUPLICIDADE = [
    "id_servico",
    "data_servico",
    "equipe",
]

LIMITE_DURACAO_HORAS = 6
LIMITE_DIFERENCA_KM = 5
LIMITE_DIFERENCA_PERCENTUAL = 0.10
LIMITE_DESLOCAMENTO_KM = 500

SEVERIDADES = {
    "CAMPO_AUSENTE": "Crítica",
    "POSSIVEL_DUPLICIDADE": "Crítica",
    "HORARIO_INVALIDO": "Crítica",
    "DURACAO_ATIPICA": "Atenção",
    "HODOMETRO_INVALIDO": "Crítica",
    "DIVERGENCIA_QUILOMETRAGEM": "Atenção",
    "CONCLUSAO_INCOMPLETA": "Crítica",
    "QUILOMETRAGEM_ATIPICA": "Atenção",
    "SOBREPOSICAO_DE_AGENDA": "Atenção",
    "EXCECAO_SEM_JUSTIFICATIVA": "Informativa",
}

COLUNAS_ALERTAS = [
    "id_linha",
    "id_servico",
    "codigo_problema",
    "severidade",
    "mensagem",
    "regra",
]


def criar_alerta(
    linha,
    codigo_problema,
    mensagem,
    regra,
):
    """Cria um alerta seguindo a estrutura padrão."""

    return {
        "id_linha": linha["id_linha"],
        "id_servico": linha["id_servico"],
        "codigo_problema": codigo_problema,
        "severidade": SEVERIDADES[codigo_problema],
        "mensagem": mensagem,
        "regra": regra,
    }


def campo_esta_ausente(valor):
    """Verifica se um valor está ausente ou contém somente espaços."""

    if pd.isna(valor):
        return True

    return isinstance(valor, str) and valor.strip() == ""


def converter_horario_em_minutos(horario):
    """Converte um horário em minutos desde a meia-noite."""

    return horario.hour * 60 + horario.minute


def validar_campos_obrigatorios(dataframe):
    """Sinaliza os campos obrigatórios ausentes."""

    alertas = []

    for _, linha in dataframe.iterrows():
        for campo in CAMPOS_OBRIGATORIOS:
            if campo_esta_ausente(linha[campo]):
                alerta = criar_alerta(
                    linha=linha,
                    codigo_problema="CAMPO_AUSENTE",
                    mensagem=(
                        f"O campo obrigatório '{campo}' "
                        "não foi informado."
                    ),
                    regra="Regra 1: campos obrigatórios vazios",
                )

                alertas.append(alerta)

    return alertas


def validar_duplicidades(dataframe):
    """Sinaliza possíveis duplicidades sem excluir registros."""

    alertas = []

    registros_completos = dataframe.dropna(
        subset=COLUNAS_DUPLICIDADE
    )

    mascara_duplicidade = registros_completos.duplicated(
        subset=COLUNAS_DUPLICIDADE,
        keep=False,
    )

    registros_duplicados = registros_completos.loc[
        mascara_duplicidade
    ]

    for _, linha in registros_duplicados.iterrows():
        alerta = criar_alerta(
            linha=linha,
            codigo_problema="POSSIVEL_DUPLICIDADE",
            mensagem=(
                "Existe outro registro com a mesma combinação "
                "de ID, data e equipe."
            ),
            regra=(
                "Regra 2: possível duplicidade por "
                "ID, data e equipe"
            ),
        )

        alertas.append(alerta)

    return alertas


def validar_horarios(dataframe):
    """Sinaliza horários finais anteriores aos iniciais."""

    alertas = []

    registros_com_horarios = dataframe.dropna(
        subset=[
            "hora_inicio",
            "hora_fim",
        ]
    )

    mascara_horario_invalido = (
        registros_com_horarios["hora_fim"]
        < registros_com_horarios["hora_inicio"]
    )

    registros_invalidos = registros_com_horarios.loc[
        mascara_horario_invalido
    ]

    for _, linha in registros_invalidos.iterrows():
        hora_inicio = linha["hora_inicio"]
        hora_fim = linha["hora_fim"]

        alerta = criar_alerta(
            linha=linha,
            codigo_problema="HORARIO_INVALIDO",
            mensagem=(
                f"O horário final ({hora_fim:%H:%M}) "
                "é anterior ao horário inicial "
                f"({hora_inicio:%H:%M})."
            ),
            regra=(
                "Regra 3: horário final anterior "
                "ao horário inicial"
            ),
        )

        alertas.append(alerta)

    return alertas


def validar_duracao(dataframe):
    """Sinaliza serviços com duração superior ao limite."""

    alertas = []

    registros_com_horarios = dataframe.dropna(
        subset=[
            "hora_inicio",
            "hora_fim",
        ]
    )

    limite_minutos = LIMITE_DURACAO_HORAS * 60

    for _, linha in registros_com_horarios.iterrows():
        inicio_minutos = converter_horario_em_minutos(
            linha["hora_inicio"]
        )

        fim_minutos = converter_horario_em_minutos(
            linha["hora_fim"]
        )

        duracao_minutos = fim_minutos - inicio_minutos

        if duracao_minutos > limite_minutos:
            duracao_horas = duracao_minutos / 60

            alerta = criar_alerta(
                linha=linha,
                codigo_problema="DURACAO_ATIPICA",
                mensagem=(
                    "O serviço apresentou duração de "
                    f"{duracao_horas:.1f} horas, superior ao "
                    "limite demonstrativo de "
                    f"{LIMITE_DURACAO_HORAS} horas."
                ),
                regra=(
                    "Regra 4: duração superior ao "
                    "limite demonstrativo"
                ),
            )

            alertas.append(alerta)

    return alertas


def validar_hodometro(dataframe):
    """Sinaliza hodômetros finais menores que os iniciais."""

    alertas = []

    registros_com_hodometro = dataframe.dropna(
        subset=[
            "km_inicial",
            "km_final",
        ]
    )

    mascara_hodometro_invalido = (
        registros_com_hodometro["km_final"]
        < registros_com_hodometro["km_inicial"]
    )

    registros_invalidos = registros_com_hodometro.loc[
        mascara_hodometro_invalido
    ]

    for _, linha in registros_invalidos.iterrows():
        km_inicial = linha["km_inicial"]
        km_final = linha["km_final"]

        alerta = criar_alerta(
            linha=linha,
            codigo_problema="HODOMETRO_INVALIDO",
            mensagem=(
                f"O hodômetro final ({km_final:.0f} km) "
                f"é menor que o inicial ({km_inicial:.0f} km)."
            ),
            regra=(
                "Regra 5: hodômetro final menor "
                "que o inicial"
            ),
        )

        alertas.append(alerta)

    return alertas


def validar_quilometragem(dataframe):
    """Sinaliza divergências entre km calculada e informada."""

    alertas = []

    registros_com_quilometragem = dataframe.dropna(
        subset=[
            "km_inicial",
            "km_final",
            "km_informada",
        ]
    )

    for _, linha in registros_com_quilometragem.iterrows():
        km_inicial = linha["km_inicial"]
        km_final = linha["km_final"]
        km_informada = linha["km_informada"]

        km_calculada = km_final - km_inicial

        if km_calculada <= 0:
            continue

        diferenca_km = abs(
            km_calculada - km_informada
        )

        diferenca_percentual = (
            diferenca_km / km_calculada
        )

        diferenca_superior = (
            diferenca_km > LIMITE_DIFERENCA_KM
        )

        percentual_superior = (
            diferenca_percentual
            > LIMITE_DIFERENCA_PERCENTUAL
        )

        if diferenca_superior and percentual_superior:
            percentual_formatado = (
                diferenca_percentual * 100
            )

            alerta = criar_alerta(
                linha=linha,
                codigo_problema=(
                    "DIVERGENCIA_QUILOMETRAGEM"
                ),
                mensagem=(
                    f"A quilometragem calculada foi de "
                    f"{km_calculada:.0f} km, mas foram "
                    f"informados {km_informada:.0f} km. "
                    f"Diferença de {diferenca_km:.0f} km "
                    f"({percentual_formatado:.1f}%)."
                ),
                regra=(
                    "Regra 6: divergência entre "
                    "quilometragem calculada e informada"
                ),
            )

            alertas.append(alerta)

    return alertas


def validar_conclusao(dataframe):
    """Sinaliza serviços concluídos sem horário final."""

    alertas = []

    status_padronizado = (
        dataframe["status"]
        .astype("string")
        .str.strip()
        .str.casefold()
    )

    status_concluido = status_padronizado.eq(
        "concluído".casefold()
    ).fillna(False)

    horario_final_ausente = dataframe["hora_fim"].isna()

    mascara_conclusao_incompleta = (
        status_concluido
        & horario_final_ausente
    )

    registros_incompletos = dataframe.loc[
        mascara_conclusao_incompleta
    ]

    for _, linha in registros_incompletos.iterrows():
        alerta = criar_alerta(
            linha=linha,
            codigo_problema="CONCLUSAO_INCOMPLETA",
            mensagem=(
                "O serviço está marcado como concluído, "
                "mas o horário final não foi informado."
            ),
            regra=(
                "Regra 7: serviço concluído "
                "sem horário final"
            ),
        )

        alertas.append(alerta)

    return alertas


def validar_quilometragem_atipica(dataframe):
    """Sinaliza valores negativos, inválidos ou acima do limite."""

    alertas = []

    for _, linha in dataframe.iterrows():
        km_inicial = linha["km_inicial"]
        km_final = linha["km_final"]
        km_informada = linha["km_informada"]

        problema = None

        if (
            pd.isna(km_inicial)
            or pd.isna(km_final)
            or pd.isna(km_informada)
        ):
            problema = (
                "Existe um valor de quilometragem "
                "ausente ou não numérico."
            )

        elif (
            km_inicial < 0
            or km_final < 0
            or km_informada < 0
        ):
            problema = (
                "Existe um valor negativo nas colunas "
                "de quilometragem."
            )

        else:
            deslocamento = km_final - km_inicial

            if deslocamento > LIMITE_DESLOCAMENTO_KM:
                problema = (
                    f"O deslocamento calculado foi de "
                    f"{deslocamento:.0f} km, superior ao "
                    f"limite demonstrativo de "
                    f"{LIMITE_DESLOCAMENTO_KM} km."
                )

            elif km_informada > LIMITE_DESLOCAMENTO_KM:
                problema = (
                    f"A quilometragem informada foi de "
                    f"{km_informada:.0f} km, superior ao "
                    f"limite demonstrativo de "
                    f"{LIMITE_DESLOCAMENTO_KM} km."
                )

        if problema is not None:
            alerta = criar_alerta(
                linha=linha,
                codigo_problema="QUILOMETRAGEM_ATIPICA",
                mensagem=problema,
                regra=(
                    "Regra 8: quilometragem negativa, "
                    "inválida ou acima do limite"
                ),
            )

            alertas.append(alerta)

    return alertas


def validar_sobreposicoes(dataframe):
    """Sinaliza serviços sobrepostos da mesma equipe e data."""

    alertas = []

    registros_completos = dataframe.dropna(
        subset=[
            "equipe",
            "data_servico",
            "hora_inicio",
            "hora_fim",
        ]
    )

    grupos = registros_completos.groupby(
        [
            "equipe",
            "data_servico",
        ]
    )

    for _, grupo in grupos:
        registros = list(grupo.iterrows())

        for posicao_a in range(len(registros)):
            _, linha_a = registros[posicao_a]

            inicio_a = linha_a["hora_inicio"]
            fim_a = linha_a["hora_fim"]

            if fim_a <= inicio_a:
                continue

            for posicao_b in range(
                posicao_a + 1,
                len(registros),
            ):
                _, linha_b = registros[posicao_b]

                if (
                    linha_a["id_servico"]
                    == linha_b["id_servico"]
                ):
                    continue

                inicio_b = linha_b["hora_inicio"]
                fim_b = linha_b["hora_fim"]

                if fim_b <= inicio_b:
                    continue

                existe_sobreposicao = (
                    inicio_a < fim_b
                    and inicio_b < fim_a
                )

                if not existe_sobreposicao:
                    continue

                alerta_a = criar_alerta(
                    linha=linha_a,
                    codigo_problema=(
                        "SOBREPOSICAO_DE_AGENDA"
                    ),
                    mensagem=(
                        "O horário deste serviço se sobrepõe "
                        f"ao serviço {linha_b['id_servico']}."
                    ),
                    regra=(
                        "Regra 9: serviços sobrepostos "
                        "da mesma equipe"
                    ),
                )

                alerta_b = criar_alerta(
                    linha=linha_b,
                    codigo_problema=(
                        "SOBREPOSICAO_DE_AGENDA"
                    ),
                    mensagem=(
                        "O horário deste serviço se sobrepõe "
                        f"ao serviço {linha_a['id_servico']}."
                    ),
                    regra=(
                        "Regra 9: serviços sobrepostos "
                        "da mesma equipe"
                    ),
                )

                alertas.append(alerta_a)
                alertas.append(alerta_b)

    return alertas


def validar_justificativas(
    dataframe,
    alertas_existentes,
):
    """Sinaliza exceções sem justificativa na observação."""

    alertas = []

    codigos_de_excecao = {
        "DURACAO_ATIPICA",
        "DIVERGENCIA_QUILOMETRAGEM",
        "QUILOMETRAGEM_ATIPICA",
    }

    linhas_com_excecao = {
        alerta["id_linha"]
        for alerta in alertas_existentes
        if alerta["codigo_problema"] in codigos_de_excecao
    }

    registros_com_excecao = dataframe[
        dataframe["id_linha"].isin(linhas_com_excecao)
    ]

    for _, linha in registros_com_excecao.iterrows():
        if campo_esta_ausente(linha["observacao"]):
            alerta = criar_alerta(
                linha=linha,
                codigo_problema=(
                    "EXCECAO_SEM_JUSTIFICATIVA"
                ),
                mensagem=(
                    "O registro possui uma exceção de duração "
                    "ou quilometragem, mas não contém observação."
                ),
                regra=(
                    "Regra 10: exceção sem justificativa "
                    "na observação"
                ),
            )

            alertas.append(alerta)

    return alertas


def executar_validacoes(dataframe):
    """Executa todas as regras e retorna a tabela de alertas."""

    alertas = []

    alertas.extend(
        validar_campos_obrigatorios(dataframe)
    )

    alertas.extend(
        validar_duplicidades(dataframe)
    )

    alertas.extend(
        validar_horarios(dataframe)
    )

    alertas.extend(
        validar_duracao(dataframe)
    )

    alertas.extend(
        validar_hodometro(dataframe)
    )

    alertas.extend(
        validar_quilometragem(dataframe)
    )

    alertas.extend(
        validar_conclusao(dataframe)
    )

    alertas.extend(
        validar_quilometragem_atipica(dataframe)
    )

    alertas.extend(
        validar_sobreposicoes(dataframe)
    )

    alertas.extend(
        validar_justificativas(
            dataframe,
            alertas,
        )
    )

    return pd.DataFrame(
        alertas,
        columns=COLUNAS_ALERTAS,
    )