import random
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd


# Garante que os mesmos dados sejam gerados em todas as execuções.
random.seed(42)


QUANTIDADE_REGISTROS = 400

COLUNAS = [
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

TIPOS_SERVICO = [
    "Manutenção",
    "Inspeção",
    "Instalação",
    "Reparo",
    "Vistoria",
]

STATUS_POSSIVEIS = [
    "Concluído",
    "Pendente",
    "Cancelado",
]

LOCALIDADES = [
    "Setor Norte",
    "Setor Sul",
    "Setor Leste",
    "Setor Oeste",
    "Setor Central",
]

OBSERVACOES = [
    "Serviço executado normalmente",
    "Equipamento inspecionado",
    "Material substituído",
    "Atendimento finalizado",
    "Verificação concluída",
    "Acesso liberado no local",
    "Nenhuma irregularidade identificada",
]

EQUIPES = [
    f"EQ-{numero:03d}"
    for numero in range(1, 21)
]


def gerar_horario_inicio():
    """Gera um horário entre 07:00 e 15:30."""

    hora = random.randint(7, 15)
    minuto = random.choice([0, 15, 30])

    return time(hour=hora, minute=minuto)


def adicionar_minutos(horario, quantidade_minutos):
    """Soma minutos a um horário sem usar uma data real."""

    horario_completo = datetime.combine(
        date.today(),
        horario,
    )

    novo_horario = horario_completo + timedelta(
        minutes=quantidade_minutos
    )

    return novo_horario.time()


def gerar_registro(numero):
    """Cria um registro sintético inicialmente válido."""

    data_inicial = date(2026, 1, 1)

    dias_adicionados = random.randint(0, 300)

    data_servico = data_inicial + timedelta(
        days=dias_adicionados
    )

    hora_inicio = gerar_horario_inicio()

    duracao_minutos = random.randint(30, 240)

    hora_fim = adicionar_minutos(
        hora_inicio,
        duracao_minutos,
    )

    km_inicial = random.randint(10_000, 90_000)

    deslocamento = random.randint(5, 150)

    km_final = km_inicial + deslocamento

    # Pequena diferença normal de até 2 km.
    variacao_informada = random.randint(-2, 2)

    km_informada = max(
        0,
        deslocamento + variacao_informada,
    )

    status = random.choices(
        population=STATUS_POSSIVEIS,
        weights=[75, 15, 10],
        k=1,
    )[0]

    # Um serviço não concluído também pode ter horário final no
    # conjunto demonstrativo. Isso não representa uma regra real.
    observacao = random.choice(OBSERVACOES)

    return {
        "id_servico": f"SRV-{numero:04d}",
        "data_servico": data_servico,
        "equipe": random.choice(EQUIPES),
        "tipo_servico": random.choice(TIPOS_SERVICO),
        "hora_inicio": hora_inicio,
        "hora_fim": hora_fim,
        "km_inicial": km_inicial,
        "km_final": km_final,
        "km_informada": km_informada,
        "status": status,
        "localidade": random.choice(LOCALIDADES),
        "observacao": observacao,
    }


def inserir_campos_ausentes(df):
    """Insere dez registros com campos obrigatórios ausentes."""

    colunas_afetadas = [
        "id_servico",
        "data_servico",
        "equipe",
        "tipo_servico",
        "hora_inicio",
        "status",
        "equipe",
        "hora_inicio",
        "tipo_servico",
        "data_servico",
    ]

    for indice, coluna in enumerate(colunas_afetadas):
        df.loc[indice, coluna] = None


def inserir_duplicidades(df):
    """Cria oito registros com a mesma combinação de ID, data e equipe."""

    for indice in range(10, 18):
        linha_original = indice - 1

        df.loc[indice, "id_servico"] = df.loc[
            linha_original,
            "id_servico",
        ]

        df.loc[indice, "data_servico"] = df.loc[
            linha_original,
            "data_servico",
        ]

        df.loc[indice, "equipe"] = df.loc[
            linha_original,
            "equipe",
        ]


def inserir_horarios_invalidos(df):
    """Cria oito horários finais anteriores aos iniciais."""

    for indice in range(18, 26):
        df.loc[indice, "hora_inicio"] = time(14, 30)
        df.loc[indice, "hora_fim"] = time(12, 20)


def inserir_duracoes_atipicas(df):
    """Cria dez serviços com duração superior a seis horas."""

    for indice in range(26, 36):
        df.loc[indice, "hora_inicio"] = time(7, 30)
        df.loc[indice, "hora_fim"] = time(15, 0)
        df.loc[indice, "observacao"] = (
            "Duração ampliada registrada para demonstração"
        )


def inserir_hodometros_invalidos(df):
    """Cria oito registros com hodômetro final menor."""

    for indice in range(36, 44):
        km_inicial = random.randint(20_000, 80_000)

        df.loc[indice, "km_inicial"] = km_inicial
        df.loc[indice, "km_final"] = km_inicial - 70
        df.loc[indice, "km_informada"] = 70


def inserir_divergencias_quilometragem(df):
    """Cria doze divergências entre km calculada e informada."""

    for indice in range(44, 56):
        km_inicial = random.randint(20_000, 80_000)

        df.loc[indice, "km_inicial"] = km_inicial
        df.loc[indice, "km_final"] = km_inicial + 86
        df.loc[indice, "km_informada"] = 60
        df.loc[indice, "observacao"] = (
            "Registro com divergência sintética"
        )


def inserir_conclusoes_incompletas(df):
    """Cria oito registros concluídos sem horário final."""

    for indice in range(56, 64):
        df.loc[indice, "status"] = "Concluído"
        df.loc[indice, "hora_fim"] = None


def inserir_quilometragens_atipicas(df):
    """Cria oito deslocamentos superiores a 500 km."""

    for indice in range(64, 72):
        km_inicial = random.randint(20_000, 80_000)

        df.loc[indice, "km_inicial"] = km_inicial
        df.loc[indice, "km_final"] = km_inicial + 650
        df.loc[indice, "km_informada"] = 650
        df.loc[indice, "observacao"] = None


def inserir_sobreposicoes(df):
    """Cria quatro pares, totalizando oito serviços sobrepostos."""

    pares = [
        (72, 73),
        (74, 75),
        (76, 77),
        (78, 79),
    ]

    for numero_par, (indice_a, indice_b) in enumerate(
        pares,
        start=1,
    ):
        equipe = f"EQ-{numero_par:03d}"
        data_compartilhada = date(2026, 11, numero_par)

        df.loc[indice_a, "equipe"] = equipe
        df.loc[indice_b, "equipe"] = equipe

        df.loc[indice_a, "data_servico"] = data_compartilhada
        df.loc[indice_b, "data_servico"] = data_compartilhada

        df.loc[indice_a, "hora_inicio"] = time(9, 0)
        df.loc[indice_a, "hora_fim"] = time(11, 0)

        df.loc[indice_b, "hora_inicio"] = time(10, 30)
        df.loc[indice_b, "hora_fim"] = time(12, 20)


def validar_estrutura(df):
    """Interrompe a geração se a estrutura não for a esperada."""

    if len(df) != QUANTIDADE_REGISTROS:
        raise ValueError(
            "A planilha precisa conter exatamente "
            f"{QUANTIDADE_REGISTROS} registros."
        )

    if list(df.columns) != COLUNAS:
        raise ValueError(
            "As colunas geradas não correspondem à estrutura esperada."
        )


def salvar_planilha(df):
    """Salva os registros dentro da pasta data."""

    pasta_data = Path("data")
    pasta_data.mkdir(exist_ok=True)

    caminho_arquivo = pasta_data / "exemplo_operacional.xlsx"

    df.to_excel(
        caminho_arquivo,
        index=False,
        engine="openpyxl",
    )

    return caminho_arquivo


def main():
    registros = [
        gerar_registro(numero)
        for numero in range(1, QUANTIDADE_REGISTROS + 1)
    ]

    df = pd.DataFrame(
        registros,
        columns=COLUNAS,
    )

    inserir_campos_ausentes(df)
    inserir_duplicidades(df)
    inserir_horarios_invalidos(df)
    inserir_duracoes_atipicas(df)
    inserir_hodometros_invalidos(df)
    inserir_divergencias_quilometragem(df)
    inserir_conclusoes_incompletas(df)
    inserir_quilometragens_atipicas(df)
    inserir_sobreposicoes(df)

    validar_estrutura(df)

    caminho_arquivo = salvar_planilha(df)

    print(
        f"Planilha criada com {len(df)} registros."
    )

    print(
        f"Arquivo: {caminho_arquivo.as_posix()}"
    )


if __name__ == "__main__":
    main()