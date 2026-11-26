"""Respostas certas das 5 tarefas do teste automatizado (testar_usabilidade.py), calculadas só do web/dados.json (mesmas fórmulas da tela Como calcular)."""


def respostas_certas(dados):
    P = [f["properties"] for f in dados["features"]]
    anos, faixas = dados["anos"], dados["faixas"]
    por_nome = {p["nome"]: p for p in P}
    pop_est = sum(p["pop"] for p in P)
    cas_est = sum(sum(p["casos"]["total"]) for p in P)
    taxa = lambda p: sum(p["casos"]["total"]) / p["pop"] * 1e5 / len(anos)
    oe = lambda p: sum(p["casos"]["total"]) / (p["pop"] * cas_est / pop_est)
    taxa_est = cas_est / pop_est * 1e5 / len(anos)
    # T1: 3 menores O/E (todos os tipos, 2019–2024) entre municípios com pelo menos 10 casos
    t1 = sorted((p for p in P if sum(p["casos"]["total"]) >= 10), key=oe)[:3]
    # T2: Sousa acima ou abaixo da média do estado
    s = por_nome["Sousa"]
    # T3: faixa etária com mais casos em Campina Grande (sem a faixa "Ignorada"; empates juntos)
    cg = por_nome["Campina Grande"]["faixa"][:10]
    t3 = [faixas[i] for i, v in enumerate(cg) if v == max(cg)]
    # T4: violência sexual no estado, 2019 e 2024
    sx = [sum(p["casos"]["sexual"][i] for p in P) for i in range(len(anos))]
    return {
        "T1": {"municipios": [{"nome": p["nome"], "cod": p["cod"], "casos": sum(p["casos"]["total"]), "oe": round(oe(p), 2)} for p in t1]},
        "T2": {"taxa_sousa": round(taxa(s), 1), "taxa_estado": round(taxa_est, 1), "oe": round(oe(s), 2),
               "resposta": "abaixo" if taxa(s) < taxa_est else "acima"},
        "T3": {"faixas": t3, "casos": max(cg), "total_cg": sum(por_nome["Campina Grande"]["faixa"]),
               "pct": round(100 * max(cg) / sum(por_nome["Campina Grande"]["faixa"]))},
        "T4": {"sexual_2019": sx[0], "sexual_2024": sx[-1], "variacao_pct": round(100 * (sx[-1] / sx[0] - 1)),
               "resposta": "cresceu" if sx[-1] > sx[0] else "não cresceu"},
        "T5": {"linhas_csv": len(P), "cabecalho": "cod_ibge7;municipio;mulheres_censo2022;casos_2019_2024;taxa_100mil_mulheres_ano;casos_esperados;observado_sobre_esperado"},
    }
